"""
Celery application for LinkMe.

Broker and result backend use Redis so the same infrastructure powers
cache, Channels, and async task processing.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("linkme")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
