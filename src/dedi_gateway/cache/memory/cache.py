import time

from ..cache import Cache


class MemoryCache(Cache):
    """
    An in-memory implementation of the Cache for hot data caching and
    multiprocess state persistence.
    """
    _challenges: dict[str, dict] = {}

    async def save_challenge(self,
                             nonce: str,
                             difficulty: int,
                             timestamp: int,
                             ):
        MemoryCache._challenges[nonce] = {
            'difficulty': difficulty,
            'timestamp': timestamp
        }

    async def get_challenge(self,
                            nonce: str,
                            ) -> int | None:
        challenge = MemoryCache._challenges.get(nonce, None)

        if challenge:
            if challenge['timestamp'] + 300 > int(time.time()):
                return challenge['difficulty']

        return None
