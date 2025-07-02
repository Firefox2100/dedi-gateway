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


class AuthMessageStatus(Enum):
    """
    Status of an auth message
    """
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'


class MessageType(Enum):
    """
    Types of messages passed in the network protocol
    """
    AUTH_REQUEST = 'authRequest'
    AUTH_INVITE = 'authInvite'
