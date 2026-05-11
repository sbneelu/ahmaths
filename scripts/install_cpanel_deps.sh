#!/usr/bin/env bash
# One-shot installer for cpanel_info.py dependencies.
# - pip-installs the Python deps listed in cpanel_info_requirements.txt
# - installs the Chromium browser used by Playwright
#
# Tries `playwright install --with-deps chromium` first to also pull in the
# system shared libraries that Chromium needs. That step requires sudo on most
# distros; if it fails (no sudo / not Debian-like) we fall back to a plain
# `playwright install chromium` and print a note so the user knows they may
# need to install system libs themselves.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQS="${SCRIPT_DIR}/cpanel_info_requirements.txt"

if [[ ! -f "${REQS}" ]]; then
    echo "ERROR: cannot find ${REQS}" >&2
    exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Installing Python packages from ${REQS}"
"${PYTHON_BIN}" -m pip install -r "${REQS}"

echo "==> Installing Playwright Chromium browser (trying --with-deps first)"
if "${PYTHON_BIN}" -m playwright install --with-deps chromium; then
    echo "==> Playwright Chromium installed with system deps."
else
    echo "==> '--with-deps' failed (most likely needs sudo or is a non-Debian distro)."
    echo "==> Falling back to 'playwright install chromium' without system deps."
    "${PYTHON_BIN}" -m playwright install chromium
    cat <<'EOF'

NOTE: Playwright installed Chromium but skipped the system-level shared
libraries. If you hit "missing libnss3 / libatk / libxcomposite" errors at
runtime, install them via your package manager, e.g. on Debian/Ubuntu:

    sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
        libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

Or simply re-run this installer with sudo available so 'playwright install
--with-deps chromium' can succeed.
EOF
fi

echo "==> Done."
