import time

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
                return challenge['difficulty']

        return None

    async def save_route(self,
                         route: Route,
                         ):
        MemoryCache._routes[route.node_id] = route.to_dict()

    async def get_route(self,
                        node_id: str,
                        ) -> Route | None:
        route_data = MemoryCache._routes.get(node_id, None)

        if route_data:
            return Route.from_dict(route_data)

        return None
