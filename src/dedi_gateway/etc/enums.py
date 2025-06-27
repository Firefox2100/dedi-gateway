from enum import Enum


class UserMappingType(Enum):
    """
    User mapping types
    """
    NO_MAPPING = 'noMapping'
    STATIC = 'static'
    DYNAMIC = 'dynamic'
