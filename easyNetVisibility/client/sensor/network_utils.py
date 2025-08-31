import fcntl
import logging
import re
import socket
import struct
from scapy.all import get_if_hwaddr

_logger = logging.getLogger('EasyNetVisibility')
_interface = None
_detected_mac = None
_detected_hostname = None


def init(param_interface):
    global _interface
    _interface = param_interface


def get_interface():
    return _interface


def get_system_dfgw():
    with open("/proc/net/route") as route_file:
        for line in route_file:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue
            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))


def get_ip():
    if _interface is None:
        _logger.warning("Interface is not set. Cannot get IP address.")
        return None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', _interface[:15].encode('utf-8')))[20:24])


def get_netmask():
    if _interface is None:
        _logger.warning("Interface is not set. Cannot get netmask.")
        return None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    netmask = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x891b, struct.pack('256s', _interface[:15].encode('utf-8')))[20:24])
    netmask_bits = sum([bin(int(x)).count('1') for x in netmask.split('.')])
    return netmask_bits


def convert_mac(macAddress):
    if re.match(r"^[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}$",
                macAddress):
        macAddress = macAddress.replace('-', '')
    elif re.match(r"^[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}$",
                  macAddress):
        macAddress = macAddress.replace(':', '')
    return macAddress.upper()


def get_mac():
    global _detected_mac

    if _detected_mac is not None:
        return _detected_mac

    if _interface is None:
        _logger.warning("Interface is not set. Cannot detect MAC address.")
        return None

    _logger.info("Detecting machine MAC based on interface " + _interface)
    mac = get_if_hwaddr(_interface)
    if mac != "00:00:00:00:00:00":
        _detected_mac = mac
        _logger.info("Detected machine MAC address:" + _detected_mac)
        return _detected_mac
    else:
        _logger.info("Failure detecting the MAC address")
        return None


def get_hostname():
    global _detected_hostname

    if _detected_hostname is not None:
        return _detected_hostname

    _detected_hostname = socket.gethostname()
    _logger.info("Detected machine hostname:" + _detected_hostname)
    return _detected_hostname
