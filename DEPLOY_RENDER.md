# Deploying Hartus Floare CRM on Render

## One-time setup
1. Create a GitHub repository (private) and upload the project files
   (the contents of the `nexus_estate_crm` folder, not the zip).
   Do not upload `db.sqlite3`, `.env` or `.venv`.
2. Create a Render account and connect GitHub.
3. In Render choose **New > Blueprint**, select the repository, and apply.
4. Render asks for `DJANGO_SUPERUSER_PASSWORD`. Enter a strong password (12+ characters).

## What happens on each deploy
- `buildCommand` installs `requirements-prod.txt` and collects static files.
- `startCommand` applies migrations, creates the `owner` admin once (skipped if it exists),
  and starts Gunicorn.

## Notes
- The free plan sleeps after inactivity, so the first load can be slow.
- The free PostgreSQL database expires after 30 days on Render unless upgraded. Back up data first.
- Custom domain: add it in Render, then set `DJANGO_ALLOWED_HOSTS` and
  `DJANGO_CSRF_TRUSTED_ORIGINS` (for example `https://crm.example.com`) in the service settings.
