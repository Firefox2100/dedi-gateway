import json
import redis.asyncio as redis

from dedi_gateway.etc.errors import MessageBrokerTimeoutException
from ..message_broker import MessageBroker


class RedisMessageBroker(MessageBroker):
    """
    A Redis-based implementation of the MessageBroker for caching and retrieving messages.
    """
    _db: redis.Redis | None = None

    @property
    def db(self) -> redis.Redis:
        """
        Get the Redis database instance.
        :return: The Redis database instance.
        """
        if self._db is None:
            raise ValueError("Redis client is not set. Call set_client() first.")
        return self._db

    @classmethod
    def set_client(cls,
                   client: redis.Redis,
                   ):
        """
        Set the Redis client for the message broker.
        :param client: Redis client instance.
        """
        cls._db = client

    async def get_message(self, node_id: str) -> dict:
        channel_name = f'message:node:{node_id}'

        value = await self.db.blpop(
            [channel_name],
            timeout=self.DRIVER_TIMEOUT,
        )

        if value:
            return json.loads(value[1])

        raise MessageBrokerTimeoutException(
            f'Timed out waiting for message for node {node_id}.'
        )

    async def publish_message(self, node_id: str, message: dict):
        channel_name = f'message:node:{node_id}'
        message_json = json.dumps(message)

        await self.db.lpush(
            channel_name,
            message_json,
        )
