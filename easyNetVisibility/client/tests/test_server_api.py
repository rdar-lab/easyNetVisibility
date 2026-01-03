import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the sensor directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sensor'))

import server_api


class TestServerApiInit(unittest.TestCase):
    def setUp(self):
        # Store original values
        self._original_address = server_api._server_api_address
        self._original_username = server_api._server_username
        self._original_password = server_api._server_password
        self._original_validate = server_api._validate_server_identity
        self._original_timeout = server_api._call_timeout
        
        # Reset module state
        server_api._server_api_address = ''
        server_api._server_username = None
        server_api._server_password = None
        server_api._validate_server_identity = False
        server_api._call_timeout = None

    def tearDown(self):
        # Restore original values
        server_api._server_api_address = self._original_address
        server_api._server_username = self._original_username
        server_api._server_password = self._original_password
        server_api._validate_server_identity = self._original_validate
        server_api._call_timeout = self._original_timeout

    def test_init_with_authentication(self):
        server_api.init('https://server.com', 'user', 'pass', True, 30)
        self.assertEqual(server_api._server_api_address, 'https://server.com')
        self.assertEqual(server_api._server_username, 'user')
        self.assertEqual(server_api._server_password, 'pass')
        self.assertTrue(server_api._validate_server_identity)
        self.assertEqual(server_api._call_timeout, 30)

    def test_init_without_authentication(self):
        server_api.init('https://server.com', None, None, False, 60)
        self.assertEqual(server_api._server_api_address, 'https://server.com')
        self.assertIsNone(server_api._server_username)
        self.assertIsNone(server_api._server_password)
        self.assertFalse(server_api._validate_server_identity)
        self.assertEqual(server_api._call_timeout, 60)

    def test_init_with_empty_username(self):
        server_api.init('https://server.com', '', 'pass', True, 30)
        self.assertIsNone(server_api._server_username)
        self.assertIsNone(server_api._server_password)


class TestGenerateSession(unittest.TestCase):
    def setUp(self):
        server_api._server_username = None
        server_api._server_password = None

    @patch('server_api.requests.Session')
    def test_generate_session_with_auth(self, mock_session_class):
        server_api._server_username = 'user'
        server_api._server_password = 'pass'
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        session = server_api.generate_session()
        
        self.assertIsNotNone(session)
        self.assertEqual(session.auth, ('user', 'pass'))

    @patch('server_api.requests.Session')
    def test_generate_session_without_auth(self, mock_session_class):
        server_api._server_username = None
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        session = server_api.generate_session()
        
        self.assertIsNotNone(session)
        # Auth should not be set
        mock_session_class.assert_called_once()


class TestGetCsrfToken(unittest.TestCase):
    @patch('server_api.get')
    def test_get_csrf_token_success(self, mock_get):
        mock_get.return_value = (200, {'csrfToken': 'test-token-123'})
        
        token = server_api.get_csrf_token(MagicMock())
        
        self.assertEqual(token, 'test-token-123')
        mock_get.assert_called_once_with('/api/csrf')

    @patch('server_api.get')
    def test_get_csrf_token_failure(self, mock_get):
        mock_get.return_value = (400, {})
        
        with self.assertRaises(Exception) as context:
            server_api.get_csrf_token(MagicMock())
        
        self.assertIn('unable to obtain CSRF token', str(context.exception))


class TestPost(unittest.TestCase):
    def setUp(self):
        server_api._server_api_address = 'https://test-server.com'
        server_api._validate_server_identity = True
        server_api._call_timeout = 30
        server_api._server_username = 'testuser'
        server_api._server_password = 'testpass'

    @patch('server_api.get_csrf_token')
    @patch('server_api.generate_session')
    def test_post_success(self, mock_generate_session, mock_get_csrf):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_session.post.return_value = mock_response
        
        mock_generate_session.return_value = mock_session
        mock_get_csrf.return_value = 'csrf-token-123'
        
        status_code, response_data = server_api.post('/api/test', {'key': 'value'})
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response_data, {'status': 'success'})
        mock_session.post.assert_called_once()
        
        # Verify the post was called with correct parameters
        call_args = mock_session.post.call_args
        self.assertIn('https://test-server.com/api/test', call_args[0])
        self.assertEqual(call_args[1]['json'], {'key': 'value'})
        self.assertEqual(call_args[1]['verify'], True)
        self.assertEqual(call_args[1]['timeout'], 30)

    @patch('server_api.get_csrf_token')
    @patch('server_api.generate_session')
    def test_post_with_headers(self, mock_generate_session, mock_get_csrf):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_session.post.return_value = mock_response
        
        mock_generate_session.return_value = mock_session
        mock_get_csrf.return_value = 'csrf-token-123'
        
        server_api.post('/api/test', {})
        
        # Verify headers were set correctly
        call_args = mock_session.post.call_args
        headers = call_args[1]['headers']
        self.assertEqual(headers['X-CSRFToken'], 'csrf-token-123')
        self.assertEqual(headers['Accept'], 'application/json')
        self.assertIn('Referer', headers)


class TestGet(unittest.TestCase):
    def setUp(self):
        server_api._server_api_address = 'https://test-server.com'
        server_api._validate_server_identity = False
        server_api._call_timeout = 60
        server_api._server_username = None

    @patch('server_api.generate_session')
    def test_get_success(self, mock_generate_session):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_response.content = b'{"data": "test"}'
        mock_session.get.return_value = mock_response
        
        mock_generate_session.return_value = mock_session
        
        status_code, response_data = server_api.get('/api/data')
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response_data, {'data': 'test'})
        mock_session.get.assert_called_once()
        
        # Verify the get was called with correct parameters
        call_args = mock_session.get.call_args
        self.assertIn('https://test-server.com/api/data', call_args[0])
        self.assertEqual(call_args[1]['verify'], False)
        self.assertEqual(call_args[1]['timeout'], 60)


class TestApiHelpers(unittest.TestCase):
    @patch('server_api.post')
    def test_add_devices(self, mock_post):
        mock_post.return_value = (200, {'status': 'success'})
        
        devices = [
            {'mac': 'AA:BB:CC:DD:EE:FF', 'ip': '192.168.1.1'},
            {'mac': 'AA:BB:CC:DD:EE:00', 'ip': '192.168.1.2'}
        ]
        
        result = server_api.add_devices(devices)
        
        self.assertEqual(result, (200, {'status': 'success'}))
        mock_post.assert_called_once_with('/api/addDevices', {'devices': devices})

    @patch('server_api.post')
    def test_add_ports(self, mock_post):
        mock_post.return_value = (200, {'status': 'success'})
        
        ports = [
            {'mac': 'AA:BB:CC:DD:EE:FF', 'port': 80, 'protocol': 'TCP'},
            {'mac': 'AA:BB:CC:DD:EE:FF', 'port': 443, 'protocol': 'TCP'}
        ]
        
        result = server_api.add_ports(ports)
        
        self.assertEqual(result, (200, {'status': 'success'}))
        mock_post.assert_called_once_with('/api/addPorts', {'ports': ports})

    @patch('server_api.post')
    def test_report_sensor_health(self, mock_post):
        mock_post.return_value = (200, {'status': 'success'})
        
        health_info = {'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'sensor1'}
        
        result = server_api.report_sensor_health(health_info)
        
        self.assertEqual(result, (200, {'status': 'success'}))
        mock_post.assert_called_once_with('/api/sensorHealth', health_info)


if __name__ == '__main__':
    unittest.main()
