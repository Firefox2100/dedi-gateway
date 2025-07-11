from dedi_gateway.etc.enums import MessageType
from ..message_metadata import MessageMetadata
from ..network_message import NetworkMessage


@NetworkMessage.register_child(MessageType.ROUTE_REQUEST)
class RouteResponse(NetworkMessage):
    """
    A message to announce a viable route to a specific node in the network.
    """
    message_type: MessageType = MessageType.ROUTE_RESPONSE

    def __init__(self,
                 metadata: MessageMetadata,
                 target_node: str,
                 route: list[str],
                 ):
        """
        A message to announce a viable route to a specific node in the network.
        :param metadata: The metadata for the message
        :param target_node: The ID of the target node to route to
        :param route: The list of node IDs representing the route
        """
        super().__init__(
            metadata=metadata,
        )
        self.target_node = target_node
        self.route = route

    def to_dict(self) -> dict:
        """
        Convert the RouteResponse to a dictionary.
        :return: A dictionary representation of the RouteResponse
        """
        payload = super().to_dict()
        payload.update({
            'targetNode': self.target_node,
            'route': self.route,
        })
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'RouteResponse':
        """
        Create a RouteResponse instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of RouteResponse
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])

        return cls(
            metadata=metadata,
            target_node=payload['targetNode'],
            route=payload['route'],
        )
