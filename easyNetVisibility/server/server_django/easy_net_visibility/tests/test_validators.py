import unittest
from easy_net_visibility_server import validators


class TestMacAddressValidator(unittest.TestCase):
    def test_valid_mac_colon_format(self):
        self.assertTrue(validators.mac_address('AA:BB:CC:DD:EE:FF'))
        self.assertTrue(validators.mac_address('00:11:22:33:44:55'))
        self.assertTrue(validators.mac_address('aA:bB:cC:dD:eE:fF'))

    def test_valid_mac_dash_format(self):
        self.assertTrue(validators.mac_address('AA-BB-CC-DD-EE-FF'))
        self.assertTrue(validators.mac_address('00-11-22-33-44-55'))
        self.assertTrue(validators.mac_address('aA-bB-cC-dD-eE-fF'))

    def test_valid_mac_alpha_format(self):
        self.assertTrue(validators.mac_address('AABBCCDDEEFF'))
        self.assertTrue(validators.mac_address('001122334455'))
        self.assertTrue(validators.mac_address('aAbBcCdDeEfF'))

    def test_invalid_mac_wrong_length(self):
        self.assertFalse(validators.mac_address('AA:BB:CC:DD:EE'))
        self.assertFalse(validators.mac_address('AA:BB:CC:DD:EE:FF:00'))
        self.assertFalse(validators.mac_address('AABBCCDDEE'))

    def test_invalid_mac_wrong_characters(self):
        self.assertFalse(validators.mac_address('ZZ:BB:CC:DD:EE:FF'))
        self.assertFalse(validators.mac_address('AA:BB:CC:DD:EE:GG'))
        self.assertFalse(validators.mac_address('AABBCCDDEEZZ'))

    def test_invalid_mac_mixed_separators(self):
        self.assertFalse(validators.mac_address('AA:BB-CC:DD:EE:FF'))
        self.assertFalse(validators.mac_address('AA-BB:CC-DD-EE-FF'))

    def test_invalid_mac_empty(self):
        self.assertFalse(validators.mac_address(''))


class TestConvertMac(unittest.TestCase):
    def test_convert_colon_format(self):
        self.assertEqual(validators.convert_mac('aa:bb:cc:dd:ee:ff'), 'AABBCCDDEEFF')
        self.assertEqual(validators.convert_mac('AA:BB:CC:DD:EE:FF'), 'AABBCCDDEEFF')

    def test_convert_dash_format(self):
        self.assertEqual(validators.convert_mac('aa-bb-cc-dd-ee-ff'), 'AABBCCDDEEFF')
        self.assertEqual(validators.convert_mac('AA-BB-CC-DD-EE-FF'), 'AABBCCDDEEFF')

    def test_convert_already_normalized(self):
        self.assertEqual(validators.convert_mac('AABBCCDDEEFF'), 'AABBCCDDEEFF')
        self.assertEqual(validators.convert_mac('aabbccddeeff'), 'AABBCCDDEEFF')

    def test_convert_mixed_case(self):
        self.assertEqual(validators.convert_mac('aA:bB:cC:dD:eE:fF'), 'AABBCCDDEEFF')
        self.assertEqual(validators.convert_mac('aA-bB-cC-dD-eE-fF'), 'AABBCCDDEEFF')


class TestIpAddressValidator(unittest.TestCase):
    def test_valid_ip_addresses(self):
        self.assertTrue(validators.ip_address('192.168.1.1'))
        self.assertTrue(validators.ip_address('10.0.0.1'))
        self.assertTrue(validators.ip_address('172.16.0.1'))
        self.assertTrue(validators.ip_address('0.0.0.0'))
        self.assertTrue(validators.ip_address('255.255.255.255'))
        self.assertTrue(validators.ip_address('8.8.8.8'))

    def test_invalid_ip_out_of_range(self):
        self.assertFalse(validators.ip_address('256.1.1.1'))
        self.assertFalse(validators.ip_address('1.256.1.1'))
        self.assertFalse(validators.ip_address('1.1.256.1'))
        self.assertFalse(validators.ip_address('1.1.1.256'))
        self.assertFalse(validators.ip_address('999.999.999.999'))

    def test_invalid_ip_wrong_format(self):
        self.assertFalse(validators.ip_address('192.168.1'))
        self.assertFalse(validators.ip_address('192.168.1.1.1'))
        self.assertFalse(validators.ip_address('192.168..1'))
        self.assertFalse(validators.ip_address('192,168,1,1'))

    def test_invalid_ip_with_letters(self):
        self.assertFalse(validators.ip_address('192.168.1.a'))
        self.assertFalse(validators.ip_address('abc.def.ghi.jkl'))

    def test_invalid_ip_empty(self):
        self.assertFalse(validators.ip_address(''))


class TestHostnameValidator(unittest.TestCase):
    def test_valid_hostnames(self):
        self.assertTrue(validators.hostname('example.com'))
        self.assertTrue(validators.hostname('sub.example.com'))
        self.assertTrue(validators.hostname('my-host'))
        self.assertTrue(validators.hostname('host123'))
        # Note: underscores are not valid in RFC 952/1123 hostnames, but are
        # intentionally allowed here for internal naming compatibility.
        self.assertTrue(validators.hostname('test_host'))
        self.assertTrue(validators.hostname('192-168-1-1'))

    def test_valid_no_hostname_format(self):
        # Format: IP (MAC) - when hostname is not available
        self.assertTrue(validators.hostname('192.168.1.1 (AABBCCDDEEFF)'))
        self.assertTrue(validators.hostname('10.0.0.1 (001122334455)'))

    def test_invalid_hostname_special_chars(self):
        self.assertFalse(validators.hostname('!!!invalid!!!'))
        self.assertFalse(validators.hostname('host@name'))
        self.assertFalse(validators.hostname('host#name'))

    def test_invalid_hostname_starts_with_hyphen(self):
        self.assertFalse(validators.hostname('-hostname'))

    def test_invalid_hostname_ends_with_hyphen(self):
        self.assertFalse(validators.hostname('hostname-'))

    def test_invalid_hostname_empty(self):
        self.assertFalse(validators.hostname(''))


class TestUrlValidator(unittest.TestCase):
    def test_valid_urls(self):
        self.assertTrue(validators.url('example.com'))
        self.assertTrue(validators.url('www.example.com'))
        self.assertTrue(validators.url('sub.example.com'))
        self.assertTrue(validators.url('api.example.com'))

    def test_valid_ip_as_url(self):
        self.assertTrue(validators.url('192.168.1.1'))
        self.assertTrue(validators.url('10.0.0.1'))
        self.assertTrue(validators.url('8.8.8.8'))

    def test_invalid_url_special_chars(self):
        self.assertFalse(validators.url('example@com'))
        self.assertFalse(validators.url('example#com'))

    def test_invalid_url_starts_with_hyphen(self):
        self.assertFalse(validators.url('-example.com'))

    def test_invalid_url_ends_with_hyphen(self):
        self.assertFalse(validators.url('example.com-'))

    def test_invalid_url_empty(self):
        self.assertFalse(validators.url(''))

    def test_invalid_url_single_char(self):
        self.assertFalse(validators.url('a'))

    def test_valid_url_minimal(self):
        """Test minimal valid URL format (3+ chars per segment)"""
        self.assertTrue(validators.url('aaa.bbb'))
