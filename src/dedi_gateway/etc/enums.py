from enum import Enum


BASE_PACKAGE = 'uk.co.firefox2100.ddg'


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


class AuthNotificationType(Enum):
    """
    Types of notifications related to authentication or authorisation
    """
    JOINING = 'joining'
    LEAVING = 'leaving'


class SyncRequestType(Enum):
    """
    What data is being requested from the sync target
    """
    INSTANCE = 'instance'
    DATA_INDEX = 'dataIndex'


class MessageType(Enum):
    """
    Types of messages passed in the network protocol
    """
    AUTH_REQUEST = BASE_PACKAGE + '.auth.request'
    AUTH_INVITE = BASE_PACKAGE + '.auth.invite'
    AUTH_REQUEST_RESPONSE = BASE_PACKAGE + '.auth.request.response'
    AUTH_INVITE_RESPONSE = BASE_PACKAGE + '.auth.invite.response'
    AUTH_CONNECT = BASE_PACKAGE + '.auth.connect'
    AUTH_NOTIFICATION = BASE_PACKAGE + '.auth.notification'
    SYNC_INDEX = BASE_PACKAGE + '.sync.index'
    SYNC_NODES = BASE_PACKAGE + '.sync.nodes'
    SYNC_REQUEST = BASE_PACKAGE + '.sync.request'
    ROUTE_REQUEST = BASE_PACKAGE + '.route.request'
    ROUTE_RESPONSE = BASE_PACKAGE + '.route.response'
    ROUTE_NOTIFICATION = BASE_PACKAGE + '.route.notification'
