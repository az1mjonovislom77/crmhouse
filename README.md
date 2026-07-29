# CRM House

CRM system for a real estate / construction company: clients, leads, bookings,
apartments, installment calculator, contract generation (PDF/DOCX), call-center
and Instagram integrations — behind a single REST API with JWT authentication.

## Features

| Module | What it does |
|---|---|
| `user` | JWT auth (access + rotating refresh token in an httponly cookie), Argon2 password hashing, roles |
| `client` | Client base, per-organization scoping |
| `leads` | Lead pipeline, real-time updates over WebSocket (Django Channels + JWT middleware), AI assistance via Groq API |
| `projects` / `home` / `booking` | Projects → blocks → apartments, interactive showrooms (SVG), reservations and sales |
| `calculator` | Installment/mortgage formulas (subsidy, credit limit, iterative calculation) with a configurable formula engine |
| `contracts` | Contract templates with placeholders, rendered to HTML / PDF (xhtml2pdf + DejaVu fonts for Cyrillic) / DOCX |
| `contact_center` | PBX / Issabel / SIP call-center integration |
| `instagram` | Instagram Graph API: media, comments, replies |
| `stats` | Sales and activity statistics |
| `tasks` | Task management with change history (django-simple-history) |
| `organization` | Multi-organization support, logo processing (auto-convert to WebP) |

Admin panel — Jazzmin-themed Django admin with model translation (uz/ru/en).

## Architecture

The codebase follows a layered, HackSoft-style structure:

- **`<app>/services/`** — business logic (writes, orchestration)
- **`<app>/selectors/`** — read-only queries
- **`<app>/api/`** — serializers, views, urls; views stay thin
- **`common/base/`** — shared base classes (viewsets, serializers, pagination)
- **`config/settings/`** — `base.py` + `local.py` / `production.py` split;
  the environment is selected by the `ENVIRONMENT` variable and **fails secure**:
  anything other than `local` loads production settings

## Tech stack

- Python 3.12, Django 5.2, Django REST Framework
- SimpleJWT (token rotation + blacklist), drf-spectacular (OpenAPI)
- Django Channels + Daphne (WebSockets; Redis channel layer in production)
- Celery + Redis (background jobs, beat schedule)
- PostgreSQL (production) / SQLite (local development)
- xhtml2pdf, python-docx, html-for-docx, openpyxl, pandas (documents & imports)
- Ruff (lint + format), mypy (django-stubs + drf-stubs), coverage, pre-commit

## Getting started

Requirements: Python 3.12. Redis and PostgreSQL are only needed for
production-like runs — local development uses SQLite and an in-memory
channel layer.

```bash
git clone https://github.com/az1mjonovislom77/crm_house.git
cd crm_house

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
# Required
ENVIRONMENT=local                # anything else loads production settings
SECRET_KEY=change-me
INSTAGRAM_ACCESS_TOKEN=dummy     # real token only needed for the instagram module
IG_USER_ID=dummy

# Optional integrations
GROQ_API_KEY=
PBX_BASE_URL=
ISSABEL_BASE_URL=
```

Production additionally requires `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`,
`REDIS_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`
(see `config/settings/production.py` for the full list).

Run it:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- API docs (Swagger UI): http://127.0.0.1:8000/api/swagger/
- OpenAPI schema: http://127.0.0.1:8000/api/schema/
- Admin: http://127.0.0.1:8000/admin/
- Health check: http://127.0.0.1:8000/health/

WebSockets (leads real-time) require the ASGI server:

```bash
daphne config.asgi:application
```

Background jobs (optional, needs Redis):

```bash
celery -A config worker -l info
celery -A config beat -l info
```

## Quality & testing

```bash
python manage.py test            # 386 tests, ~3s (external APIs are mocked)
ruff check .                     # lint
ruff format --check .            # formatting
mypy .                           # strict-ish typing, 0 errors
coverage run manage.py test && coverage report   # 83%, CI gate at 78%
```

Enable the git hooks once:

```bash
pre-commit install
```

CI (GitHub Actions, on every push/PR to `main`) runs the full chain:
ruff lint → format check → mypy → Django system check →
tests with coverage → coverage gate (`--fail-under=78`).

Test conventions: `APITestCase` + `force_authenticate`, external HTTP mocked
with `unittest.mock`, media written to a temp dir via
`override_settings(MEDIA_ROOT=...)`, MD5 password hasher in test mode for speed.

## Notes

- `static/fonts/` (DejaVu TTFs) is required for PDF generation with Cyrillic
  text — do not remove it.
- One-off data import/backfill scripts live in `*/management/commands/` and are
  intentionally excluded from coverage.