from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.errors import ConfigurationParsingException


class MessageBroker:
    """
    A class to handle message caching and retrieval for network nodes.
    """
    DRIVER_TIMEOUT = 60

    async def get_message(self, node_id: str) -> dict:
        """
        Retrieve a message for a specific node. Async blocking operation,
        so if no message is found, it will wait until a message is available or
        the operation times out.
        :param node_id: The node ID to retrieve the message for.
        :return: A dictionary containing the message data.
        :raises MessageBrokerTimeoutException: If the operation times out.
        """
        raise NotImplementedError(
            'This method should be implemented by subclasses of MessageBroker.'
        )

    async def publish_message(self, node_id: str, message: dict):
        """
        Publish a message to a specific node.
        :param node_id: The node ID to publish the message to.
        :param message: The message data to publish, as a dictionary.
        """


_active_broker: MessageBroker | None = None


def get_active_broker() -> MessageBroker:
    """
    Return the active message broker set by configuration
    :return: MessageBroker instance based on the configuration.
    """
    global _active_broker

    if _active_broker is not None:
        return _active_broker

    if SERVICE_CONFIG.broker_driver == 'redis':
        import redis.asyncio as redis
        from .redis_driver import RedisMessageBroker

        redis_client = redis.Redis(
            host=SERVICE_CONFIG.redis_host,
            port=SERVICE_CONFIG.redis_port,
            decode_responses=True,
        )

        RedisMessageBroker.set_client(redis_client)
        _active_broker = RedisMessageBroker()

        return _active_broker
    elif SERVICE_CONFIG.broker_driver == 'memory':
        from .memory import MemoryMessageBroker

        _active_broker = MemoryMessageBroker()

        return _active_broker
    else:
        raise ConfigurationParsingException(
            f'Unsupported message broker driver: {SERVICE_CONFIG.broker_driver}'
        )
