import datetime
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from easy_net_visibility_server.models import Device, Sensor
from easy_net_visibility_server.pushover_notifier import PushoverNotifier, get_notifier


# Test configuration with Pushover enabled
PUSHOVER_TEST_CONFIG = {
    'enabled': True,
    'user_key': 'test_user_key',
    'api_token': 'test_api_token',
    'alert_new_device': True,
    'alert_gateway_timeout': True,
    'alert_device_offline': True,
    'gateway_timeout_minutes': 10
}


class TestPushoverNotifier(TestCase):
    """Test the PushoverNotifier class"""

    @patch('easy_net_visibility_server.pushover_notifier.PushoverClient')
    @override_settings(PUSHOVER_CONFIG=PUSHOVER_TEST_CONFIG)
    def test_notifier_initialization_success(self, mock_client):
        """Test successful initialization of Pushover notifier"""
        notifier = PushoverNotifier()
        
        self.assertTrue(notifier.enabled)
        self.assertTrue(notifier.alert_new_device)
        self.assertTrue(notifier.alert_gateway_timeout)
        self.assertTrue(notifier.alert_device_offline)
        self.assertEqual(notifier.gateway_timeout_minutes, 10)
        mock_client.assert_called_once_with('test_user_key', api_token='test_api_token')

    @override_settings(PUSHOVER_CONFIG={'enabled': False})
    def test_notifier_disabled(self):
        """Test notifier is disabled when configured as such"""
        notifier = PushoverNotifier()
        
        self.assertFalse(notifier.enabled)

    @override_settings()
    def test_notifier_no_config(self):
        """Test notifier handles missing configuration gracefully"""
        # Remove PUSHOVER_CONFIG if it exists
        if hasattr(TestCase.settings_module, 'PUSHOVER_CONFIG'):
            delattr(TestCase.settings_module, 'PUSHOVER_CONFIG')
        
        notifier = PushoverNotifier()
        
        self.assertFalse(notifier.enabled)

    @patch('easy_net_visibility_server.pushover_notifier.PushoverClient')
    @override_settings(PUSHOVER_CONFIG=PUSHOVER_TEST_CONFIG)
    def test_send_notification_success(self, mock_client_class):
        """Test sending a notification successfully"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        notifier = PushoverNotifier()
        notifier.send_notification("Test message", "Test Title", priority=1)
        
        mock_client.send_message.assert_called_once_with(
            "Test message", title="Test Title", priority=1
        )

    @patch('easy_net_visibility_server.pushover_notifier.PushoverClient')
    @override_settings(PUSHOVER_CONFIG=PUSHOVER_TEST_CONFIG)
    def test_notify_new_device(self, mock_client_class):
        """Test new device notification"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        notifier = PushoverNotifier()
        notifier.notify_new_device("test-device", "192.168.1.100", "AA:BB:CC:DD:EE:FF")
        
        # Verify send_message was called
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args
        
        # Check the message content
        self.assertIn("test-device", call_args[0][0])
        self.assertIn("192.168.1.100", call_args[0][0])
        self.assertIn("AA:BB:CC:DD:EE:FF", call_args[0][0])
        self.assertEqual(call_args[1]['title'], "New Device Detected")

    @patch('easy_net_visibility_server.pushover_notifier.PushoverClient')
    @override_settings(PUSHOVER_CONFIG=PUSHOVER_TEST_CONFIG)
    def test_notify_gateway_timeout(self, mock_client_class):
        """Test gateway timeout notification"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        notifier = PushoverNotifier()
        notifier.notify_gateway_timeout("gateway-1", 15)
        
        # Verify send_message was called
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args
        
        # Check the message content
        self.assertIn("gateway-1", call_args[0][0])
        self.assertIn("15 minutes", call_args[0][0])
        self.assertEqual(call_args[1]['title'], "Gateway Timeout Alert")
        self.assertEqual(call_args[1]['priority'], 1)

    @patch('easy_net_visibility_server.pushover_notifier.PushoverClient')
    @override_settings(PUSHOVER_CONFIG=PUSHOVER_TEST_CONFIG)
    def test_notify_device_offline(self, mock_client_class):
        """Test device offline notification"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        notifier = PushoverNotifier()
        notifier.notify_device_offline("offline-device", "192.168.1.200", "11:22:33:44:55:66")
        
        # Verify send_message was called
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args
        
        # Check the message content
        self.assertIn("offline-device", call_args[0][0])
        self.assertIn("192.168.1.200", call_args[0][0])
        self.assertIn("11:22:33:44:55:66", call_args[0][0])
        self.assertEqual(call_args[1]['title'], "Device Offline Alert")

    @patch('easy_net_visibility_server.pushover_notifier.PushoverClient')
    @override_settings(PUSHOVER_CONFIG={**PUSHOVER_TEST_CONFIG, 'alert_new_device': False})
    def test_notification_not_sent_when_disabled(self, mock_client_class):
        """Test notifications are not sent when alert type is disabled"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        notifier = PushoverNotifier()
        notifier.notify_new_device("test-device", "192.168.1.100", "AA:BB:CC:DD:EE:FF")
        
        # Verify send_message was NOT called
        mock_client.send_message.assert_not_called()


class TestPushoverIntegration(TestCase):
    """Test Pushover integration with API views"""

    @patch('easy_net_visibility_server.pushover_notifier.PushoverClient')
    @patch('easy_net_visibility_server.api_views.get_notifier')
    @override_settings(PUSHOVER_CONFIG=PUSHOVER_TEST_CONFIG)
    def test_new_device_triggers_notification(self, mock_get_notifier, mock_client_class):
        """Test that adding a new device triggers a Pushover notification"""
        mock_notifier = MagicMock()
        mock_get_notifier.return_value = mock_notifier
        
        from easy_net_visibility_server.api_views import _process_device, _create_device_obj_from_data
        
        # Create a new device
        device_data = {
            'hostname': 'new-device',
            'ip': '192.168.1.50',
            'mac': 'AA:BB:CC:DD:EE:FF',
            'vendor': 'TestVendor'
        }
        device = _create_device_obj_from_data(device_data)
        
        # Process the device (should trigger notification)
        status, error = _process_device(device, {})
        
        # Verify the device was added successfully
        self.assertEqual(status, 200)
        self.assertIsNone(error)
        
        # Verify notification was triggered
        mock_notifier.notify_new_device.assert_called_once()
        call_args = mock_notifier.notify_new_device.call_args[0]
        self.assertEqual(call_args[0], 'new-device')
        self.assertEqual(call_args[1], '192.168.1.50')
        self.assertIn('aa:bb:cc:dd:ee:ff', call_args[2].lower())

    @patch('easy_net_visibility_server.pushover_notifier.PushoverClient')
    @patch('easy_net_visibility_server.api_views.get_notifier')
    @override_settings(PUSHOVER_CONFIG=PUSHOVER_TEST_CONFIG)
    def test_existing_device_no_notification(self, mock_get_notifier, mock_client_class):
        """Test that updating an existing device does not trigger notification"""
        mock_notifier = MagicMock()
        mock_get_notifier.return_value = mock_notifier
        
        # Create an existing device
        existing = Device.objects.create(
            hostname='existing-device',
            ip='192.168.1.60',
            mac='11:22:33:44:55:66',
            vendor='TestVendor',
            first_seen=timezone.now(),
            last_seen=timezone.now()
        )
        
        from easy_net_visibility_server.api_views import _process_device, _create_device_obj_from_data
        
        # Update the existing device
        device_data = {
            'hostname': 'existing-device',
            'ip': '192.168.1.61',  # Changed IP
            'mac': '11:22:33:44:55:66',
            'vendor': 'TestVendor'
        }
        device = _create_device_obj_from_data(device_data)
        existing_map = {existing.mac: existing}
        
        # Process the device (should NOT trigger notification)
        status, error = _process_device(device, existing_map)
        
        # Verify the device was updated successfully
        self.assertEqual(status, 200)
        self.assertIsNone(error)
        
        # Verify notification was NOT triggered
        mock_notifier.notify_new_device.assert_not_called()
