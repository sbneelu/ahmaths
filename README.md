# AHmaths.com

A revision website for the Scottish Advanced Higher Mathematics course. Live at https://ahmaths.com. The repository for the older version of the site written in PHP is available [here](https://github.com/sbneelu/ahmaths-old).

## Quickstart

```bash
git clone https://github.com/sbneelu/ahmaths.git
cd ahmaths
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set the required environment variables (or place a `config.json` at the project root with the equivalent keys):

Required:
- `SECRET_KEY` — Flask session secret. Any long random string.
- `DATABASE_URL` — SQLAlchemy connection string, e.g. `sqlite:///ahmaths.db` or `postgresql+pg8000://user:pass@host/db`.

Optional (only needed for the relevant feature):
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD` — SMTP credentials used by the contact form and password-reset emails.
- `EMAIL_NAME`, `EMAIL_ADDRESS` — sender name/address for outbound mail (default `AHmaths` / `MAIL_USERNAME`).
- `CONTACT_RECIPIENT` — address that receives contact-form submissions (default `EMAIL_ADDRESS`).
- `RECAPTCHA_SECRET`, `RECAPTCHA_SITEKEY` — Google reCAPTCHA v2 keys for the contact form.
- `GA_MEASUREMENT_ID` — Google Analytics measurement ID injected into the base template.
- `SESSION_COOKIE_SECURE` — `true`/`false`; defaults to `true`. Set to `false` for plain-HTTP local development.

Seed the database and run the dev server:

```bash
python setup_db.py     # creates tables and inserts topics / subtopics / papers / questions
python run.py          # serves on http://localhost:5000
```

`setup_db.py` is idempotent — re-running it will not duplicate rows.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## Adding a past paper

`scripts/add_new_paper_to_db.py` ingests a per-paper data file and either prints/writes the SQL it would run (default) or applies the inserts directly via the Flask app context (`--commit`). Existing paper and question rows are skipped, so the script is safe to re-run.

Input file format (one paper per file):

```
2025 Paper 1
1 4 youtubeID?start=0 binomial_theorem binomial_expansion
2 5 youtubeID?start=10 differentiation chain_rule,product_rule
// comments start with //; use _ for an empty field, e.g. 3 5 _ integration parts
```

Usage:

```bash
python scripts/add_new_paper_to_db.py path/to/2025-paper-1.txt              # dry run; writes a .sql file
python scripts/add_new_paper_to_db.py path/to/2025-paper-1.txt --commit     # writes directly to the DB
```

After running, the printed steps cover renaming the PDF + marking-instructions files (`AH-Maths-<paper id>.pdf`, `AH-Maths-MI-<paper id>.pdf`) and uploading them under `ahmaths/static/sqa-papers/`.
