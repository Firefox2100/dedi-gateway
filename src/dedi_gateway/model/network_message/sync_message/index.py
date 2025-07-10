from dedi_gateway.etc.enums import MessageType
from ..network_message import NetworkMessage, MessageMetadata


@NetworkMessage.register_child(MessageType.SYNC_INDEX)
class SyncIndex(NetworkMessage):
    """
    A message to synchronize the data index across nodes in the network.
    """
    message_type: MessageType = MessageType.SYNC_INDEX

    def __init__(self,
                 metadata: MessageMetadata,
                 data_index: dict,
                 ):
        """
        A message to synchronize the data index across nodes in the network.
        :param metadata: The metadata for this message
        :param data_index: The data index to be synchronized. This should be implemented
            by the services using this gateway, as it is specific to application logic.
        """
        super().__init__(
            metadata=metadata
        )
        self.data_index = data_index

    def to_dict(self) -> dict:
        """
        Convert the SyncIndex to a dictionary.
        :return: A dictionary representation of the SyncIndex
        """
        payload = super().to_dict()
        payload.update({
            'dataIndex': self.data_index,
        })
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'SyncIndex':
        """
        Create a SyncIndex instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of SyncIndex
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])

        return cls(
            metadata=metadata,
            data_index=payload['dataIndex'],
        )
