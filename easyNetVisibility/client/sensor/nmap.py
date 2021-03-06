from datetime import datetime

import logging
import os
import xml.etree.ElementTree as ElementTree

import network_utils
import server_api

devices = {}
logger = logging.getLogger('EasyNetVisibility')


def ping_sweep():
    global devices

    logger.info('Beginning Ping Sweep')
    if not os.path.exists('/opt/easy_net_visibility/client/nmap_scans'):
        os.makedirs('/opt/easy_net_visibility/client/nmap_scans')
    ip = network_utils.get_ip()
    netmask = network_utils.get_netmask()

    os.popen("nmap -sn %s/%s -e %s -oX /opt/easy_net_visibility/client/nmap_scans/pingSweep.xml" % (
        ip, str(netmask), network_utils.get_interface())).read()
    result_file = '/opt/easy_net_visibility/client/nmap_scans/pingSweep.xml'
    try:
        tree = ElementTree.parse(result_file)
        root = tree.getroot()
        # Parse the nmap.xml file
        for host in root.findall("./host"):
            ip_address = ""
            mac_address = ""
            hostname = ""
            # host_state = ""
            mac_vendor = ""
            # for status in host.findall("./status"):
            #     host_state = status.get('state')
            #     host_state = host_state.rstrip()
            for ip in host.findall("./address"):
                address_type = ip.get('addrtype')
                if address_type == "mac":
                    mac_address = ip.get('addr')
                    mac_address = mac_address.rstrip()
                    mac_address = network_utils.convert_mac(mac_address)
                    mac_vendor = ip.get('vendor')
                    if mac_vendor is None:
                        mac_vendor = 'Unknown'
                    mac_vendor = mac_vendor.rstrip()
                if address_type == "ipv4":
                    ip_address = ip.get('addr')
                    ip_address = ip_address.rstrip()
            for hostname in host.findall("./hostnames/hostname"):
                hostname = hostname.get('name')
                hostname = hostname.rstrip()
            # If mac address is missing, it's the local interface
            if len(mac_address) > 0:
                if len(hostname) < 1:
                    hostname = "%s (%s)" % (ip_address, mac_address)

                logger.info('found device:' + str((hostname, str(ip_address), mac_address, mac_vendor)))
                devices[mac_address] = ip_address
                server_api.add_device(hostname, str(ip_address), mac_address, mac_vendor)
    except Exception as e:
        logger.error("Error with ping sweep XML file: " + str(e))
    os.system('rm ' + result_file)


def port_scan():
    logger.info("Beginning port scan")
    if not os.path.exists('/opt/easy_net_visibility/client/nmap_scans'):
        os.makedirs('/opt/easy_net_visibility/client/nmap_scans')

    for device_mac in devices:
        logger.info("Port scanning %s", devices[device_mac])
        result_file = "/opt/easy_net_visibility/client/nmap_scans/portScan_%s_%s.xml" % (
            datetime.now().strftime('%Y-%m-%d_%H-%M'), devices[device_mac])
        os.popen("nmap -sV -oX %s %s" % (result_file, devices[device_mac])).read()
        try:
            tree = ElementTree.parse(result_file)
            root = tree.getroot()
            # Parse the portScan.xml file
            for port in root.findall("./host/ports/port"):
                port_state = 'filtered'
                for state in port.findall("./state"):
                    port_state = state.get('state')
                if port_state == 'open':
                    port_num = str(port.get('portid'))
                    proto = port.get('protocol')
                    service_name = ''
                    service_product = ''
                    service_version = ''
                    for service in port.findall("./service"):
                        service_name = service.get('name')
                        service_product = service.get('product')
                        service_version = service.get('version')
                    port_info = {'mac': device_mac,
                                 'port': port_num,
                                 'protocol': proto,
                                 'name': service_name,
                                 'version': service_version,
                                 'product': service_product}
                    logger.info('found port: ' + str(port_info))
                    server_api.add_port(port_info)
        except Exception as e:
            logger.error("Error with port scan XML file: " + str(e))
        os.system('rm ' + result_file)
