# Standard imports
from pathlib import Path
from typing import Optional

import logging
import os
import pkgutil


def registerPlugins(logger: Optional[logging.Logger] = None) -> list:
    """Will register all the plugins provided in the plugin_modules folder

    :return: the names of all the plugins
    :rtype: a list of strings
    """

    module_names = []
    # plugin_path = [str(Path(__file__).resolve().parent) + "/plugin_modules"]
    plugin_path = [str(Path(__file__).resolve().parent)]
    print(plugin_path)
    for importer, module_name, ispkg in pkgutil.walk_packages(plugin_path):
        if (
            module_name != "abstract_plugin"
            and module_name != "__init__"
            and module_name != "abstract_plugin_message_validator"
            and module_name != "common_dataclasses"
            and module_name != "common_plugin_functions"
            and module_name != "abstract_plugin_template_generator"
            and module_name != "abstract_uri_separator"
            and module_name != "file_uri_separator"
        ):
            module_path = module_name.replace(".", os.path.sep)
            full_module_path = os.path.join(plugin_path[0], module_path)
            # Make sure we are only grabbing zambeze plugins and not modules
            # from elsewhere in the Python path
            if os.path.isdir(full_module_path):
                module_names.append(module_name)
    if logger:
        logger.debug(f"Registered Plugins: {', '.join(module_names)}")
    return module_names
