from celery import shared_task

from django.utils import timezone

from .models import Notification


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={
        "max_retries": 5,
    },
)
def send_notification(
    self,
    notification_id,
):

    notification = Notification.objects.get(
        id=notification_id
    )

    if notification.status == (
        Notification.STATUS_SENT
    ):
        return {
            "status": "already_sent",
            "notification_id": notification.id,
        }

    try:

        print(
            f"Sending notification "
            f"{notification.id}"
        )

        print(
            f"User: {notification.user_id}"
        )

        print(
            f"Title: {notification.title}"
        )

        print(
            f"Message: {notification.message}"
        )

        notification.status = (
            Notification.STATUS_SENT
        )

        notification.sent_at = timezone.now()

        notification.save(
            update_fields=[
                "status",
                "sent_at",
                "updated_at",
            ]
        )

        return {
            "status": "sent",
            "notification_id": notification.id,
        }

    except Exception:

        notification.status = (
            Notification.STATUS_FAILED
        )

        notification.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        raise


@shared_task
def cleanup_old_notifications():

    threshold = (
        timezone.now()
        - timezone.timedelta(
            days=30
        )
    )

    deleted_count, _ = (
        Notification.objects
        .filter(
            created_at__lt=threshold
        )
        .delete()
    )

    return {
        "deleted": deleted_count
    }