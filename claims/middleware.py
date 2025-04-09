from django.shortcuts import redirect

class InactivityLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Session is active and user is logged in
            return self.get_response(request)

        # If session expired and this was a logged-in page, redirect with timeout message
        if request.path != '/logout/' and request.path != '/accounts/login/':
            return redirect('/logout/?timeout=1')

        return self.get_response(request)
