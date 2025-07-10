from .network_message import NetworkMessage
from .message_metadata import MessageMetadata


class CustomMessage(NetworkMessage):
    """
    A custom message serving as a container for application-specific data.
    """
    def __init__(self,
                 metadata: MessageMetadata,
                 message_type: str,
                 message_data: dict,
                 message_header: dict = None,
                 ):
        """
        A custom message serving as a container for application-specific data.
        :param metadata: The metadata for this message
        :param message_type: The type of the custom message, needs to be a string
            in the registered configuration types
        :param message_data: The data of the custom message, should be a dictionary;
            this will be sent as the payload of the message
        :param message_header: Optional header for the message, can be used to
            include tokens, cookies, etc. that are needed for a proxied request
        """
        super().__init__(
            metadata=metadata,
        )
        self.message_type = message_type
        self.message_data = message_data
        self.message_header = message_header

    def to_dict(self) -> dict:
        """
        Convert the CustomMessage to a dictionary.
        :return: A dictionary representation of the CustomMessage
        """
        payload = super().to_dict()
        payload.update({
            'messageType': self.message_type,
            'messageData': self.message_data,
        })
        if self.message_header:
            payload['messageHeader'] = self.message_header
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'CustomMessage':
        """
        Create a CustomMessage instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of CustomMessage
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])

        return cls(
            metadata=metadata,
            message_type=payload['messageType'],
            message_data=payload['messageData'],
            message_header=payload.get('messageHeader', None),
        )
