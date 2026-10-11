# Hartus Floare — Real Estate CRM Starter

A premium-styled, responsive Django CRM starter focused on property sales workflows. It is a real codebase—not just a screenshot or design prompt—and is intended to be a strong foundation for a production project.

## Included modules

- **Overview dashboard:** lead counts, active pipeline value, closed value this month, calls today, task reminders, deal-stage breakdown and a six-month revenue chart.
- **Lead management:** contact profiles, source, buying/renting/selling/investment intent, property requirements, budgets, status, priority, assignment, notes and next follow-up.
- **Call activity:** manual call logging, direction, outcome, duration, notes and next follow-up. The app does not place calls by itself; telephony integration requires a provider and credentials.
- **Property inventory:** sale/rent listings, reference IDs, availability status, price, area/units, rooms, location, owner/contact, assigned agent and description.
- **Deals:** stages, lead/property links, deal values, expected close dates and commission calculations.
- **Follow-up tasks:** due date, priority, assignee, linked records, overdue calculation and complete/reopen action.
- **Global search, lead CSV export, Django admin, login/logout, demo-data seed command and model/view tests.**
- **Claude Code guidance:** `CLAUDE.md` plus five focused `.claude/skills/` files for architecture, UI, security, QA and real-estate workflows.

## Visual system

The interface uses a deep evergreen/navy sidebar, warm off-white canvas, restrained jade highlights, brass accents, soft borders and compact typography. Layouts are responsive and include useful empty states, filters, pagination, accessible labels and small-screen navigation.

## Requirements

- Python 3.12+
- Django 6.1.1 (pinned in `requirements.txt`)
- SQLite for local development (included with Python)
- Optional: PostgreSQL + `psycopg[binary]` for a production database

## Run locally (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations crm
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and sign in with the user you created. Use `http://127.0.0.1:8000/admin/` to manage users and inspect records.

### macOS / Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py check
python manage.py makemigrations crm
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Load synthetic demo data

After creating a staff user with `createsuperuser`:

```bash
python manage.py seed_demo --username YOUR_ADMIN_USERNAME --count 18
```

To remove the previous demo records first and reseed them:

```bash
python manage.py seed_demo --username YOUR_ADMIN_USERNAME --count 18 --clear-demo
```

The records are clearly named `DEMO`, and email addresses use the reserved `.invalid` domain. Names, numbers, prices and properties are synthetic. Never treat them as real customer/listing information.

## Tests and quality checks

```bash
python manage.py check
python manage.py test
```

The included tests cover lead initials/budget formatting, automatic property references, won-deal timestamp/commission calculations, task completion timestamps, authentication, a basic agent-scope check and CSV export. Run these checks again after every Claude-assisted code change.

## Environment variables

Copy `.env.example` to `.env` as a reference. The starter intentionally avoids requiring a dotenv package; export environment variables in your shell or configure them in your hosting platform. `config/settings.py` reads:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (`True` locally, `False` in production)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `DJANGO_CSRF_TRUSTED_ORIGINS` (comma-separated full origins)
- `DB_ENGINE` (`sqlite` or `postgresql`), `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

For PostgreSQL, install `psycopg[binary]` in your deployment environment and set `DB_ENGINE=postgresql` plus the database variables.

## Important before production

This is a functional starter, not a certified enterprise deployment. Before using real clients or deploying publicly:

1. Set a strong, unique `DJANGO_SECRET_KEY`; set `DJANGO_DEBUG=False`; configure `ALLOWED_HOSTS`, HTTPS, trusted origins and the production database.
2. Review role/permission policy with your actual business structure. In this starter, staff/superusers can manage team assignments; ordinary users have scoped access to many CRM records, while property inventory is visible workspace-wide.
3. Add backups, log retention, monitoring, dependency scanning and a tested restore process.
4. Configure email/SMS/WhatsApp/telephony providers only after supplying verified credentials and consent/compliance requirements.
5. Add data retention, privacy/export/deletion policy and audit trails appropriate to your jurisdiction and agency.
6. Consider object storage for uploaded property photos; image upload and storage are not wired up in this first starter.
7. Run tests against the intended database and hosting stack before production.

## Claude Code workflow

Open this folder in Claude Code. Start with the instructions in `CLAUDE.md`; the skills in `.claude/skills/` provide focused project rules for the main work streams. Recommended first request: “Inspect the entire repository, run Django checks and tests, identify concrete bugs and UX gaps, then fix them in small tested changes. Do not claim any integration works unless the code and credentials actually support it.”

### Recommended next upgrades

- Team roles/permissions matrix and audit history
- Lead import with duplicate detection and validation preview
- Kanban lead/deal boards with drag-and-drop safeguards
- Email, WhatsApp and telephony integrations with delivery logs
- Property photos, map/geocoding and viewing appointments
- Scheduled reminders, SLA alerts and team activity reports
- REST API, API permissions, OpenAPI docs and integration tests
- PostgreSQL-backed staging, CI and deployment manifests

## Technology notes

Django 6.1.1 is pinned from the official Django release listing. Review the official release/security notes before upgrading: https://www.djangoproject.com/download/ and https://docs.djangoproject.com/en/6.1/releases/.
