import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the sensor directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sensor'))

import fortigate


class TestFortigateInit(unittest.TestCase):
    def test_init_sets_credentials(self):
        """Test that init properly sets connection parameters"""
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)
        
        self.assertEqual(fortigate._fortigate_host, 'https://192.168.1.1')
        self.assertEqual(fortigate._fortigate_api_key, 'test_api_key_12345')
        self.assertEqual(fortigate._validate_ssl, False)


class TestFortigateAPIRequest(unittest.TestCase):
    def setUp(self):
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)
    
    @patch('fortigate.requests.get')
    def test_make_api_request_success(self, mock_get):
        """Test successful API request"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success', 'results': []}
        mock_get.return_value = mock_response
        
        result = fortigate._make_api_request('/api/v2/monitor/system/dhcp/select')
        
        self.assertEqual(result['status'], 'success')
        mock_get.assert_called_once()
    
    @patch('fortigate.requests.get')
    def test_make_api_request_failure(self, mock_get):
        """Test failed API request"""
        mock_get.side_effect = Exception("Connection error")
        
        with self.assertRaises(Exception):
            fortigate._make_api_request('/api/v2/monitor/system/dhcp/select')
    
    def test_make_api_request_not_initialized(self):
        """Test API request without initialization"""
        fortigate._fortigate_host = None
        
        with self.assertRaises(ValueError):
            fortigate._make_api_request('/api/v2/monitor/system/dhcp/select')
        
        # Restore state
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)


class TestFortigateDHCPLeases(unittest.TestCase):
    def setUp(self):
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)
    
    @patch('fortigate._make_api_request')
    def test_get_dhcp_leases_success(self, mock_request):
        """Test successful DHCP leases retrieval"""
        mock_request.return_value = {
            'status': 'success',
            'results': [
                {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'device1'},
                {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55', 'hostname': 'device2'}
            ]
        }
        
        result = fortigate.get_dhcp_leases()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['hostname'], 'device1')
    
    @patch('fortigate._make_api_request')
    def test_get_dhcp_leases_failure(self, mock_request):
        """Test DHCP leases retrieval failure"""
        mock_request.side_effect = Exception("API error")
        
        result = fortigate.get_dhcp_leases()
        
        # Should return empty list on error
        self.assertEqual(result, [])


class TestFortigateFirewallSessions(unittest.TestCase):
    def setUp(self):
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)
    
    @patch('fortigate._make_api_request')
    def test_get_firewall_sessions_success(self, mock_request):
        """Test successful firewall sessions retrieval"""
        mock_request.return_value = {
            'status': 'success',
            'results': [
                {'src': '192.168.1.10', 'srcmac': 'AA:BB:CC:DD:EE:FF', 'dst': '8.8.8.8'},
                {'src': '192.168.1.20', 'srcmac': '00:11:22:33:44:55', 'dst': '1.1.1.1'}
            ]
        }
        
        result = fortigate.get_firewall_sessions()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['src'], '192.168.1.10')
        self.assertEqual(result[0]['srcmac'], 'AA:BB:CC:DD:EE:FF')
    
    @patch('fortigate._make_api_request')
    def test_get_firewall_sessions_failure(self, mock_request):
        """Test firewall sessions retrieval failure"""
        mock_request.side_effect = Exception("API error")
        
        result = fortigate.get_firewall_sessions()
        
        # Should return empty list on error
        self.assertEqual(result, [])
    
    @patch('fortigate._make_api_request')
    def test_get_firewall_sessions_non_success_status(self, mock_request):
        """Test firewall sessions with non-success status"""
        mock_request.return_value = {
            'status': 'error',
            'error': 'Permission denied'
        }
        
        result = fortigate.get_firewall_sessions()
        
        self.assertEqual(result, [])


class TestFortigateDiscoverDevices(unittest.TestCase):
    def setUp(self):
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_from_dhcp_only(self, mock_dhcp, mock_sessions):
        """Test device discovery from DHCP leases only"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'laptop1'},
            {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55', 'hostname': 'server1'}
        ]
        mock_sessions.return_value = []
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 2)
        # MAC addresses should be normalized (no colons, uppercase)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('001122334455', macs)
        
        # Check hostname
        laptop = [d for d in result if d['mac'] == 'AABBCCDDEEFF'][0]
        self.assertEqual(laptop['hostname'], 'laptop1')
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_from_sessions_only(self, mock_dhcp, mock_sessions):
        """Test device discovery from firewall sessions only"""
        mock_dhcp.return_value = []
        mock_sessions.return_value = [
            {'src': '192.168.1.10', 'srcmac': 'AA:BB:CC:DD:EE:FF', 'dst': '8.8.8.8'},
            {'src': '192.168.1.20', 'srcmac': '00:11:22:33:44:55', 'dst': '1.1.1.1'}
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 2)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('001122334455', macs)
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_combined_sources(self, mock_dhcp, mock_sessions):
        """Test device discovery combining DHCP and firewall sessions"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'laptop1'}
        ]
        mock_sessions.return_value = [
            {'src': '192.168.1.10', 'srcmac': 'AA:BB:CC:DD:EE:FF', 'dst': '8.8.8.8'},
            {'src': '192.168.1.20', 'srcmac': '00:11:22:33:44:55', 'dst': '1.1.1.1'}
        ]
        
        result = fortigate.discover_devices()
        
        # Should have 2 unique devices (one from DHCP + sessions, one from sessions only)
        self.assertEqual(len(result), 2)
        
        # Device from DHCP should have hostname from DHCP
        laptop = [d for d in result if d['mac'] == 'AABBCCDDEEFF'][0]
        self.assertEqual(laptop['hostname'], 'laptop1')
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_hostname_enrichment(self, mock_dhcp, mock_sessions):
        """Test that firewall session devices are enriched with DHCP hostnames"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'enriched-hostname'}
        ]
        mock_sessions.return_value = [
            {'src': '192.168.1.10', 'srcmac': 'AA:BB:CC:DD:EE:FF', 'dst': '8.8.8.8'}
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 1)
        # Should have enriched hostname from DHCP
        self.assertEqual(result[0]['hostname'], 'enriched-hostname')
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_alternative_field_names(self, mock_dhcp, mock_sessions):
        """Test device discovery with alternative field names"""
        mock_dhcp.return_value = [
            {'ip-address': '192.168.1.10', 'mac-address': 'AA:BB:CC:DD:EE:FF', 'host-name': 'device1'}
        ]
        mock_sessions.return_value = [
            {'srcaddr': '192.168.1.20', 'src_mac': '00:11:22:33:44:55', 'dstaddr': '8.8.8.8'}
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 2)
        # Check that alternative field names are handled
        device1 = [d for d in result if d['mac'] == 'AABBCCDDEEFF'][0]
        self.assertEqual(device1['hostname'], 'device1')
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_empty(self, mock_dhcp, mock_sessions):
        """Test device discovery with no devices"""
        mock_dhcp.return_value = []
        mock_sessions.return_value = []
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 0)
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_missing_fields(self, mock_dhcp, mock_sessions):
        """Test device discovery with missing IP or MAC fields"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10'},  # Missing MAC
            {'mac': 'AA:BB:CC:DD:EE:FF'},  # Missing IP
            {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55', 'hostname': 'valid'}  # Valid
        ]
        mock_sessions.return_value = []
        
        result = fortigate.discover_devices()
        
        # Only the valid entry should be included
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['ip'], '192.168.1.20')
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_default_hostname(self, mock_dhcp, mock_sessions):
        """Test that IP is used as hostname when hostname is missing"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': ''}  # Empty hostname
        ]
        mock_sessions.return_value = []
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 1)
        # When hostname is empty, it should fall back to IP
        self.assertEqual(result[0]['hostname'], '192.168.1.10')
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_mac_normalization(self, mock_dhcp, mock_sessions):
        """Test MAC address normalization with different formats"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'aa:bb:cc:dd:ee:ff', 'hostname': 'device1'},  # lowercase
            {'ip': '192.168.1.20', 'mac': 'AA-BB-CC-DD-EE-11', 'hostname': 'device2'}  # dashes
        ]
        mock_sessions.return_value = []
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 2)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('AABBCCDDEE11', macs)
    
    @patch('fortigate.get_firewall_sessions')
    @patch('fortigate.get_dhcp_leases')
    def test_discover_devices_deduplication(self, mock_dhcp, mock_sessions):
        """Test that devices are deduplicated by MAC address"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'hostname-from-dhcp'}
        ]
        mock_sessions.return_value = [
            {'src': '192.168.1.10', 'srcmac': 'AA:BB:CC:DD:EE:FF', 'dst': '8.8.8.8'}
        ]
        
        result = fortigate.discover_devices()
        
        # Should only have 1 device despite appearing in both sources
        self.assertEqual(len(result), 1)
        # Should use hostname from DHCP (first source)
        self.assertEqual(result[0]['hostname'], 'hostname-from-dhcp')


if __name__ == '__main__':
    unittest.main()
