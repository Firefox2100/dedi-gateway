import time

from dedi_gateway.etc.consts import LOGGER
from dedi_gateway.model.route import Route
from ..cache import Cache


class MemoryCache(Cache):
    """
    An in-memory implementation of the Cache for hot data caching and
    multiprocess state persistence.
    """
    _challenges: dict[str, dict] = {}
    _routes: dict[str, dict] = {}

    async def save_challenge(self,
                             nonce: str,
                             difficulty: int,
                             ):
        LOGGER.debug(
            'Saving challenge to memory cache: nonce=%s, difficulty=%d',
            nonce,
            difficulty
        )

        MemoryCache._challenges[nonce] = {
            'difficulty': difficulty,
            'timestamp': time.time(),
        }

    async def get_challenge(self,
                            nonce: str,
                            ) -> int | None:
        challenge = MemoryCache._challenges.get(nonce, None)

        if challenge:
            if challenge['timestamp'] + 300 > int(time.time()):
                LOGGER.debug(
                    'Challenge found in memory cache: nonce=%s, difficulty=%d',
                    nonce,
                    challenge['difficulty']
                )
                return challenge['difficulty']

            LOGGER.warning(
                'Expired challenge accessed in memory cache: nonce=%s, difficulty=%d',
                nonce,
                challenge['difficulty']
            )

        return None

    async def save_route(self,
                         route: Route,
                         ):
        LOGGER.debug(
            'Saving route to memory cache: node_id=%s, route=%s',
            route.node_id,
            route.to_dict()
        )

        MemoryCache._routes[route.node_id] = route.to_dict()

    async def get_route(self,
                        node_id: str,
                        ) -> Route | None:
        route_data = MemoryCache._routes.get(node_id, None)

        if route_data:
            LOGGER.debug(
                'Route found in memory cache: node_id=%s, route=%s',
                node_id,
                route_data
            )

            return Route.from_dict(route_data)

        LOGGER.warning(
            'Route not found in memory cache: node_id=%s',
            node_id
        )

        return None

    async def delete_route(self,
                           node_id: str,
                           ) -> bool:
        if node_id in MemoryCache._routes:
            del MemoryCache._routes[node_id]

            LOGGER.debug(
                'Route deleted from memory cache: node_id=%s',
                node_id
            )
            return True

        LOGGER.warning(
            'Attempted to delete non-existent route in memory cache: node_id=%s',
            node_id
        )

        return False
