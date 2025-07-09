from dedi_gateway.etc.enums import MessageType
from dedi_gateway.model.node import Node
from ..message_metadata import MessageMetadata
from ..network_message import NetworkMessage


@NetworkMessage.register_child(MessageType.AUTH_INVITE_RESPONSE)
class AuthInviteResponse(NetworkMessage):
    """
    A message responding to an invitation to join a network.
    """
    message_type = MessageType.AUTH_INVITE_RESPONSE

    def __init__(self,
                 metadata: MessageMetadata,
                 approved: bool,
                 node: Node = None,
                 justification: str = '',
                 ):
        """
        A message responding to an invitation to join a network.
        :param metadata: The metadata for the message
        :param approved: Whether the invitation is accepted or not
        :param node: The node representing the responder, if accepted
        :param justification: The reason for the response
        """
        super().__init__(
            metadata=metadata,
        )
        self.approved = approved
        self.node = node
        self.justification = justification

    def to_dict(self) -> dict:
        """
        Convert the AuthInviteResponse to a dictionary.
        :return: A dictionary representation of the AuthInviteResponse
        """
        payload = super().to_dict()
        payload.update({
            'approved': self.approved,
            'justification': self.justification,
        })
        if self.approved:
            payload['node'] = self.node.to_dict() if self.node else None

        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'AuthInviteResponse':
        """
        Create an AuthInviteResponse from a dictionary.
        :param payload: The dictionary containing the message data
        :return: An AuthInviteResponse instance
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])
        approved = payload['approved']
        node = Node.from_dict(payload['node']) if 'node' in payload else None
        justification = payload.get('justification', '')

        return cls(
            metadata=metadata,
            approved=approved,
            node=node,
            justification=justification,
        )
