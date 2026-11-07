from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication subclass that skips CSRF validation.
    Enables seamless API calls from external frontends (e.g., React, Vue, mobile apps)
    even when a browser session exists in the same browser.
    """
    def enforce_csrf(self, request):
        return
