
from shutil import which

def isExecutable(name: str) -> bool:
    """Check whether an executable is findable is on PATH and marked as executable.
    
    :param name: name of the executable as called from the shell or os
    :type name: str
    :return: whether the exectuable exists on the path and can be exectued
    :rtype: bool
    """
    return which(name) is not None