import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the sensor directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sensor'))

import ddwrt


class TestDDWRTInit(unittest.TestCase):
    def test_init_sets_credentials(self):
        """Test that init properly sets connection parameters"""
        ddwrt.init('http://192.168.1.1', 'admin', 'test_password', False)
        
        self.assertEqual(ddwrt._ddwrt_host, 'http://192.168.1.1')
        self.assertEqual(ddwrt._ddwrt_username, 'admin')
        self.assertEqual(ddwrt._ddwrt_password, 'test_password')
        self.assertEqual(ddwrt._validate_ssl, False)


class TestDDWRTDHCPLeases(unittest.TestCase):
    def setUp(self):
        ddwrt.init('http://192.168.1.1', 'admin', 'test_password', False)
    
    @patch('ddwrt._make_request')
    def test_get_dhcp_leases_table_format(self, mock_request):
        """Test successful DHCP leases retrieval with HTML table format"""
        mock_request.return_value = '''
        <table>
        <tr><td>device1</td><td>AA:BB:CC:DD:EE:FF</td><td>192.168.1.10</td><td>expires</td></tr>
        <tr><td>device2</td><td>00:11:22:33:44:55</td><td>192.168.1.20</td><td>expires</td></tr>
        </table>
        '''
        
        result = ddwrt.get_dhcp_leases()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['hostname'], 'device1')
        self.assertEqual(result[0]['ip'], '192.168.1.10')
        self.assertEqual(result[0]['mac'], 'AA:BB:CC:DD:EE:FF')
    
    @patch('ddwrt._make_request')
    def test_get_dhcp_leases_failure(self, mock_request):
        """Test DHCP leases retrieval failure"""
        mock_request.side_effect = Exception("Connection error")
        
        result = ddwrt.get_dhcp_leases()
        
        # Should return empty list on error
        self.assertEqual(result, [])


class TestDDWRTARPTable(unittest.TestCase):
    def setUp(self):
        ddwrt.init('http://192.168.1.1', 'admin', 'test_password', False)
    
    @patch('ddwrt._make_request')
    def test_get_arp_table_success(self, mock_request):
        """Test successful ARP table retrieval"""
        mock_request.return_value = '''
        <table>
        <tr><td>192.168.1.10</td><td>AA:BB:CC:DD:EE:FF</td></tr>
        <tr><td>192.168.1.20</td><td>00:11:22:33:44:55</td></tr>
        </table>
        '''
        
        result = ddwrt.get_arp_table()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['ip'], '192.168.1.10')
        self.assertEqual(result[0]['mac'], 'AA:BB:CC:DD:EE:FF')


class TestDDWRTDiscoverDevices(unittest.TestCase):
    def setUp(self):
        ddwrt.init('http://192.168.1.1', 'admin', 'test_password', False)
    
    @patch('ddwrt.get_wireless_clients')
    @patch('ddwrt.get_arp_table')
    @patch('ddwrt.get_dhcp_leases')
    def test_discover_devices_from_dhcp_only(self, mock_dhcp, mock_arp, mock_wireless):
        """Test device discovery from DHCP leases only"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'laptop1'},
            {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55', 'hostname': 'server1'}
        ]
        mock_arp.return_value = []
        mock_wireless.return_value = []
        
        result = ddwrt.discover_devices()
        
        self.assertEqual(len(result), 2)
        macs = [d['mac'] for d in result]
        self.assertIn('AABBCCDDEEFF', macs)
        self.assertIn('001122334455', macs)
    
    @patch('ddwrt.get_wireless_clients')
    @patch('ddwrt.get_arp_table')
    @patch('ddwrt.get_dhcp_leases')
    def test_discover_devices_combined_sources(self, mock_dhcp, mock_arp, mock_wireless):
        """Test device discovery combining all sources"""
        mock_dhcp.return_value = [
            {'ip': '192.168.1.10', 'mac': 'AA:BB:CC:DD:EE:FF', 'hostname': 'laptop1'}
        ]
        mock_arp.return_value = [
            {'ip': '192.168.1.20', 'mac': '00:11:22:33:44:55'}
        ]
        mock_wireless.return_value = [
            {'mac': 'AA:BB:CC:DD:EE:FF'}  # Same as DHCP device
        ]
        
        result = ddwrt.discover_devices()
        
        # Should have 2 unique devices
        self.assertEqual(len(result), 2)
        
        # Device from DHCP should have hostname
        laptop = [d for d in result if d['mac'] == 'AABBCCDDEEFF'][0]
        self.assertEqual(laptop['hostname'], 'laptop1')
    
    @patch('ddwrt.get_wireless_clients')
    @patch('ddwrt.get_arp_table')
    @patch('ddwrt.get_dhcp_leases')
    def test_discover_devices_empty(self, mock_dhcp, mock_arp, mock_wireless):
        """Test device discovery with no devices"""
        mock_dhcp.return_value = []
        mock_arp.return_value = []
        mock_wireless.return_value = []
        
        result = ddwrt.discover_devices()
        
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
