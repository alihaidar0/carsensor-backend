# ============================================================
#  config/settings/production.py
#
#  Stack:
#    Database  → Neon       (serverless PostgreSQL)
#    Files     → Cloudflare R2  (S3-compatible, static + media)
#    Runtime   → GCP Cloud Run  (containerised, auto-scaling)
#    Cache     → Redis      (Upstash or Cloud Memorystore)
# ============================================================

import logging

from .base import *  # noqa: F401, F403
from .base import DATABASES, REST_FRAMEWORK, env

# ── Core ──────────────────────────────────────────────────────
DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# ── Security headers ──────────────────────────────────────────
# Cloud Run sits behind a Google load balancer — trust its headers
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ── Neon Database ─────────────────────────────────────────────
# Neon is serverless — connections open and close per request.
# CONN_MAX_AGE=0  → no persistent connections (required for Neon)
# sslmode=require → Neon enforces TLS, always
#
# Connection string format (set in GCP Secret Manager):
#   postgresql://user:pass@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["OPTIONS"] = {
    "connect_timeout": 10,
    "sslmode": "require",
}

# ── Cloudflare R2 — Static files ──────────────────────────────
# R2 is S3-compatible → uses django-storages + boto3, no special plugin.
# Two separate prefixes in one bucket: /static/ and /media/
#
# R2 credentials (set in GCP Secret Manager):
#   R2_ACCESS_KEY_ID     → R2 API token (not your CF account key)
#   R2_SECRET_ACCESS_KEY → R2 API token secret
#   R2_BUCKET_NAME       → your bucket name
#   R2_ENDPOINT_URL      → https://<accountid>.r2.cloudflarestorage.com
#   R2_CUSTOM_DOMAIN     → your public domain (e.g. cdn.yourdomain.com)
#                          Set this in R2 → Bucket → Settings → Custom Domain
AWS_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("R2_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = env("R2_ENDPOINT_URL")
AWS_S3_CUSTOM_DOMAIN = env("R2_CUSTOM_DOMAIN", default=None)

# R2 does not use AWS regions — this suppresses boto3 warnings
AWS_S3_REGION_NAME = "auto"

# Public read — files are served directly via CDN, no signed URLs
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

# ── Static files → R2 /static/ ───────────────────────────────
STATICFILES_STORAGE = "config.storage_backends.StaticRootS3Boto3Storage"

if AWS_S3_CUSTOM_DOMAIN:
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
else:
    STATIC_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/static/"

# ── Media files → R2 /media/ ─────────────────────────────────
DEFAULT_FILE_STORAGE = "config.storage_backends.MediaRootS3Boto3Storage"

if AWS_S3_CUSTOM_DOMAIN:
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
else:
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/media/"

# ── REST Framework ────────────────────────────────────────────
# No browsable API in production — JSON only
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

# ── CORS ─────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

# ── Structured JSON logging for GCP Cloud Logging ────────────
# Cloud Logging indexes these fields automatically.
# View logs: GCP Console → Logging → Log Explorer
class CloudRunFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json
        import traceback as tb

        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            log_entry["traceback"] = tb.format_exc()

        return json.dumps(log_entry, default=str)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "cloud_run": {"()": CloudRunFormatter},
    },
    "handlers": {
        "cloud_run": {
            "class": "logging.StreamHandler",
            "formatter": "cloud_run",
        },
    },
    "root": {"handlers": ["cloud_run"], "level": "WARNING"},
    "loggers": {
        "django": {
            "handlers": ["cloud_run"],
            "level": env("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["cloud_run"],
            "level": "WARNING",  # never log SQL in production
            "propagate": False,
        },
    },
}
