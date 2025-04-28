from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve

EXEMPT_URLS = [
    '/login/',
    '/signup/',
    '/forgot-password/',
]

class InactivityLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip logout logic for exempt URLs
        if any(request.path.startswith(url) for url in EXEMPT_URLS):
            return self.get_response(request)

        # Proceed with session timeout check
        if request.user.is_authenticated and request.session.get_expiry_age() <= 0:
            from django.contrib.auth import logout
            logout(request)
            return redirect('/login/?timeout=1')

        return self.get_response(request)