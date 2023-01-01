# Standard imports
import http.client as httplib

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
