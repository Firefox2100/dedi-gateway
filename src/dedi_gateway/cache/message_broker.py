from typing import AsyncGenerator

from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.errors import ConfigurationParsingException


class MessageBroker:
    """
    A class to handle message caching and retrieval for network nodes.
    """
    DRIVER_TIMEOUT = 60

    async def get_message(self, node_id: str) -> dict | None:
        """
        Retrieve a message for a specific node. Async blocking operation,
        so if no message is found, it will wait until a message is available or
        the operation times out.
        :param node_id: The node ID to retrieve the message for.
        :return: A dictionary containing the message data.
        """
        raise NotImplementedError

    async def publish_message(self, node_id: str, message: dict):
        """
        Publish a message to a specific node.
        :param node_id: The node ID to publish the message to.
        :param message: The message data to publish, as a dictionary.
        """
        raise NotImplementedError

    async def add_to_response(self,
                              message: dict,
                              ):
        """
        Add a response message to the broker.
        :param message: The response message to add, as a dictionary.
        """
        raise NotImplementedError

    def response_generator(self,
                                 message_id: str,
                                 message_count: int = 1,
                                 ) -> AsyncGenerator[dict, None]:
        """
        Asynchronous generator to yield responses for a specific message ID.
        :param message_id: The ID of the message to retrieve responses for.
        :param message_count: The number of expected responses.
        :return: An asynchronous generator yielding response messages.
        """
        raise NotImplementedError


_active_broker: MessageBroker | None = None


def get_active_broker() -> MessageBroker:
    """
    Return the active message broker set by configuration
    :return: MessageBroker instance based on the configuration.
    """
    global _active_broker

    if _active_broker is not None:
        return _active_broker

    if SERVICE_CONFIG.cache_driver == 'redis':
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
    elif SERVICE_CONFIG.cache_driver == 'memory':
        from .memory import MemoryMessageBroker

        _active_broker = MemoryMessageBroker()

        return _active_broker
    else:
        raise ConfigurationParsingException(
            f'Unsupported message broker driver: {SERVICE_CONFIG.cache_driver}'
        )
