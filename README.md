# Django Project

> Started from [django-project-template](https://github.com/YOUR_USERNAME/django-project-template)

## Stack

- **Runtime**: Python 3.14 · Django 5.x · Django REST Framework
- **Database**: PostgreSQL 17 (dev) · Neon (production)
- **Cache / Queue**: Redis 8 · Celery
- **Storage**: Local (dev) · Cloudflare R2 (production)
- **Deploy**: GCP Cloud Run

## Quick Start

```bash
# 1. Open in VS Code Dev Container (pulls the dev image)
#    VS Code → "Reopen in Container"

# 2. Initialize uv project
uv init --no-package .
uv venv
source .venv/bin/activate

# 3. Install Django and core packages
uv add django djangorestframework django-environ psycopg[binary,pool] \
       dj-database-url djangorestframework-simplejwt django-allauth \
       django-cors-headers django-filter drf-spectacular \
       celery django-celery-beat django-celery-results django-redis \
       django-storages boto3 whitenoise gunicorn uvicorn Pillow

uv add --dev pytest pytest-django pytest-cov factory-boy faker \
            django-debug-toolbar django-silk ipython django-extensions \
            mypy django-stubs djangorestframework-stubs ruff

# 4. Create Django project
django-admin startproject config .

# 5. Set up environment
cp .env.example .env
# Edit .env with your values

# 6. Run migrations
python manage.py migrate

# 7. Start server
python manage.py runserver 0.0.0.0:8000
# → http://localhost:8000
```

## Project Structure

```
├── apps/               ← your Django apps go here
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── docker/
│   └── Dockerfile.prod
├── scripts/
│   └── entrypoint.prod.sh
├── .github/workflows/
│   ├── ci.yml          ← lint + test
│   ├── docker.yml      ← build prod image
│   └── deploy.yml      ← deploy to Cloud Run
└── docker-compose.yml
```

## CI/CD

```
feature/* → CI (lint + test)
develop   → CI → build prod image
main      → build prod image → deploy staging → smoke test → deploy prod
```

## Required GitHub Secrets

| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `GCP_SA_KEY` | GCP Service Account JSON |
| `GCP_REGION` | e.g. `us-central1` |
| `CLOUD_RUN_SERVICE_STAGING` | Staging service name |
| `CLOUD_RUN_SERVICE_PROD` | Production service name |
