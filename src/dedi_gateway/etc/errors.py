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
