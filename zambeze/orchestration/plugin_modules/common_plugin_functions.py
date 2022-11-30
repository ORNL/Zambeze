# Standard imports
from pathlib import Path

import pkgutil


def registerPlugins(logger) -> None:
    """Will register all the plugins provided in the plugin_modules folder

    :return: the names of all the plugins
    :rtype: a list of strings
    """

    module_names = []
    #plugin_path = [str(Path(__file__).resolve().parent) + "/plugin_modules"]
    plugin_path = [str(Path(__file__).resolve().parent)]
    for importer, module_name, ispkg in pkgutil.walk_packages(path=plugin_path):
        if (
            module_name != "abstract_plugin"
            and module_name != "__init__"
            and module_name != "abstract_plugin_message_helper"
            and module_name != "common_dataclasses"
            and module_name != "common_plugin_functions"
        ):
            module_names.append(module_name)
    logger.debug(f"Registered Plugins: {', '.join(module_names)}")
    return module_names


