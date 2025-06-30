from enum import Enum


class ConnectivityType(Enum):
    """
    Connectivity types
    """
    OFFLINE = 'offline'
    DIRECT = 'direct'
    PROXY = 'proxy'


class TransportType(Enum):
    """
    Transport types
    """
    SSE = 'sse'
    WEBSOCKET = 'websocket'


class UserMappingType(Enum):
    """
    User mapping types
    """
    NO_MAPPING = 'noMapping'
    STATIC = 'static'
    DYNAMIC = 'dynamic'


class MessageType(Enum):
    """
    Types of messages passed in the network protocol
    """
    AUTH_REQUEST = 'authRequest'
