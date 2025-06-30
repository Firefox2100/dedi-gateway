class MessageMetadata:
    """
    Metadata for a message in the Decentralised Discovery Link network.
    """
    def __init__(self,
                 network_id: str,
                 node_id: str,
                 message_id: str,
                 timestamp: float,
                 ):
        """
        Metadata for a message in the Decentralised Discovery Link network.
        :param network_id: The unique ID of the network
        :param node_id: The unique ID of the node that sent the message
        :param message_id: The unique ID of the message
        :param timestamp: The timestamp when the message was sent, in seconds since the epoch
        """
        self.network_id = network_id
        self.node_id = node_id
        self.message_id = message_id
        self.timestamp = timestamp
