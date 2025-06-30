from dedi_gateway.etc.enums import MessageType
from ..message_metadata import MessageMetadata
from ..network_message import NetworkMessage


@NetworkMessage.register_child(MessageType.AUTH_REQUEST)
class AuthRequest(NetworkMessage):
    """
    A message to request joining a network.
    """
    message_type: MessageType = MessageType.AUTH_REQUEST

    def __init__(self,
                 metadata: MessageMetadata,
                 ):
        super().__init__(
            metadata=metadata,
        )
