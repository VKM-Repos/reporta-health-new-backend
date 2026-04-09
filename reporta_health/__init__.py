# This makes config a Python package
from .config.celery import app as celery_app

__all__ = ('celery_app',)