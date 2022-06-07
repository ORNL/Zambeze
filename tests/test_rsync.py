# Local imports
import zambeze.orchestration.service_modules.rsync as rsync

# Standard imports
import copy
import os
import pwd
import pytest
import socket

@pytest.mark.unit
def test_rsync_requiredEndpointKeysExist():
    package = {
        "ip": "something",
        "user": "a user",
        "path": "a path to a file"
    }

    fields_exist = rsync.requiredEndpointKeysExist(package)
    assert fields_exist
    
    package2 = {
        "ip2": "something",
        "user": "a user",
        "path": "a path to a file"
    }
    
    fields_exist = rsync.requiredEndpointKeysExist(package2)
    assert fields_exist is False

    package3 = {
        "ip": "something",
        "user_s": "a user",
        "path": "a path to a file"
    }
    
    fields_exist = rsync.requiredEndpointKeysExist(package3)
    assert fields_exist is False

    package4 = {
        "ip": "something",
        "user": "a user",
        "pat": "a path to a file"
    }
    
    fields_exist = rsync.requiredEndpointKeysExist(package4)
    assert fields_exist is False

@pytest.mark.unit
def test_rsync_requiredSourceAndDestinationKeysExist():
    package = {
        "source": {
            "ip": "something",
            "user": "a user",
            "path": "a path to a file"
        },
        "destination": {
            "ip": "something",
            "user": "a user",
            "path": "a path to a file"
        }
    }

    fields_exist = rsync.requiredSourceAndDestinationKeysExist(package)
    assert fields_exist
 
    package = {
        "destination": {
            "ip": "something",
            "user": "a user",
            "path": "a path to a file"
        }
    }

    fields_exist = rsync.requiredSourceAndDestinationKeysExist(package)
    assert fields_exist is False
 
    package = {
        "source": {
            "ip": "something",
            "user": "a user",
            "path": "a path to a file"
        }
    }

    fields_exist = rsync.requiredSourceAndDestinationKeysExist(package)
    assert fields_exist is False
