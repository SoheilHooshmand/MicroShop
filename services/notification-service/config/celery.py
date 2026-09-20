import os

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)


app = Celery(
    "notification_service"
)


app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

app.conf.beat_schedule = {

    "cleanup-old-notifications": {
        "task": (
            "notifications.tasks."
            "cleanup_old_notifications"
        ),
        "schedule": crontab(
            hour=3,
            minute=0,
        ),
    },

}

app.autodiscover_tasks()