
from zambeze.campaign.activities.python import PythonActivity
from zambeze.orchestration.plugin_modules.python.python import Python
from zambeze.campaign.activities.abstract_activity import Activity

# Standard imports
import os
import pytest

import logging
import uuid

logger = logging.getLogger(__name__)


@pytest.mark.unit
def test_python_configuration():
    python_plugin = Python()



    assert True