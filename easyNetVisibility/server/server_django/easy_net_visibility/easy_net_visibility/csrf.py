from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware as DjangoCsrfViewMiddleware


class CsrfViewMiddleware(DjangoCsrfViewMiddleware):
    def process_request(self, request):
        if not getattr(settings, 'CSRF_PROTECTION_ENABLED', True):
            return None  # Skip CSRF logic if disabled

        return super().process_request(request)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not getattr(settings, 'CSRF_PROTECTION_ENABLED', True):
            return None  # Skip CSRF validation if disabled

        return super().process_view(request, callback, callback_args, callback_kwargs)
