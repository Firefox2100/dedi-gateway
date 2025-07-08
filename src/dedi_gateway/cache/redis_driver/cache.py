import json
import redis.asyncio as redis

from dedi_gateway.model.route import Route
from ..cache import Cache


class RedisCache(Cache):
    """
    A Redis-based implementation of the Cache for sharing data between processes.
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
        Set the Redis client for the cache.
        :param client: Redis client instance.
        """
        cls._db = client

    async def save_challenge(self,
                             nonce: str,
                             difficulty: int,
                             ):
        await self.db.set(
            f'challenge:{nonce}',
            difficulty,
            ex=300,
        )

    async def get_challenge(self,
                            nonce: str,
                            ) -> int | None:
        return await self.db.get(f'challenge:{nonce}')

    async def save_route(self,
                         route: Route,
                         ):
        route_data = route.to_dict()

        await self.db.set(
            f'route:{route.node_id}',
            json.dumps(route_data),
        )

    async def get_route(self,
                        node_id: str,
                        ) -> Route | None:
        route_data = await self.db.get(f'route:{node_id}')

        if route_data:
            return Route.from_dict(json.loads(route_data))

        return None

    async def delete_route(self,
                           node_id: str,
                           ) -> bool:
        result = await self.db.delete(f'route:{node_id}')

        return result > 0
