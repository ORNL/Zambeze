# Standard python imports
from uuid import UUID

def validUUID(uuid_to_test: str, version=4) -> bool:
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
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False

    Function was taken from https://stackoverflow.com/questions/19989481/how-to-determine-if-a-string-is-a-valid-v4-uuid
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test