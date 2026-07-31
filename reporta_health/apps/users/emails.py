from django.conf import settings
from django.core.mail import send_mail

from djoser.email import ActivationEmail, PasswordResetEmail


class CustomActivationEmail(ActivationEmail):
    pass


class CustomPasswordResetEmail(PasswordResetEmail):
    pass


def send_otp_email(user):
    """Send the current OTP code to the user's email."""
    send_mail(
        subject="Your Reporta Health verification code",
        message=(
            f"Hi {user.first_name or user.username},\n\n"
            f"Your verification code is: {user.otp_code}\n\n"
            f"This code expires in 5 minutes."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else None,
        recipient_list=[user.email],
        fail_silently=False,
    )
