# Local imports
from zambeze.orchestration.services import Services

# Standard imports
import uuid

def test_registered_services():
    """Test simply checks that you can get a list of all the registered services"""
    services = Services()
    found_shell = False
    for service in services.registered():
        if  service == "shell":
            found_shell = True

    assert(found_shell)

def test_check_configured_services():

    services = Services()

    assert(len(services.configured) == 0)

    configuration = {
        "shell": {}
    }

    services.configure(configuration)

    assert(len(services.configured) > 0)