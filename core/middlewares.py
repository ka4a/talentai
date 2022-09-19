from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware


class SessionMiddleware(SessionMiddleware):
    """
    Overridden to be mostly the same except add check for paths to exclude from
    saving session.
    """

    def process_response(self, request, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.

        Additionally checks accessed path to decide if session should be saved.
        """
        if request.path not in settings.SESSION_SAVE_EXCLUDE_PATHS:
            request.session.modified = True
        return super().process_response(request, response)


def authentication_middleware(get_response):
    """Add custom X-Authenticated header to provide authentication status"""

    def middleware(request):
        response = get_response(request)
        if request.user.is_authenticated:
            if request.user.is_staff:
                response['X-Authenticated'] = 'STAFF_USER'
            else:
                response['X-Authenticated'] = 'CASUAL_USER'
        else:
            response['X-Authenticated'] = 'NOT_AUTHENTICATED'

        return response

    return middleware
