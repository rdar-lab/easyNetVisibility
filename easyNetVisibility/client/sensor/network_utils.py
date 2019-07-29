import fcntl
import logging
import re
import socket
import struct
from scapy.all import get_if_hwaddr

logger = logging.getLogger('EasyNetVisibility')
interface = None
detected_mac = None
detected_hostname = None


def init(param_interface):
    global interface
    interface = param_interface


def get_interface():
    return interface


def get_system_dfgw():
    with open("/proc/net/route") as route_file:
        for line in route_file:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue
            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', interface[:15]))[20:24])


def get_netmask():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    netmask = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x891b, struct.pack('256s', interface))[20:24])
    netmask = sum([bin(int(x)).count('1') for x in netmask.split('.')])
    return netmask


def convert_mac(macAddress):
    if re.match(r"^[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}$",
                macAddress):
        macAddress = macAddress.replace('-', '')
    elif re.match(r"^[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}$",
                  macAddress):
        macAddress = macAddress.replace(':', '')
    return macAddress.upper()


def get_mac():
    global detected_mac

    if detected_mac is not None:
        return detected_mac

    logger.info("Detecting machine MAC based on interface " + interface)
    mac = get_if_hwaddr(interface)
    if mac != "00:00:00:00:00:00":
        detected_mac = mac
        logger.info("Detected machine MAC address:" + detected_mac)
        return detected_mac
    else:
        logger.info("Failure detecting the MAC address")


def get_hostname():
    global detected_hostname

    if detected_hostname is not None:
        return detected_hostname

    detected_hostname = socket.gethostname()
    logger.info("Detected machine hostname:" + detected_hostname)
    return detected_hostname
