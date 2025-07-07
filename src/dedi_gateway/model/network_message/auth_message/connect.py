from dedi_gateway.etc.enums import MessageType
from ..network_message import NetworkMessage


@NetworkMessage.register_child(MessageType.AUTH_CONNECT)
class AuthConnect(NetworkMessage):
    """
    A message to authenticate a connection between nodes.
    """
    message_type: MessageType = MessageType.AUTH_CONNECT
