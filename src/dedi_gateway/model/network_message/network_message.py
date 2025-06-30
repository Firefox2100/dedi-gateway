from dedi_gateway.etc.enums import MessageType
from ..base_model import BaseModel
from .message_metadata import MessageMetadata


class NetworkMessage(BaseModel):
    """
    Base class for a Network Message
    """
    message_type: MessageType = None

    def __init__(self,
                 metadata: MessageMetadata,
                 ):
        self.metadata = metadata

    def to_dict(self) -> dict:
        """
        Convert the NetworkMessage to a dictionary.
        :return: A dictionary representation of the NetworkMessage
        """
        return {
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
