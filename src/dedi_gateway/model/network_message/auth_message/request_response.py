from dedi_gateway.etc.enums import MessageType
from dedi_gateway.model.node import Node
from dedi_gateway.model.network import Network
from ..message_metadata import MessageMetadata
from ..network_message import NetworkMessage


@NetworkMessage.register_child(MessageType.AUTH_REQUEST_RESPONSE)
class AuthRequestResponse(NetworkMessage):
    """
    A message responding to a join request.
    """
    def __init__(self,
                 metadata: MessageMetadata,
                 approved: bool,
                 node: Node = None,
                 network: Network = None,
                 justification: str = '',
                 ):
        """
        A message responding to a join request.
        :param metadata: The metadata for the message
        :param approved: Whether the request is approved or not
        :param node: The node representing the responder, if approved
        :param network: The detailed network information, if approved
        :param justification: The reason for the response
        """
        super().__init__(
            metadata=metadata,
        )
        self.approved = approved
        self.node = node
        self.network = network
        self.justification = justification

    def to_dict(self) -> dict:
        """
        Convert the AuthRequestResponse to a dictionary.
        :return: A dictionary representation of the AuthRequestResponse
        """
        payload = super().to_dict()
        payload.update({
            'approved': self.approved,
            'justification': self.justification,
        })
        if self.approved:
            payload['node'] = self.node.to_dict() if self.node else None
            payload['network'] = self.network.to_dict() if self.network else None

        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'AuthRequestResponse':
        """
        Create an AuthRequestResponse instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of AuthRequestResponse
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])
        node = Node.from_dict(payload['node']) if payload.get('node') else None
        network = Network.from_dict(payload['network']) if payload.get('network') else None

        return cls(
            metadata=metadata,
            approved=payload['approved'],
            node=node,
            network=network,
            justification=payload.get('justification', ''),
        )
