# Standard python imports
import re
from uuid import UUID


def valid_uuid(uuid_to_test: str, version=None) -> bool:
    """Check if uuid_to_test is a valid UUID.

    :param uuid_to_test: The 36 character UUID
    :type uuid_to_test: string
    :param version: version of the uuid to use
    :type version: integer

    Example Arguments

    uuid_to_test : str
    version : {1, 2, 3, 4}

    Examples
    --------
    >>> valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> valid_uuid('c9bf9e58')
    False

    Function was taken from
    https://stackoverflow.com/questions/19989481/how-to-determine-if-a-string-
    is-a-valid-v4-uuid
    """
    if not isinstance(uuid_to_test, str):
        raise Exception("UUID must be of type str")

    uuid_obj = ""
    try:
        if version:
            uuid_obj = UUID(uuid_to_test, version=version)
        else:
            uuid_obj = UUID(uuid_to_test)
    except ValueError:
        return False
    return str(uuid_obj).lower() == str(uuid_to_test).lower()


def valid_email(email: str) -> bool:
    regexp = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    if re.match(regexp, email):
        return True
    else:
        return False
