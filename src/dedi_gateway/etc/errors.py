"""
Exception definitions for dedi-gateway package
"""


class DediGatewayException(Exception):
    """
    Base class for all exceptions raised by the service.
    """

    def __init__(self,
                 message: str = None,
                 status_code: int = 500,
                 ):
        super().__init__(message)

        self.message = message
        self.status_code = status_code


class ConfigurationParsingException(DediGatewayException):
    """
    Exception raised when there is an error parsing the configuration.
    """
    def __init__(self,
                 message: str = 'Error parsing configuration.',
                 status_code: int = 400,
                 ):
        super().__init__(message, status_code)


class MessageBrokerTimeoutException(DediGatewayException):
    """
    Message broker timeout without receiving a message.
    """
    def __init__(self,
                 message: str = 'Message broker timeout without receiving a message.',
                 status_code: int = 504,
                 ):
        super().__init__(message, status_code)


class KmsKeyManagementException(DediGatewayException):
    """
    Exception raised when there is an error with KMS key management.
    """
    def __init__(self,
                 message: str = 'Error managing KMS keys.',
                 status_code: int = 500,
                 ):
        super().__init__(message, status_code)


class NetworkRequestFailedException(DediGatewayException):
    """
    Exception raised when a network request fails.
    """
    def __init__(self,
                 message: str = 'Network request failed.',
                 status_code: int = 502,
                 ):
        super().__init__(message, status_code)


class JoiningNetworkException(DediGatewayException):
    """
    Exception raised when joining a network fails.
    """
    def __init__(self,
                 message: str = 'Failed to join the network.',
                 status_code: int = 503,
                 ):
        super().__init__(message, status_code)


class InvitingNodeException(DediGatewayException):
    """
    Exception raised when inviting a node to a network fails.
    """
    def __init__(self,
                 message: str = 'Failed to invite the node to the network.',
                 status_code: int = 503,
                 ):
        super().__init__(message, status_code)


class NetworkNotFoundException(DediGatewayException):
    """
    Exception raised when a network is not found.
    """
    def __init__(self,
                 message: str = 'Network not found.',
                 status_code: int = 404,
                 ):
        super().__init__(message, status_code)


class NodeNotFoundException(DediGatewayException):
    """
    Exception raised when a node is not found.
    """
    def __init__(self,
                 message: str = 'Node not found.',
                 status_code: int = 404,
                 ):
        super().__init__(message, status_code)


class NodeNotApprovedException(DediGatewayException):
    """
    Exception raised when a node is not approved to join a network.
    """
    def __init__(self,
                 message: str = 'Node not approved to communicate with this service.',
                 status_code: int = 403,
                 ):
        super().__init__(message, status_code)


class NodeNotConnectedException(DediGatewayException):
    """
    Exception raised when a node is not connected to the network.
    """
    def __init__(self,
                 message: str = 'Node is not connected to the network.',
                 status_code: int = 503,
                 ):
        super().__init__(message, status_code)


class NetworkMessageNotFoundException(DediGatewayException):
    """
    Exception raised when a network message is not found.
    """
    def __init__(self,
                 message: str = 'Network message not found.',
                 status_code: int = 404,
                 ):
        super().__init__(message, status_code)


class NetworkMessageSignatureException(DediGatewayException):
    """
    Exception raised when a network message signature is invalid.
    """
    def __init__(self,
                 message: str = 'Network message signature is invalid.',
                 status_code: int = 400,
                 ):
        super().__init__(message, status_code)


class MessageConfigurationNotFoundException(DediGatewayException):
    """
    Exception raised when a message configuration is not found.
    """
    def __init__(self,
                 message: str = 'Message configuration not found.',
                 status_code: int = 404,
                 ):
        super().__init__(message, status_code)


class MessageConfigurationParsingException(DediGatewayException):
    """
    Exception raised when there is an error parsing a message configuration.
    """
    def __init__(self,
                 message: str = 'Error parsing message configuration.',
                 status_code: int = 400,
                 ):
        super().__init__(message, status_code)
