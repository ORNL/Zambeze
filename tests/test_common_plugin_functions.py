# Local imports
from zambeze.orchestration.plugin_modules.common_plugin_functions import registerPlugins
from zambeze.log_manager import LogManager

# Standard imports
import logging
import pytest

logger = LogManager(logging.DEBUG, "commput_plugin_functions")

@pytest.mark.unit
def test_registerPlugins():
    plugins = registerPlugins(logger)
    assert len(plugins) > 0

    for plugin in plugins:
        # Lets make sure we don't import system plugins i.e. git.cmd we will
        # do this by assuming we should only be importing plugins that are flat
        # and are not nested 'git' is valid 'git.something' is not
        assert "." not in plugin
