from dedi_gateway.etc.enums import MessageType
from ..base_model import BaseModel
from .message_metadata import MessageMetadata


class NetworkMessage(BaseModel):
    """
    Base class for a Network Message
    """
    child_registry = {}
    message_type: MessageType | str = None

    def __init__(self,
                 metadata: MessageMetadata,
                 ):
        """
        Base class for a Network message
        :param metadata: The metadata for the message
        """
        self.metadata = metadata

    def to_dict(self) -> dict:
        """
        Convert the NetworkMessage to a dictionary.
        :return: A dictionary representation of the NetworkMessage
        """
        if self.message_type is None:
            message_type = None
        elif isinstance(self.message_type, MessageType):
            message_type = self.message_type.value
        elif isinstance(self.message_type, str):
            message_type = self.message_type
        else:
            raise TypeError(f"Invalid message_type: {self.message_type}")

        return {
            'messageType': message_type,
            'metadata': self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> 'NetworkMessage':
        """
        Create a NetworkMessage instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of NetworkMessage
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])

        return cls(
            metadata=metadata,
        )

    @classmethod
    def factory(cls, payload: dict):
        """
        Factory method to create a NetworkMessage instance from a dictionary.
        :param payload:
        :return:
        """
        message_type = payload.get('messageType', None)
        if message_type is None:
            return cls.from_dict(payload)

        try:
            message_type = MessageType(message_type)
            return cls.factory_from_id(
                payload=payload,
                id_var=message_type
            )
        except ValueError:
            from .custom_message import CustomMessage

            return CustomMessage.from_dict(payload)
