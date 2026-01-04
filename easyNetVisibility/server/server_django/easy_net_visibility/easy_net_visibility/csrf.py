from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware as DjangoCsrfViewMiddleware


class CsrfViewMiddleware(DjangoCsrfViewMiddleware):
    def process_request(self, request):
        if not getattr(settings, 'CSRF_PROTECTION_ENABLED', True):
            return None  # Skip CSRF logic if disabled

        return super().process_request(request)
