from dedi_gateway.etc.enums import MessageType
from dedi_gateway.model.node import Node
from dedi_gateway.model.network import Network
from ..message_metadata import MessageMetadata
from ..network_message import NetworkMessage


@NetworkMessage.register_child(MessageType.AUTH_INVITE)
class AuthInvite(NetworkMessage):
    """
    A message to invite a node to an existing network.
    """
    message_type: MessageType = MessageType.AUTH_INVITE

    def __init__(self,
                 metadata: MessageMetadata,
                 node: Node,
                 network: Network,
                 challenge_nonce: str,
                 challenge_solution: int,
                 justification: str = '',
                 ):
        """
        A message to request joining a network.
        :param metadata: The metadata for the message
        :param node: The node representing the requester
        :param network: The network to which the node is being invited
        :param challenge_nonce: The nonce for the security challenge
        :param challenge_solution: The security challenge solution
        :param justification: The reason for the request
        """
        super().__init__(
            metadata=metadata,
        )
        self.node = node
        self.network = network
        self.challenge_nonce = challenge_nonce
        self.challenge_solution = challenge_solution
        self.justification = justification

    def to_dict(self) -> dict:
        """
        Convert the AuthRequest to a dictionary.
        :return: A dictionary representation of the AuthRequest
        """
        payload = super().to_dict()
        payload.update({
            'node': self.node.to_dict(),
            'network': self.network.to_dict(),
            'challenge': {
                'nonce': self.challenge_nonce,
                'solution': self.challenge_solution,
            },
            'justification': self.justification,
        })
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'AuthInvite':
        """
        Create an AuthRequest instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of AuthRequest
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])
        node = Node.from_dict(payload['node'])
        network = Network.from_dict(payload['network'])

        return cls(
            metadata=metadata,
            node=node,
            network=network,
            challenge_nonce=payload['challenge']['nonce'],
            challenge_solution=payload['challenge']['solution'],
            justification=payload.get('justification', ''),
        )
