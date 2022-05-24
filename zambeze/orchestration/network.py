import http.client as httplib

def externalNetworkConnectionDetected():
    """Check if we can connect to external network. 8.8.8.8 is the 
    Google namespace server."""
    connection = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        connection.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        connection.close()