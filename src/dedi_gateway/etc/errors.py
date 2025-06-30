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
