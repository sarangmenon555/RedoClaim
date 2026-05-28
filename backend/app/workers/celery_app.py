"""Celery async task workers."""
from celery import Celery
from celery.schedules import crontab
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "redoclaim_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.process_document": {"queue": "documents"},
        "app.workers.tasks.run_analysis": {"queue": "analysis"},
        "app.workers.tasks.generate_appeal_task": {"queue": "appeals"},
        "app.workers.tasks.send_deadline_reminders": {"queue": "analysis"},
    },
    beat_schedule={
        # Check IRDAI deadlines daily at 9 AM IST
        "check-deadlines-daily": {
            "task": "app.workers.tasks.send_deadline_reminders",
            "schedule": crontab(hour=9, minute=0),
        },
    },
)
