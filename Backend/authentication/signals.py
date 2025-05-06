from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def set_idle_session_expiry(sender, request, user, **kwargs):
    if hasattr(user, 'role') and user.role == 'enduser':
        request.session.set_expiry(6000)  # 1 minute for testing
    else:
        request.session.set_expiry(0)   # Expires when browser closes