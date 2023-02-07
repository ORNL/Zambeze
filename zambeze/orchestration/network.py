# Standard imports
import http.client as httplib
import re
import socket

import ipaddress


def externalNetworkConnectionDetected() -> bool:
    """Check if we can connect to external network.

    :returns: True if can connect to google server, false otherwise
    :rtype: bool
    Using the ip address 8.8.8.8 which is the Google namespace server.
    """
    connection = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        connection.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        connection.close()


def isAddressValid(address: str, version: str = "IPv4") -> bool:
    if version == "IPv4":
        try:
            ipaddress.ip_address(address)
            return True
        except ValueError:
            print("address/netmask is invalid: %s" % address)
            return False
        except Exception:
            print("Usage : %s  ip" % address)
            return False
    else:
        raise Exception(f"Unsupported IP version {version}")


def getIP(address_or_hostname: str):
    """ Check if this is an ip address

    if not check to see if we can resolve to an IP address by assuming it is a hostname

    :Example

    >>> ip = getIP("zambeze1")

    :Example

    Or does nothing if already an ip

    >>> ip = getIP("127.0.0.1")
    """
    if re.search("[a-zA-Z]", address_or_hostname):
        # assuming that because it contains characters it is a hostname
        try:
            neighbor_vm_ip = socket.gethostbyname(address_or_hostname)
        except Exception as e:
            print(e)
            raise Exception(
                f"Unable resolze {address_or_hostname} to an IP" " Address"
            )
    else:
        neighbor_vm_ip = address_or_hostname
    return neighbor_vm_ip

