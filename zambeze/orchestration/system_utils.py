from shutil import which
import pwd

def isExecutable(name: str) -> bool:
    """Check whether an executable is findable is on PATH and marked as executable.

    :param name: name of the executable as called from the shell or os
    :type name: str
    :return: whether the exectuable exists on the path and can be exectued
    :rtype: bool
    """
    return which(name) is not None

def userExists(username: str) -> bool:
    """Check whether a user exists on the host.

    :param username: the username to check
    :type username: string
    :return: True if the user is found and false otherwise
    :rtype: bool
    """
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False