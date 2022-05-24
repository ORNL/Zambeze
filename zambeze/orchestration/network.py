# Standard imports
import http.client as httplib

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