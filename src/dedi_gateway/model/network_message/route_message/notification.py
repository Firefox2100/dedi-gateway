from dedi_gateway.etc.enums import MessageType
from ..message_metadata import MessageMetadata
from ..network_message import NetworkMessage


@NetworkMessage.register_child(MessageType.ROUTE_NOTIFICATION)
class RouteNotification(NetworkMessage):
    """
    A message to notify the network that a node either went offline,
    or broke the existing route.
    """
    message_type: MessageType = MessageType.ROUTE_NOTIFICATION

    def __init__(self,
                 metadata: MessageMetadata,
                 target_node: str,
                 ):
        """
        A message to notify the network that a node either went offline,
        or broke the existing route.
        :param metadata: The metadata for the message
        :param target_node: The ID of the target node to route to
        """
        super().__init__(
            metadata=metadata,
        )
        self.target_node = target_node

    def to_dict(self) -> dict:
        """
        Convert the RouteNotification to a dictionary.
        :return: A dictionary representation of the RouteRequest
        """
        payload = super().to_dict()
        payload.update({
            'targetNode': self.target_node,
        })
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'RouteNotification':
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
