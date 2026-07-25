"""
WSGI config for LinkMe.

Used by gunicorn for traditional HTTP deployments. Prefer ASGI (Daphne)
when WebSockets are required.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
