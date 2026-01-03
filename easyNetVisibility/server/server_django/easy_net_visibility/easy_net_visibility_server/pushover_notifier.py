"""
Pushover notification service for sending alerts about network devices and sensors.
"""
import logging
from typing import Optional
from django.conf import settings

try:
    from pushover_complete import PushoverAPI
except ImportError:
    PushoverAPI = None

_logger = logging.getLogger(__name__)


class PushoverNotifier:
    """
    Handles sending Pushover notifications based on configuration.
    """
    
    def __init__(self):
        self.enabled = False
        self.client = None
        self.user_key = None
        self.alert_new_device = False
        self.alert_gateway_timeout = False
        self.alert_device_offline = False
        self.gateway_timeout_minutes = 10
        
        self._load_config()
    
    def _load_config(self):
        """Load Pushover configuration from Django settings."""
        pushover_config = getattr(settings, 'PUSHOVER_CONFIG', None)
        
        if not pushover_config:
            _logger.debug("Pushover configuration not found in settings")
            return
        
        if not PushoverAPI:
            _logger.warning("pushover-complete library not installed, notifications disabled")
            return
        
        self.enabled = pushover_config.get('enabled', False)
        
        if not self.enabled:
            _logger.debug("Pushover notifications are disabled")
            return
        
        user_key = pushover_config.get('user_key', '')
        api_token = pushover_config.get('api_token', '')
        
        if not user_key or not api_token:
            _logger.error("Pushover user_key or api_token not configured")
            self.enabled = False
            return
        
        try:
            self.client = PushoverAPI(api_token)
            self.user_key = user_key
            self.alert_new_device = pushover_config.get('alert_new_device', False)
            self.alert_gateway_timeout = pushover_config.get('alert_gateway_timeout', False)
            self.alert_device_offline = pushover_config.get('alert_device_offline', False)
            self.gateway_timeout_minutes = pushover_config.get('gateway_timeout_minutes', 10)
            _logger.info(f"Pushover notifier initialized: new_device={self.alert_new_device}, "
                        f"gateway_timeout={self.alert_gateway_timeout}, "
                        f"device_offline={self.alert_device_offline}")
        except Exception as e:
            _logger.error(f"Failed to initialize Pushover client: {e}")
            self.enabled = False
    
    def send_notification(self, message: str, title: str = "EasyNetVisibility", priority: int = 0):
        """
        Send a Pushover notification.
        
        Args:
            message: The notification message
            title: The notification title
            priority: Priority level (-2 to 2, default 0)
        """
        if not self.enabled or not self.client:
            _logger.debug(f"Notification not sent (disabled): {message}")
            return
        
        try:
            self.client.send_message(self.user_key, message, title=title, priority=priority)
            _logger.info(f"Pushover notification sent: {title} - {message}")
        except Exception as e:
            _logger.error(f"Failed to send Pushover notification: {e}")
    
    def notify_new_device(self, device_name: str, ip: str, mac: str):
        """
        Send alert for newly detected device.
        
        Args:
            device_name: Device hostname or nickname
            ip: Device IP address
            mac: Device MAC address
        """
        if not self.alert_new_device:
            return
        
        message = f"New device detected:\nName: {device_name}\nIP: {ip}\nMAC: {mac}"
        self.send_notification(message, title="New Device Detected", priority=0)
    
    def notify_gateway_timeout(self, sensor_name: str, minutes_offline: int):
        """
        Send alert for gateway (sensor) timeout.
        
        Args:
            sensor_name: Sensor hostname
            minutes_offline: Minutes since last seen
        """
        if not self.alert_gateway_timeout:
            return
        
        message = f"Gateway '{sensor_name}' has not been detected for {minutes_offline} minutes"
        self.send_notification(message, title="Gateway Timeout Alert", priority=1)
    
    def notify_device_offline(self, device_name: str, ip: str, mac: str):
        """
        Send alert for device going offline.
        
        Args:
            device_name: Device hostname or nickname
            ip: Device IP address
            mac: Device MAC address
        """
        if not self.alert_device_offline:
            return
        
        message = f"Device went offline:\nName: {device_name}\nIP: {ip}\nMAC: {mac}"
        self.send_notification(message, title="Device Offline Alert", priority=0)


# Global notifier instance
_notifier: Optional[PushoverNotifier] = None


def get_notifier() -> PushoverNotifier:
    """Get or create the global PushoverNotifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = PushoverNotifier()
    return _notifier
