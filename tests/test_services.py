# Local imports
from zambeze.orchestration.services import Services

# Standard imports
import uuid


def test_registered_services():
    """Test simply checks that you can get a list of all the registered services"""
    services = Services()
    found_shell = False
    found_rsync = False
    for service in services.registered:
        if service == "shell":
            found_shell = True
        elif service == "rsync":
            found_rsync = True

    assert found_shell
    assert found_rsync


def test_check_configured_services():

    services = Services()

    assert len(services.configured) == 0

    configuration = {"shell": {}}

    services.configure(configuration)

    assert len(services.configured) > 0
