from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.errors import ConfigurationParsingException
from dedi_gateway.model.route import Route


class Cache:
    """
    A class for hot data caching and multiprocess state persistence.
    """
    async def save_challenge(self,
                             nonce: str,
                             difficulty: int,
                             ):
        """
        Store a generated challenge in the cache.
        :param nonce: The challenge nonce, generated by challenger
        :param difficulty: The difficulty of the challenge, by how many leading zeros it should have
        :param timestamp: The time of generation in seconds since epoch
        """
        raise NotImplementedError

    async def get_challenge(self,
                            nonce: str,
                            ) -> int | None:
        """
        Retrieve a challenge from the cache.
        :param nonce: The challenge nonce to retrieve
        :return: The difficulty of the challenge if it exists and is not expired, otherwise None
        """
        raise NotImplementedError

    async def save_route(self,
                         route: Route,
                         ):
        """
        Save a route to the cache.
        :param route: The route to save
        """
        raise NotImplementedError

    async def get_route(self,
                        node_id: str,
                        ) -> Route | None:
        """
        Retrieve a route from the cache by node ID.
        :param node_id: The ID of the node for which to retrieve the route
        :return: The route if it exists, otherwise None
        """
        raise NotImplementedError

    async def delete_route(self,
                           node_id: str,
                           ) -> bool:
        """
        Delete a route from the cache by node ID.
        :param node_id: The ID of the node for which to delete the route
        """
        raise NotImplementedError


_active_cache: Cache | None = None


def get_active_cache() -> Cache:
    """
    Return the active cache set by configuration
    :return: Cache instance based on the configuration.
    """
    global _active_cache

    if _active_cache is not None:
        return _active_cache

    if SERVICE_CONFIG.cache_driver == 'redis':
        # TODO: Implement RedisCache
        raise NotImplementedError(
            'RedisCache is not implemented yet.'
        )
    elif SERVICE_CONFIG.cache_driver == 'memory':
        from .memory import MemoryCache

        _active_cache = MemoryCache()

        return _active_cache
    else:
        raise ConfigurationParsingException(
            f'Unsupported cache driver: {SERVICE_CONFIG.broker_driver}'
        )
