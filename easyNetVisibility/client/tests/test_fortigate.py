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
        
        result = fortigate._make_api_request('/api/v2/monitor/system/arp')
        
        self.assertEqual(result['status'], 'success')
        mock_get.assert_called_once()
    
    @patch('fortigate.requests.get')
    def test_make_api_request_failure(self, mock_get):
        """Test failed API request"""
        mock_get.side_effect = Exception("Connection error")
        
        with self.assertRaises(Exception):
            fortigate._make_api_request('/api/v2/monitor/system/arp')
    
    def test_make_api_request_not_initialized(self):
        """Test API request without initialization"""
        fortigate._fortigate_host = None
        
        with self.assertRaises(ValueError):
            fortigate._make_api_request('/api/v2/monitor/system/arp')
        
        # Restore state
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)


class TestFortigateARPTable(unittest.TestCase):
    def setUp(self):
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)
    
    @patch('fortigate._make_api_request')
    def test_get_arp_table_success(self, mock_request):
        """Test successful ARP table retrieval"""
        mock_request.return_value = {
            'status': 'success',
            'results': [
                {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF'},
                {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55'}
            ]
        }
        
        result = fortigate.get_arp_table()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['ip'], '192.168.1.10')
        self.assertEqual(result[0]['mac'], 'AA:BB:CC:DD:EE:FF')
    
    @patch('fortigate._make_api_request')
    def test_get_arp_table_failure(self, mock_request):
        """Test ARP table retrieval failure"""
        mock_request.side_effect = Exception("API error")
        
        result = fortigate.get_arp_table()
        
        # Should return empty list on error
        self.assertEqual(result, [])
    
    @patch('fortigate._make_api_request')
    def test_get_arp_table_non_success_status(self, mock_request):
        """Test ARP table with non-success status"""
        mock_request.return_value = {
            'status': 'error',
            'error': 'Permission denied'
        }
        
        result = fortigate.get_arp_table()
        
        self.assertEqual(result, [])


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


class TestFortigateUserDevices(unittest.TestCase):
    def setUp(self):
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)
    
    @patch('fortigate._make_api_request')
    def test_get_user_devices_success(self, mock_request):
        """Test successful user devices retrieval"""
        mock_request.return_value = {
            'status': 'success',
            'results': [
                {
                    'mac_addr': 'AA:BB:CC:DD:EE:FF',
                    'ipv4_address': '192.168.1.10',
                    'hostname': 'laptop1',
                    'os_name': 'Windows 10'
                },
                {
                    'mac_addr': '00:11:22:33:44:55',
                    'ipv4_address': '192.168.1.20',
                    'hostname': 'server1',
                    'os_name': 'Linux'
                }
            ]
        }
        
        result = fortigate.get_user_devices()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['hostname'], 'laptop1')
        self.assertEqual(result[0]['os_name'], 'Windows 10')
    
    @patch('fortigate._make_api_request')
    def test_get_user_devices_failure(self, mock_request):
        """Test user devices retrieval failure"""
        mock_request.side_effect = Exception("API error")
        
        result = fortigate.get_user_devices()
        
        # Should return empty list on error
        self.assertEqual(result, [])
    
    @patch('fortigate._make_api_request')
    def test_get_user_devices_non_success_status(self, mock_request):
        """Test user devices with non-success status"""
        mock_request.return_value = {
            'status': 'error',
            'error': 'Permission denied'
        }
        
        result = fortigate.get_user_devices()
        
        self.assertEqual(result, [])


class TestFortigateDiscoverDevices(unittest.TestCase):
    def setUp(self):
        fortigate.init('https://192.168.1.1', 'test_api_key_12345', False)
    
    @patch('fortigate.get_user_devices')
    def test_discover_devices_from_user_device_api(self, mock_user_devices):
        """Test device discovery from FortiGate user device API (primary method)"""
        mock_user_devices.return_value = [
            {
                'mac_addr': 'AA:BB:CC:DD:EE:FF',
                'ipv4_address': '192.168.1.10',
                'hostname': 'laptop1',
                'os_name': 'Windows 10'
            },
            {
                'mac_addr': '00:11:22:33:44:55',
                'ipv4_address': '192.168.1.20',
                'hostname': 'server1',
                'os_name': 'Linux'
            }
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 2)
        # MAC addresses should be normalized (no colons, uppercase)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('001122334455', macs)
        
        # Check hostname and vendor (from os_name)
        laptop = [d for d in result if d['mac'] == 'AABBCCDDEEFF'][0]
        self.assertEqual(laptop['hostname'], 'laptop1')
        self.assertEqual(laptop['vendor'], 'Windows 10')
    
    @patch('fortigate.get_user_devices')
    def test_discover_devices_user_api_with_alternative_field_names(self, mock_user_devices):
        """Test device discovery with alternative field names from user device API"""
        mock_user_devices.return_value = [
            {
                'mac': 'AA:BB:CC:DD:EE:FF',  # Alternative field name
                'ip': '192.168.1.10',  # Alternative field name
                'host_name': 'device1',  # Alternative field name
                'os_name': ''  # Empty OS name
            }
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['hostname'], 'device1')
        self.assertEqual(result[0]['vendor'], 'Unknown')  # Empty os_name results in Unknown
    
    @patch('fortigate.get_dhcp_leases')
    @patch('fortigate.get_arp_table')
    @patch('fortigate.get_user_devices')
    def test_discover_devices_fallback_to_arp(self, mock_user_devices, mock_arp, mock_dhcp):
        """Test device discovery falls back to ARP table when user device API returns empty"""
        mock_user_devices.return_value = []  # Empty result triggers fallback
        mock_arp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF'},
            {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55'}
        ]
        mock_dhcp.return_value = []
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 2)
        # MAC addresses should be normalized (no colons, uppercase)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('001122334455', macs)
    
    @patch('fortigate.get_dhcp_leases')
    @patch('fortigate.get_arp_table')
    @patch('fortigate.get_user_devices')
    def test_discover_devices_with_hostnames_from_dhcp(self, mock_user_devices, mock_arp, mock_dhcp):
        """Test device discovery with hostnames from DHCP (fallback path)"""
        mock_user_devices.return_value = []  # Trigger fallback
        mock_arp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF'}
        ]
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'device1'}
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['hostname'], 'device1')
        self.assertEqual(result[0]['ip'], '192.168.1.10')
        self.assertEqual(result[0]['mac'], 'AABBCCDDEEFF')
    
    @patch('fortigate.get_dhcp_leases')
    @patch('fortigate.get_arp_table')
    @patch('fortigate.get_user_devices')
    def test_discover_devices_dhcp_only(self, mock_user_devices, mock_arp, mock_dhcp):
        """Test device discovery with only DHCP data (fallback path)"""
        mock_user_devices.return_value = []  # Trigger fallback
        mock_arp.return_value = []
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'device1'}
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['hostname'], 'device1')
    
    @patch('fortigate.get_user_devices')
    def test_discover_devices_mac_normalization(self, mock_user_devices):
        """Test MAC address normalization with different formats"""
        mock_user_devices.return_value = [
            {
                'mac_addr': 'aa:bb:cc:dd:ee:ff',  # lowercase with colons
                'ipv4_address': '192.168.1.10',
                'hostname': 'device1',
                'os_name': 'Windows'
            },
            {
                'mac_addr': 'AA-BB-CC-DD-EE-11',  # uppercase with dashes
                'ipv4_address': '192.168.1.20',
                'hostname': 'device2',
                'os_name': 'Linux'
            }
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 2)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('AABBCCDDEE11', macs)
    
    @patch('fortigate.get_dhcp_leases')
    @patch('fortigate.get_arp_table')
    @patch('fortigate.get_user_devices')
    def test_discover_devices_empty(self, mock_user_devices, mock_arp, mock_dhcp):
        """Test device discovery with no devices"""
        mock_user_devices.return_value = []  # Trigger fallback
        mock_arp.return_value = []
        mock_dhcp.return_value = []
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 0)
    
    @patch('fortigate.get_user_devices')
    def test_discover_devices_missing_fields(self, mock_user_devices):
        """Test device discovery with missing IP or MAC fields"""
        mock_user_devices.return_value = [
            {'ipv4_address': '192.168.1.10'},  # Missing MAC
            {'mac_addr': 'AA:BB:CC:DD:EE:FF'},  # Missing IP
            {'ipv4_address': '192.168.1.20', 'mac_addr': '00:11:22:33:44:55'}  # Valid
        ]
        
        result = fortigate.discover_devices()
        
        # Only the valid entry should be included
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['ip'], '192.168.1.20')
    
    @patch('fortigate.get_user_devices')
    def test_discover_devices_default_hostname(self, mock_user_devices):
        """Test that IP is used as hostname when hostname is missing"""
        mock_user_devices.return_value = [
            {
                'mac_addr': 'AA:BB:CC:DD:EE:FF',
                'ipv4_address': '192.168.1.10',
                'hostname': '',  # Empty hostname
                'os_name': 'Linux'
            }
        ]
        
        result = fortigate.discover_devices()
        
        self.assertEqual(len(result), 1)
        # When hostname is empty, it should fall back to IP
        self.assertEqual(result[0]['hostname'], '192.168.1.10')


if __name__ == '__main__':
    unittest.main()
