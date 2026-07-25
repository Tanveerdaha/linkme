"""
LinkMe Django project package.

Celery is imported here so the worker discovers the app when Django starts.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
