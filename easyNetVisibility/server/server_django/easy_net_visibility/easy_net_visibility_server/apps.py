from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class EasyNetVisibilityServerConfig(AppConfig):
    name = 'easy_net_visibility_server'

    def ready(self):
        """
        Called when Django starts. Initialize background services here.
        """
        # Only start monitoring service in production (when running with Gunicorn/WSGI)
        # and only in the main process (not in reloader or worker processes)
        import os
        import sys
        
        # Check if we're running the main Django server (not management commands or tests)
        # and not in the autoreloader process
        is_main_process = (
            'runserver' not in sys.argv and
            'test' not in sys.argv and
            os.environ.get('RUN_MAIN') != 'true'  # Not the autoreloader
        )
        
        if is_main_process:
            try:
                from easy_net_visibility_server.monitoring_service import get_monitoring_service
                monitoring_service = get_monitoring_service()
                monitoring_service.start()
                logger.info("Network monitoring service started successfully")
            except Exception as e:
                logger.error(f"Failed to start network monitoring service: {e}")

