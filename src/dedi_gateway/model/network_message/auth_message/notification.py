from dedi_gateway.etc.enums import MessageType, AuthNotificationType
from ..network_message import NetworkMessage, MessageMetadata


@NetworkMessage.register_child(MessageType.AUTH_NOTIFICATION)
class AuthNotification(NetworkMessage):
    """
    A message to notify the network about an event, whether it be
    a node joining, leaving, or any other significant event related
    to authorisation and authentication.
    """
    message_type: MessageType = MessageType.AUTH_NOTIFICATION

    def __init__(self,
                 metadata: MessageMetadata,
                 reason: AuthNotificationType,
                 affected_node_id: str,
                 affected_node_signature: str,
                 ):
        """
        A message to notify the network about an event.
        :param metadata: The metadata for this message
        :param reason: The reason for the notification, such as joining or leaving
        :param affected_node_id: Which node triggered the notification
        """
        super().__init__(
            metadata=metadata,
        )
        self.reason = reason
        self.affected_node_id = affected_node_id
        self.affected_node_signature = affected_node_signature

    def to_dict(self) -> dict:
        """
        Convert the AuthNotification to a dictionary.
        :return: A dictionary representation of the AuthNotification
        """
        payload = super().to_dict()
        payload.update({
            'reason': self.reason.value,
            'affectedNodeId': self.affected_node_id,
            'affectedNodeSignature': self.affected_node_signature,
        })
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'AuthNotification':
        """
        Create an AuthNotification instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of AuthNotification
        """
        metadata = MessageMetadata.from_dict(payload['metadata'])
        reason = AuthNotificationType(payload['reason'])

        return cls(
            metadata=metadata,
            reason=reason,
            affected_node_id=payload['affectedNodeId'],
            affected_node_signature=payload['affectedNodeSignature'],
        )
