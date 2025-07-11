from dedi_gateway.etc.enums import MessageType
from ..message_metadata import MessageMetadata
from ..network_message import NetworkMessage


@NetworkMessage.register_child(MessageType.ROUTE_REQUEST)
class RouteRequest(NetworkMessage):
    """
    A message to request a viable route to a specific node in the network.
    """
    message_type: MessageType = MessageType.ROUTE_REQUEST

    def __init__(self,
                 metadata: MessageMetadata,
                 target_node: str,
                 ):
        """
        A message to request a viable route to a specific node in the network.
        :param metadata: The metadata for the message
        :param target_node: The ID of the target node to route to
        """
        super().__init__(
            metadata=metadata,
        )
        self.target_node = target_node

    def to_dict(self) -> dict:
        """
        Convert the RouteRequest to a dictionary.
        :return: A dictionary representation of the RouteRequest
        """
        payload = super().to_dict()
        payload.update({
            'targetNode': self.target_node,
        })
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'RouteRequest':
        """
        Create a RouteRequest instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of RouteRequest
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])

        return cls(
            metadata=metadata,
            target_node=payload['targetNode'],
        )
