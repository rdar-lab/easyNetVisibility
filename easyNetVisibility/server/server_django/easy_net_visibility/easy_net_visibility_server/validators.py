import re


def convert_mac(mac_address):
    if re.match(r"^[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}-[A-za-z0-9]{2}$",
                mac_address):
        mac_address = mac_address.replace('-', '')
    elif re.match(r"^[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}:[A-za-z0-9]{2}$",
                  mac_address):
        mac_address = mac_address.replace(':', '')
    return mac_address.upper()


def mac_address(mac_address):
    dash_match = re.match(
        r"^[A-Fa-f0-9]{2}-[A-Fa-f0-9]{2}-[A-Fa-f0-9]{2}-[A-Fa-f0-9]{2}-[A-Fa-f0-9]{2}-[A-Fa-f0-9]{2}$",
        mac_address)
    colon_match = re.match(
        r"^[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}:[A-Fa-f0-9]{2}$", mac_address)
    alpha_match = re.match(r"^[A-Fa-f0-9]{12}$", mac_address)
    if dash_match or colon_match or alpha_match:
        return True
    else:
        return False


def url(url):
    url_match = re.match(
        r"^([a-zA-Z0-9][a-zA-Z0-9\-\_]+[a-zA-Z0-9]\.)+([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-\_])+[A-Za-z0-9]$", url)
    ip_match = re.match(
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$",
        url)
    if url_match or ip_match:
        return True
    else:
        return False


def hostname(hostname):
    hostname_match = re.match(
        r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-\_]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-\_]*[A-Za-z0-9])$",
        hostname)
    no_hostname_match = re.match(r"^(\d+\.\d+\.\d+\.\d+\s\(\w{12}\))", hostname)
    if hostname_match or no_hostname_match:
        return True
    else:
        return False


def ip_address(ip_address):
    ip_match = re.match(
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$",
        ip_address)
    if ip_match:
        return True
    else:
        return False
