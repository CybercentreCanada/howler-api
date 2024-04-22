import socket
import subprocess
import sys
from typing import Optional
import uuid
from ipaddress import IPv4Network, ip_address

import pr2modules.iproute as iproute

from howler.common.net_static import TLDS_ALPHA_BY_DOMAIN


def is_valid_port(value: int) -> bool:
    try:
        if 1 <= int(value) <= 65535:
            return True
    except ValueError:
        pass

    return False


def is_valid_domain(domain: str) -> bool:
    if "@" in domain:
        return False

    if "." in domain:
        tld = domain.split(".")[-1]
        return tld.upper() in TLDS_ALPHA_BY_DOMAIN

    return False


def is_valid_ip(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) == 4:
        for p in parts:
            try:
                if not (0 <= int(p) <= 255):
                    return False
            except ValueError:
                return False

        if int(parts[0]) == 0:
            return False

        if int(parts[3]) == 0:
            return False

        return True

    return False


def is_ip_in_network(ip: str, network: IPv4Network) -> bool:
    if not is_valid_ip(ip):
        return False

    return ip_address(ip) in network


def is_valid_email(email: str) -> bool:
    parts = email.split("@")
    if len(parts) == 2:
        if is_valid_domain(parts[1]):
            return True

    return False


def get_hostname() -> str:
    return socket.gethostname()


def get_mac_address() -> str:
    return "".join(["{0:02x}".format((uuid.getnode() >> i) & 0xFF) for i in range(0, 8 * 6, 8)][::-1]).upper()
