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
    AUTH_REQUEST = 'uk.co.firefox2100.ddg.auth.request'
    AUTH_INVITE = 'uk.co.firefox2100.ddg.auth.invite'
    AUTH_REQUEST_RESPONSE = 'uk.co.firefox2100.ddg.auth.request.response'
    AUTH_INVITE_RESPONSE = 'uk.co.firefox2100.ddg.auth.invite.response'
    AUTH_CONNECT = 'uk.co.firefox2100.ddg.auth.connect'
