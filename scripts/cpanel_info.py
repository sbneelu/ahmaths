#!/usr/bin/env python3
"""
cpanel_info.py — read-only Playwright recon of a Namecheap-hosted cPanel
account, dumping deployment-relevant info as YAML. Reads pages only; never
modifies cPanel. Redacts env-var values whose name matches the redact list and
masks password inputs before screenshotting. Exit codes: 0 OK, 1 config/login
failure, 2 partial extraction (YAML still written; failed sections on stderr).
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import yaml
from playwright.sync_api import (
    Frame,
    Page,
    TimeoutError as PWTimeout,
    sync_playwright,
)

DEFAULT_TIMEOUT_MS = 15_000
DEFAULT_NAV_TIMEOUT_MS = 30_000
REDACT_TOKENS = ("PASSWORD", "SECRET", "KEY", "TOKEN")
REDACTED = "<redacted>"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("cpanel_info")


# ----- Config ------------------------------------------------------------

@dataclass
class Config:
    url: str
    username: str
    password: str
    totp_secret: str | None
    output_path: Path
    screenshot_dir: Path
    headless: bool
    slow_mo_ms: int


def load_config() -> Config:
    missing: list[str] = []
    url = os.environ.get("CPANEL_URL", "").rstrip("/")
    if not url:
        missing.append("CPANEL_URL")
    username = os.environ.get("CPANEL_USERNAME", "")
    if not username:
        missing.append("CPANEL_USERNAME")
    password = os.environ.get("CPANEL_PASSWORD", "")
    if not password:
        missing.append("CPANEL_PASSWORD")
    if missing:
        log.error("Missing required env vars: %s", ", ".join(missing))
        raise SystemExit(1)
    try:
        slow_mo_ms = int(os.environ.get("SLOW_MO_MS", "0"))
    except ValueError:
        slow_mo_ms = 0
    return Config(
        url=url,
        username=username,
        password=password,
        totp_secret=os.environ.get("CPANEL_TOTP_SECRET") or None,
        output_path=Path(os.environ.get("OUTPUT_PATH", "/tmp/cpanel_info.yaml")),
        screenshot_dir=Path(os.environ.get("SCREENSHOT_DIR", "/tmp/cpanel-screenshots")),
        headless=os.environ.get("HEADLESS", "true").strip().lower() != "false",
        slow_mo_ms=slow_mo_ms,
    )


# ----- Helpers -----------------------------------------------------------

def needs_redact(name: str) -> bool:
    upper = name.upper()
    return any(tok in upper for tok in REDACT_TOKENS)


def mask_password_inputs(page: Page) -> None:
    try:
        page.evaluate(
            "() => document.querySelectorAll('input[type=\"password\"]')"
            ".forEach(el => { if (el.value) el.value = '<redacted>'; })"
        )
    except Exception:
        pass


@dataclass
class Screenshotter:
    out_dir: Path
    index: int = 0
    entries: list[dict[str, str]] = field(default_factory=list)

    def take(self, page: Page, label: str) -> None:
        self.index += 1
        slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        target = self.out_dir / f"{self.index:02d}-{slug}.png"
        try:
            mask_password_inputs(page)
            page.screenshot(path=str(target), full_page=True)
            self.entries.append({"path": str(target), "page": label})
            log.info("screenshot: %s", label)
        except Exception as e:
            log.warning("screenshot failed for %s: %s", label, type(e).__name__)


def wait_dom(page: Page, timeout: int = DEFAULT_TIMEOUT_MS) -> None:
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
    except PWTimeout:
        pass


def deep_link(base: str, cpsess: str, path: str) -> str:
    return f"{base}/{cpsess}/frontend/jupiter/{path.lstrip('/')}"


# ----- Login -------------------------------------------------------------

def do_login(page: Page, cfg: Config) -> str:
    log.info("navigating to cPanel login")
    page.goto(cfg.url, wait_until="domcontentloaded")
    wait_dom(page)
    log.info("submitting username/password")
    page.locator('input[name="user"]').first.fill(cfg.username)
    page.locator('input[name="pass"]').first.fill(cfg.password)
    page.locator(
        '#login_submit, input[type="submit"][value*="og" i], button[type="submit"]'
    ).first.click()

    try:
        page.wait_for_url(re.compile(r"/cpsess\d+/"), timeout=DEFAULT_NAV_TIMEOUT_MS)
    except PWTimeout:
        pass

    tfa = page.locator(
        'input[name="tfa_token"], input[placeholder*="Security Code" i]'
    ).first
    if tfa.count() > 0 and tfa.is_visible():
        if not cfg.totp_secret:
            log.error("2FA is enabled but CPANEL_TOTP_SECRET is not set")
            raise SystemExit(1)
        import pyotp
        log.info("2FA prompt detected, generating TOTP")
        tfa.fill(pyotp.TOTP(cfg.totp_secret).now())
        page.locator(
            'button[type="submit"], input[type="submit"], button:has-text("Continue")'
        ).first.click()
        try:
            page.wait_for_url(re.compile(r"/cpsess\d+/"), timeout=DEFAULT_NAV_TIMEOUT_MS)
        except PWTimeout:
            log.error("did not reach a /cpsess.../ URL after 2FA")
            raise SystemExit(1)

    m = re.search(r"/cpsess(\d+)/", page.url)
    if not m:
        log.error("login did not reach a cpsess URL")
        raise SystemExit(1)
    log.info("logged in (cpsess token captured)")
    return f"cpsess{m.group(1)}"


# ----- Extractors --------------------------------------------------------
# Each takes (page, cfg, cpsess, shot) and returns the dict for the YAML.
# JS evaluators are kept inline because the work is DOM parsing.


_JS_LABELLED_VALUE = """(rx) => {
    const re = new RegExp(rx, 'i');
    for (const el of document.querySelectorAll('*')) {
        if (el.children.length) continue;
        if (!re.test((el.textContent || '').trim())) continue;
        let n = el;
        for (let i = 0; i < 4 && n; i++) {
            n = n.parentElement; if (!n) break;
            const txt = (n.textContent || '').trim();
            const after = txt.replace(re, '').trim();
            if (after && after !== txt) return after;
        }
    }
    return null;
}"""


def _clean(v: str | None) -> str | None:
    if not v:
        return v
    v = re.sub(r"\s+", " ", v.strip())
    if "\n" in v:
        v = v.split("\n", 1)[0].strip()
    return v or None


def extract_general(page: Page, cfg: Config, cpsess: str, shot: Screenshotter) -> dict:
    page.goto(deep_link(cfg.url, cpsess, ""), wait_until="domcontentloaded")
    wait_dom(page)
    shot.take(page, "home")

    def val(label_regex: str) -> str | None:
        try:
            return page.evaluate(_JS_LABELLED_VALUE, label_regex)
        except Exception:
            return None

    username = val(r"^\s*(Current User|Username)\s*:?\s*$") or cfg.username
    primary_domain = val(r"^\s*(Primary Domain|Main Domain)\s*:?\s*$")
    home_dir = val(r"^\s*Home Directory\s*:?\s*$")

    cpanel_version = None
    for sel in ("footer", "#footer", ".footer", "body"):
        try:
            txt = page.locator(sel).first.inner_text(timeout=2_000)
        except Exception:
            continue
        m = re.search(r"cPanel.*?Version[:\s]+([0-9][0-9.\-]+)", txt, re.I)
        if m:
            cpanel_version = m.group(1)
            break

    return {
        "username": _clean(username),
        "server_hostname": urlparse(cfg.url).hostname,
        "primary_domain": _clean(primary_domain),
        "home_dir": _clean(home_dir),
        "cpanel_version": _clean(cpanel_version),
    }


def extract_domains(page: Page, cfg: Config, cpsess: str, shot: Screenshotter) -> list[dict]:
    page.goto(deep_link(cfg.url, cpsess, "domains/index.html"), wait_until="domcontentloaded")
    wait_dom(page)
    shot.take(page, "domains")

    rows = page.evaluate("""() => {
        const out = [];
        for (const t of document.querySelectorAll('table')) {
            for (const tr of t.querySelectorAll('tr')) {
                const cells = Array.from(tr.querySelectorAll('td')).map(c => (c.innerText || '').trim());
                if (cells.length >= 2) out.push(cells);
            }
        }
        return out;
    }""")

    type_map = {"main": "Primary", "parked": "Alias"}
    domains: list[dict] = []
    seen: set[str] = set()
    for cells in rows:
        name = next((c for c in cells if re.match(r"^[\w.\-]+\.[a-z]{2,}$", c, re.I)), None)
        if not name or name in seen:
            continue
        doc_root = next((c for c in cells if c.startswith("/") and "/" in c[1:]), None)
        dtype = next(
            (c for c in cells if c.lower() in {"main", "primary", "addon", "subdomain", "alias", "parked"}),
            None,
        )
        if dtype:
            dtype = type_map.get(dtype.lower(), dtype.capitalize())
        seen.add(name)
        domains.append({"name": name, "document_root": doc_root, "type": dtype})
    return domains


def _python_frame(page: Page) -> Frame:
    """The Python App page is iframe'd inside Jupiter. Return its frame."""
    for _ in range(15):
        for f in page.frames:
            url = f.url or ""
            if "python" in url.lower() or "passenger" in url.lower():
                return f
        page.wait_for_timeout(500)
    return page.main_frame


def extract_python_app(page: Page, cfg: Config, cpsess: str, shot: Screenshotter) -> dict:
    page.goto(
        deep_link(cfg.url, cpsess, "setup-python-app/index.html"),
        wait_until="domcontentloaded",
    )
    wait_dom(page, timeout=DEFAULT_NAV_TIMEOUT_MS)
    page.wait_for_timeout(1_500)
    shot.take(page, "python-apps-list")

    frame = _python_frame(page)
    try:
        frame.wait_for_load_state("domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    except PWTimeout:
        pass

    try:
        rows_text = frame.locator("body").inner_text(timeout=3_000)
    except Exception:
        rows_text = ""

    if "ahmaths.com" not in rows_text:
        existing = sorted({
            e for e in re.findall(r"[\w.\-]+\.[a-z]{2,}", rows_text)
            if "." in e and not e.endswith(".py")
        })
        return {"found": False, "other_apps_seen": existing}

    # Click an edit affordance on the ahmaths.com row.
    try:
        row = frame.locator("tr", has_text="ahmaths.com").first
        if row.count() > 0:
            for sel in (
                'a:has-text("Edit")',
                'button:has-text("Edit")',
                'a[title*="Edit" i]',
                'button[title*="Edit" i]',
                "a.edit, button.edit",
                "a",
            ):
                btn = row.locator(sel).first
                if btn.count() > 0:
                    btn.click()
                    break
    except Exception as e:
        log.warning("could not click edit on ahmaths.com row: %s", type(e).__name__)

    page.wait_for_timeout(2_000)
    frame = _python_frame(page)
    try:
        frame.wait_for_load_state("domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
    except PWTimeout:
        pass
    shot.take(page, "python-app-detail")

    def read_field(pat: str) -> str | None:
        try:
            v = frame.evaluate(
                """(pat) => {
                    const re = new RegExp(pat, 'i');
                    for (const l of document.querySelectorAll(
                        'label, .form-label, dt, th, td, span, div'
                    )) {
                        if (!re.test((l.textContent || '').trim())) continue;
                        let n = l;
                        for (let i = 0; i < 5 && n; i++) {
                            const c = n.querySelector(
                                'input, select, textarea, .form-control-static, .readonly-value'
                            );
                            if (c) {
                                if ('value' in c && c.value) return c.value;
                                const tx = (c.textContent || '').trim();
                                if (tx) return tx;
                            }
                            n = n.parentElement;
                        }
                    }
                    return null;
                }""",
                pat,
            )
            return str(v).strip() if v else None
        except Exception:
            return None

    python_version = read_field(r"Python\s*version")
    app_root = read_field(r"Application\s*root|App\s*root")
    app_url = read_field(r"Application\s*URL|App\s*URL")
    startup_file = read_field(r"Application\s*startup\s*file|Startup\s*file")
    entry_point = read_field(r"Application\s*Entry\s*point|Entry\s*point")
    passenger_log = read_field(r"Passenger\s*log|Log\s*file")

    venv_path = None
    try:
        body_txt = frame.locator("body").inner_text(timeout=2_000)
        m = re.search(r"source\s+(\S+/bin/activate)", body_txt)
        if m:
            venv_path = m.group(1).replace("/bin/activate", "")
        if not venv_path:
            m = re.search(r"(/home/\S+/virtualenv/\S+)", body_txt)
            if m:
                venv_path = m.group(1)
    except Exception:
        pass

    # Environment variables — name/value input pairs under an "Environment
    # variables" heading (fallback: any UPPER_SNAKE name in scope).
    env_vars: dict[str, str] = {}
    try:
        pairs = frame.evaluate("""() => {
            const result = [];
            let section = null;
            for (const h of document.querySelectorAll(
                'h1,h2,h3,h4,h5,legend,div,span,label'
            )) {
                if (/environment\\s+variable/i.test(h.textContent || '')) {
                    section = h; break;
                }
            }
            const scope = section
                ? (section.closest('section, fieldset, .panel, .card, form, div') || document)
                : document;
            scope.querySelectorAll('tr, .row, li, .env-row').forEach(r => {
                const inputs = r.querySelectorAll('input[type="text"], input:not([type])');
                if (inputs.length >= 2) {
                    const n = (inputs[0].value || '').trim();
                    const v = (inputs[1].value || '').trim();
                    if (n) result.push([n, v]);
                }
            });
            if (result.length === 0) {
                const inputs = Array.from(scope.querySelectorAll(
                    'input[type="text"], input:not([type])'
                ));
                for (let i = 0; i + 1 < inputs.length; i += 2) {
                    const n = (inputs[i].value || '').trim();
                    const v = (inputs[i+1].value || '').trim();
                    if (n && /^[A-Z_][A-Z0-9_]*$/.test(n)) result.push([n, v]);
                }
            }
            return result;
        }""")
        for name, value in pairs:
            env_vars[name] = REDACTED if needs_redact(name) else value
    except Exception as e:
        log.warning("could not parse env vars: %s", type(e).__name__)

    return {
        "found": True,
        "version": python_version,
        "app_root": app_root,
        "app_url": app_url,
        "startup_file": startup_file,
        "entry_point": entry_point,
        "venv_path": venv_path,
        "env_vars": env_vars,
        "passenger_log": passenger_log,
    }


def extract_databases(page: Page, cfg: Config, cpsess: str, shot: Screenshotter) -> dict:
    out: dict[str, Any] = {"mysql": [], "postgres": "not offered", "app_uses": "unclear"}

    page.goto(deep_link(cfg.url, cpsess, "sql/index.html"), wait_until="domcontentloaded")
    wait_dom(page)
    shot.take(page, "mysql-databases")
    try:
        out["mysql"] = page.evaluate("""() => {
            const out = [];
            document.querySelectorAll('table').forEach(t => {
                const headers = Array.from(t.querySelectorAll('th'))
                    .map(h => (h.innerText || '').trim().toLowerCase());
                const looksRight = headers.some(h => h.includes('database'))
                    && headers.some(h => h.includes('user') || h.includes('privileged'));
                if (!looksRight) return;
                t.querySelectorAll('tbody tr').forEach(tr => {
                    const tds = Array.from(tr.querySelectorAll('td')).map(c => (c.innerText || '').trim());
                    if (tds.length >= 2) {
                        const users = tds[1].split(/[\\n,]+/).map(s => s.trim())
                            .filter(s => s && !/^(privileges|delete|none)$/i.test(s));
                        out.push({name: tds[0], users});
                    }
                });
            });
            return out;
        }""") or []
    except Exception as e:
        log.warning("mysql parse failed: %s", type(e).__name__)

    page.goto(deep_link(cfg.url, cpsess, "postgres/index.html"), wait_until="domcontentloaded")
    wait_dom(page)
    shot.take(page, "postgres-databases")
    try:
        body = page.locator("body").inner_text(timeout=3_000)
        if re.search(r"not\s+enabled|feature.*disabled|404|not found", body, re.I):
            out["postgres"] = "not offered"
        else:
            pg = page.evaluate("""() => {
                const out = [];
                document.querySelectorAll('table').forEach(t => {
                    t.querySelectorAll('tbody tr').forEach(tr => {
                        const tds = Array.from(tr.querySelectorAll('td')).map(c => (c.innerText || '').trim());
                        if (tds.length >= 2) {
                            out.push({
                                name: tds[0],
                                users: tds[1].split(/[\\n,]+/).map(s => s.trim()).filter(Boolean)
                            });
                        }
                    });
                });
                return out;
            }""")
            out["postgres"] = pg if pg else "not offered"
    except Exception:
        out["postgres"] = "not offered"

    if isinstance(out["postgres"], list) and out["postgres"]:
        out["app_uses"] = "postgres" if not out["mysql"] else "unclear"
    elif out["mysql"]:
        out["app_uses"] = "mysql"
    return out


def extract_git(page: Page, cfg: Config, cpsess: str, shot: Screenshotter) -> dict:
    page.goto(
        deep_link(cfg.url, cpsess, "version_control/index.html"),
        wait_until="domcontentloaded",
    )
    wait_dom(page)
    page.wait_for_timeout(1_000)
    shot.take(page, "git-version-control")

    repos = page.evaluate("""() => {
        const out = [];
        const seen = new Set();
        for (const c of document.querySelectorAll(
            '.panel, .card, .repository, li, tr, .repo, [class*="repo"]'
        )) {
            const txt = (c.innerText || '').trim();
            if (!txt) continue;
            if (!/clone\\s*url|repository\\s*path|branch/i.test(txt)) continue;
            if (seen.has(txt)) continue;
            seen.add(txt);
            const get = re => { const m = txt.match(re); return m ? m[1].trim() : null; };
            out.push({
                name: get(/(?:Name|Repository Name)[:\\s]+([^\\n]+)/i),
                remote_url: get(/Clone URL[:\\s]+([^\\n]+)/i),
                branch: get(/Branch[:\\s]+([^\\n]+)/i),
                path: get(/Repository Path[:\\s]+([^\\n]+)/i),
                has_cpanel_yml: /\\.cpanel\\.yml/i.test(txt),
            });
        }
        return out;
    }""") or []

    return {
        "repos": [
            {
                "name": r.get("name"),
                "remote_url": r.get("remote_url"),
                "branch": r.get("branch"),
                "path": r.get("path"),
                "has_cpanel_yml": bool(r.get("has_cpanel_yml")),
            }
            for r in repos
        ]
    }


def extract_ssh(page: Page, cfg: Config, cpsess: str, shot: Screenshotter) -> dict:
    page.goto(deep_link(cfg.url, cpsess, "ssh/index.html"), wait_until="domcontentloaded")
    wait_dom(page)
    shot.take(page, "ssh-access")

    try:
        body = page.locator("body").inner_text(timeout=3_000)
    except Exception:
        body = ""
    m = re.search(r"\bport[^\d]{0,5}(\d{2,5})\b", body, re.I)
    port = int(m.group(1)) if m else None

    try:
        link = page.locator(
            'a:has-text("Manage SSH Keys"), button:has-text("Manage SSH Keys")'
        ).first
        if link.count() > 0:
            link.click()
            wait_dom(page)
            page.wait_for_timeout(1_000)
        else:
            page.goto(
                deep_link(cfg.url, cpsess, "ssh/manage.html"),
                wait_until="domcontentloaded",
            )
            wait_dom(page)
    except Exception:
        pass
    shot.take(page, "ssh-keys")

    keys = page.evaluate("""() => {
        const out = [];
        document.querySelectorAll('table').forEach(t => {
            t.querySelectorAll('tbody tr').forEach(tr => {
                const tds = Array.from(tr.querySelectorAll('td')).map(c => (c.innerText || '').trim());
                if (tds.length >= 2) {
                    const joined = tds.join(' | ').toLowerCase();
                    const authorized = /\\b(authorized|yes)\\b/.test(joined)
                        && !/not\\s*authorized/.test(joined);
                    out.push({name: tds[0], authorized});
                }
            });
        });
        return out;
    }""") or []

    return {"authorized_keys": keys, "port": port}


_JS_LIST_DIR = """() => {
    const out = [];
    const rows = document.querySelectorAll(
        '#filemanager2_table tbody tr, #fileTable tr, table tr'
    );
    rows.forEach(r => {
        const nameCell = r.querySelector('.name, .filename, td.fileName, td a, td span');
        if (!nameCell) return;
        const name = (nameCell.innerText || '').trim();
        if (!name || name === 'Name') return;
        const html = (r.innerHTML || '').toLowerCase();
        const isDir = /icon-dir|icon-folder|fa-folder|class="[^"]*dir[^"]*"/.test(html);
        out.push({name, is_dir: isDir});
    });
    return out;
}"""


def extract_filesystem(
    page: Page, cfg: Config, cpsess: str, shot: Screenshotter, app_root: str | None
) -> dict:
    out: dict[str, Any] = {
        "app_root_listing": [],
        "has_venv": False,
        "has_tmp": False,
        "tmp_contents": None,
        "has_config_json": False,
        "has_git_dir": False,
        "has_passenger_wsgi": False,
    }
    if not app_root:
        log.warning("no app_root captured — skipping file manager listing")
        return out

    page.goto(
        deep_link(cfg.url, cpsess, "filemanager/index.html") + f"?dir={app_root}",
        wait_until="domcontentloaded",
    )
    wait_dom(page)
    page.wait_for_timeout(1_500)
    shot.take(page, "filemanager-app-root")

    def list_dir() -> list[dict]:
        try:
            return page.evaluate(_JS_LIST_DIR) or []
        except Exception:
            return []

    entries: list[dict] = []
    seen: set[str] = set()
    for e in list_dir():
        n = e.get("name")
        if not n or n in seen or n in (".", ".."):
            continue
        seen.add(n)
        entries.append(e)
    out["app_root_listing"] = entries

    by_name = {e["name"]: e for e in entries}
    out["has_venv"] = "venv" in by_name and by_name["venv"].get("is_dir", False)
    out["has_tmp"] = "tmp" in by_name and by_name["tmp"].get("is_dir", False)
    out["has_config_json"] = "config.json" in by_name
    out["has_git_dir"] = ".git" in by_name
    out["has_passenger_wsgi"] = "passenger_wsgi.py" in by_name

    if out["has_tmp"]:
        tmp_path = app_root.rstrip("/") + "/tmp"
        page.goto(
            deep_link(cfg.url, cpsess, "filemanager/index.html") + f"?dir={tmp_path}",
            wait_until="domcontentloaded",
        )
        wait_dom(page)
        page.wait_for_timeout(1_000)
        shot.take(page, "filemanager-tmp")
        out["tmp_contents"] = [
            e["name"] for e in list_dir() if e.get("name") not in (".", "..")
        ]

    return out


# ----- Main --------------------------------------------------------------

def prepare_screenshot_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def run_section(name: str, fn: Callable[[], Any], failures: list[str]) -> Any:
    log.info("section: %s", name)
    try:
        return fn()
    except SystemExit:
        raise
    except Exception as e:
        failures.append(name)
        log.error("section %s failed: %s: %s", name, type(e).__name__, e)
        log.debug("traceback:\n%s", traceback.format_exc())
        return None


def main() -> int:
    cfg = load_config()
    prepare_screenshot_dir(cfg.screenshot_dir)

    failures: list[str] = []
    result: dict[str, Any] = {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=cfg.headless, slow_mo=cfg.slow_mo_ms)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            ignore_https_errors=False,
        )
        context.set_default_timeout(DEFAULT_TIMEOUT_MS)
        context.set_default_navigation_timeout(DEFAULT_NAV_TIMEOUT_MS)
        page = context.new_page()
        shot = Screenshotter(out_dir=cfg.screenshot_dir)

        try:
            cpsess = do_login(page, cfg)
        except SystemExit:
            browser.close()
            return 1
        except Exception as e:
            log.error("login failed: %s: %s", type(e).__name__, e)
            browser.close()
            return 1

        result["general"] = run_section(
            "general", lambda: extract_general(page, cfg, cpsess, shot), failures
        ) or {}
        result["domains"] = run_section(
            "domains", lambda: extract_domains(page, cfg, cpsess, shot), failures
        ) or []
        result["python_app"] = run_section(
            "python_app", lambda: extract_python_app(page, cfg, cpsess, shot), failures
        ) or {"found": False}
        result["databases"] = run_section(
            "databases", lambda: extract_databases(page, cfg, cpsess, shot), failures
        ) or {"mysql": [], "postgres": "not offered", "app_uses": "unclear"}
        result["git_version_control"] = run_section(
            "git_version_control", lambda: extract_git(page, cfg, cpsess, shot), failures
        ) or {"repos": []}
        result["ssh"] = run_section(
            "ssh", lambda: extract_ssh(page, cfg, cpsess, shot), failures
        ) or {"authorized_keys": [], "port": None}

        app_root = (result.get("python_app") or {}).get("app_root")
        result["filesystem"] = run_section(
            "filesystem",
            lambda: extract_filesystem(page, cfg, cpsess, shot, app_root),
            failures,
        ) or {}

        result["screenshots"] = shot.entries
        browser.close()

    cfg.output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cfg.output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(result, f, sort_keys=False, default_flow_style=False)
    log.info("wrote %s", cfg.output_path)

    if failures:
        print(
            "PARTIAL: the following sections failed: " + ", ".join(failures),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log.error("interrupted")
        sys.exit(1)
