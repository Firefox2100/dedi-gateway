from dedi_gateway.etc.enums import MessageType
from dedi_gateway.model.node import Node
from ..network_message import NetworkMessage, MessageMetadata


@NetworkMessage.register_child(MessageType.SYNC_NODES)
class SyncNode(NetworkMessage):
    """
    A message to synchronize the known nodes across other nodes in the network.
    """
    message_type: MessageType = MessageType.SYNC_NODES

    def __init__(self,
                 metadata: MessageMetadata,
                 nodes: list[Node],
                 ):
        """
        A message to synchronize the data index across nodes in the network.
        :param metadata: The metadata for this message
        :param nodes: The known nodes to be synchronized, including the current node.
        """
        super().__init__(
            metadata=metadata
        )
        self.nodes = nodes

    def to_dict(self) -> dict:
        """
        Convert the SyncNode to a dictionary.
        :return: A dictionary representation of the SyncNode
        """
        payload = super().to_dict()
        payload.update({
            'nodes': [node.to_dict() for node in self.nodes],
        })
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'SyncNode':
        """
        Create a SyncNode instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of SyncNode
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])
        nodes = [Node.from_dict(node) for node in payload['nodes']]

        return cls(
            metadata=metadata,
            nodes=nodes,
        )
