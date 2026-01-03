import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import tempfile
import xml.etree.ElementTree as ET

# Add the sensor directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sensor'))

import nmap


class TestPingSweep(unittest.TestCase):
    def setUp(self):
        nmap._found_devices = {}

    @patch('os.system')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.popen')
    @patch('network_utils.get_ip')
    @patch('network_utils.get_netmask')
    @patch('network_utils.get_interface')
    @patch('xml.etree.ElementTree.parse')
    def test_ping_sweep_success(self, mock_parse, mock_interface, mock_netmask, 
                                mock_ip, mock_popen, mock_makedirs, mock_exists, mock_system):
        # Setup mocks
        mock_ip.return_value = '192.168.1.100'
        mock_netmask.return_value = 24
        mock_interface.return_value = 'eth0'
        mock_exists.return_value = True
        mock_popen.return_value.read.return_value = ''
        
        # Create mock XML structure
        xml_content = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.1" addrtype="ipv4"/>
                <address addr="AA:BB:CC:DD:EE:FF" addrtype="mac" vendor="TestVendor"/>
                <hostnames>
                    <hostname name="router.local"/>
                </hostnames>
            </host>
            <host>
                <status state="up"/>
                <address addr="192.168.1.2" addrtype="ipv4"/>
                <address addr="00:11:22:33:44:55" addrtype="mac" vendor="AnotherVendor"/>
                <hostnames/>
            </host>
        </nmaprun>
        """
        
        root = ET.fromstring(xml_content)
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = root
        mock_parse.return_value = mock_tree
        
        # Execute
        result = nmap.ping_sweep()
        
        # Verify
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['mac'], 'AABBCCDDEEFF')
        self.assertEqual(result[0]['ip'], '192.168.1.1')
        self.assertEqual(result[0]['hostname'], 'router.local')
        self.assertEqual(result[0]['vendor'], 'TestVendor')
        
        self.assertEqual(result[1]['mac'], '001122334455')
        self.assertEqual(result[1]['ip'], '192.168.1.2')
        # When no hostname, it should be IP (MAC)
        self.assertIn('192.168.1.2', result[1]['hostname'])
        self.assertIn('001122334455', result[1]['hostname'])
        
        # Check that found_devices was populated
        self.assertEqual(len(nmap._found_devices), 2)
        self.assertEqual(nmap._found_devices['AABBCCDDEEFF'], '192.168.1.1')

    @patch('os.system')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.popen')
    @patch('network_utils.get_ip')
    @patch('network_utils.get_netmask')
    @patch('network_utils.get_interface')
    @patch('xml.etree.ElementTree.parse')
    def test_ping_sweep_no_mac(self, mock_parse, mock_interface, mock_netmask, 
                               mock_ip, mock_popen, mock_makedirs, mock_exists, mock_system):
        """Test that devices without MAC (local interface) are skipped"""
        mock_ip.return_value = '192.168.1.100'
        mock_netmask.return_value = 24
        mock_interface.return_value = 'eth0'
        mock_exists.return_value = True
        mock_popen.return_value.read.return_value = ''
        
        # Device without MAC address
        xml_content = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.100" addrtype="ipv4"/>
                <hostnames>
                    <hostname name="local.host"/>
                </hostnames>
            </host>
        </nmaprun>
        """
        
        root = ET.fromstring(xml_content)
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = root
        mock_parse.return_value = mock_tree
        
        result = nmap.ping_sweep()
        
        # Should be empty since device has no MAC
        self.assertEqual(len(result), 0)

    @patch('os.system')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.popen')
    @patch('network_utils.get_ip')
    @patch('network_utils.get_netmask')
    @patch('network_utils.get_interface')
    @patch('xml.etree.ElementTree.parse')
    def test_ping_sweep_no_vendor(self, mock_parse, mock_interface, mock_netmask, 
                                  mock_ip, mock_popen, mock_makedirs, mock_exists, mock_system):
        """Test handling of devices with no vendor information"""
        mock_ip.return_value = '192.168.1.100'
        mock_netmask.return_value = 24
        mock_interface.return_value = 'eth0'
        mock_exists.return_value = True
        mock_popen.return_value.read.return_value = ''
        
        xml_content = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <status state="up"/>
                <address addr="192.168.1.1" addrtype="ipv4"/>
                <address addr="AA:BB:CC:DD:EE:FF" addrtype="mac"/>
                <hostnames>
                    <hostname name="device.local"/>
                </hostnames>
            </host>
        </nmaprun>
        """
        
        root = ET.fromstring(xml_content)
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = root
        mock_parse.return_value = mock_tree
        
        result = nmap.ping_sweep()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['vendor'], 'Unknown')

    @patch('os.system')
    @patch('os.path.exists')
    @patch('os.popen')
    @patch('network_utils.get_ip')
    @patch('network_utils.get_netmask')
    @patch('network_utils.get_interface')
    @patch('xml.etree.ElementTree.parse')
    def test_ping_sweep_creates_directory(self, mock_parse, mock_interface, mock_netmask, 
                                         mock_ip, mock_popen, mock_exists, mock_system):
        """Test that directory is created if it doesn't exist"""
        mock_ip.return_value = '192.168.1.100'
        mock_netmask.return_value = 24
        mock_interface.return_value = 'eth0'
        mock_exists.return_value = False
        mock_popen.return_value.read.return_value = ''
        
        mock_parse.side_effect = Exception("File not found")
        
        with patch('os.makedirs') as mock_makedirs:
            try:
                nmap.ping_sweep()
            except:
                pass
            
            mock_makedirs.assert_called_once_with('/opt/easy_net_visibility/client/nmap_scans')


class TestPortScan(unittest.TestCase):
    def setUp(self):
        nmap._found_devices = {
            'AABBCCDDEEFF': '192.168.1.1'
        }

    @patch('os.system')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.popen')
    @patch('xml.etree.ElementTree.parse')
    def test_port_scan_success(self, mock_parse, mock_popen, mock_makedirs, 
                               mock_exists, mock_system):
        mock_exists.return_value = True
        mock_popen.return_value.read.return_value = ''
        
        xml_content = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <ports>
                    <port protocol="tcp" portid="80">
                        <state state="open"/>
                        <service name="http" product="nginx" version="1.18.0"/>
                    </port>
                    <port protocol="tcp" portid="443">
                        <state state="open"/>
                        <service name="https" product="nginx" version="1.18.0"/>
                    </port>
                    <port protocol="tcp" portid="22">
                        <state state="filtered"/>
                        <service name="ssh"/>
                    </port>
                </ports>
            </host>
        </nmaprun>
        """
        
        root = ET.fromstring(xml_content)
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = root
        mock_parse.return_value = mock_tree
        
        result = list(nmap.port_scan())
        
        # Should yield one list of ports for the one device
        self.assertEqual(len(result), 1)
        ports = result[0]
        
        # Should have 2 open ports (filtered port should be excluded)
        self.assertEqual(len(ports), 2)
        
        # Check first port
        self.assertEqual(ports[0]['port'], '80')
        self.assertEqual(ports[0]['protocol'], 'tcp')
        self.assertEqual(ports[0]['name'], 'http')
        self.assertEqual(ports[0]['product'], 'nginx')
        self.assertEqual(ports[0]['version'], '1.18.0')
        self.assertEqual(ports[0]['mac'], 'AABBCCDDEEFF')

    @patch('os.system')
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.popen')
    @patch('xml.etree.ElementTree.parse')
    def test_port_scan_no_open_ports(self, mock_parse, mock_popen, mock_makedirs, 
                                    mock_exists, mock_system):
        """Test device with no open ports"""
        mock_exists.return_value = True
        mock_popen.return_value.read.return_value = ''
        
        xml_content = """<?xml version="1.0"?>
        <nmaprun>
            <host>
                <ports>
                    <port protocol="tcp" portid="22">
                        <state state="filtered"/>
                        <service name="ssh"/>
                    </port>
                </ports>
            </host>
        </nmaprun>
        """
        
        root = ET.fromstring(xml_content)
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = root
        mock_parse.return_value = mock_tree
        
        result = list(nmap.port_scan())
        
        # Should still yield but with empty list
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]), 0)

    @patch('os.system')
    @patch('os.path.exists')
    @patch('os.popen')
    @patch('xml.etree.ElementTree.parse')
    def test_port_scan_creates_directory(self, mock_parse, mock_popen, mock_exists, mock_system):
        """Test that directory is created if it doesn't exist"""
        mock_exists.return_value = False
        mock_popen.return_value.read.return_value = ''
        
        mock_parse.side_effect = Exception("File not found")
        
        with patch('os.makedirs') as mock_makedirs:
            try:
                list(nmap.port_scan())
            except:
                pass
            
            mock_makedirs.assert_called_once_with('/opt/easy_net_visibility/client/nmap_scans')

    def test_port_scan_empty_devices(self):
        """Test port scan when no devices found"""
        nmap._found_devices = {}
        
        result = list(nmap.port_scan())
        
        # Should yield nothing
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
