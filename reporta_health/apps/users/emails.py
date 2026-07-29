from djoser.email import ActivationEmail, PasswordResetEmail


class CustomActivationEmail(ActivationEmail):
    pass


class CustomPasswordResetEmail(PasswordResetEmail):
    pass