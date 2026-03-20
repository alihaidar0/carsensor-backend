from .base import *  # noqa: F401, F403, F405

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
    "django_extensions",
]

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "mailpit"
EMAIL_PORT = 1025
