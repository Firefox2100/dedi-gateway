from dedi_gateway.etc.enums import MessageType, SyncRequestType
from ..network_message import NetworkMessage, MessageMetadata


@NetworkMessage.register_child(MessageType.SYNC_REQUEST)
class SyncRequest(NetworkMessage):
    """
    A message to request another node to synchronise its data.
    """
    message_type: MessageType = MessageType.SYNC_REQUEST

    def __init__(self,
                 metadata: MessageMetadata,
                 target: SyncRequestType,
                 ):
        """
        A message to request another node to synchronise its data.
        :param metadata: The metadata for this message
        :param target: What data is being requested from the node.
        """
        super().__init__(
            metadata=metadata
        )
        self.target = target

    def to_dict(self) -> dict:
        """
        Convert the SyncRequest to a dictionary.
        :return: A dictionary representation of the SyncRequest
        """
        payload = super().to_dict()
        payload.update({
            'target': self.target.value,
        })
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'SyncRequest':
        """
        Create a SyncRequest instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of SyncRequest
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])
        target = SyncRequestType(payload['target'])

        return cls(
            metadata=metadata,
            target=target,
        )
