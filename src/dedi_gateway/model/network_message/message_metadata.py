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

    def to_dict(self):
        """
        Convert the message metadata to a dictionary.
        :return: A dictionary representation of the message metadata
        """
        return {
            'networkId': self.network_id,
            'nodeId': self.node_id,
            'messageId': self.message_id,
            'timestamp': self.timestamp,
        }

    @classmethod
    def from_dict(cls, payload: dict):
        """
        Create a MessageMetadata instance from a dictionary.
        :param payload: A dictionary containing the message metadata
        :return: An instance of MessageMetadata
        """
        return cls(
            network_id=payload['networkId'],
            node_id=payload['nodeId'],
            message_id=payload['messageId'],
            timestamp=payload['timestamp'],
        )
