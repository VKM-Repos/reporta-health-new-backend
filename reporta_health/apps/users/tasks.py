from celery import shared_task
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def send_otp_email_task(user_id):
    from .emails import send_otp_email
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    send_otp_email(user)