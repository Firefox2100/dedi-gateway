import asyncio

from dedi_gateway.etc.errors import MessageBrokerTimeoutException
from ..message_broker import MessageBroker


class AsyncQueue:
    """
    A thread-safe asynchronous queue for data exchange.
    """
    def __init__(self):
        self._queue = []
        self._condition = asyncio.Condition()
        self._lock = asyncio.Lock()

    def __len__(self):
        with self._lock:
            return len(self._queue)

    async def put(self, item):
        """
        Asynchronously put an item in the back of the queue
        """
        async with self._condition:
            async with self._lock:
                self._queue.append(item)
            self._condition.notify_all()

    async def get(self):
        """
        Asynchronously get an item from the front of the queue
        """
        async with self._condition:
            while not self._queue:
                await self._condition.wait()
            async with self._lock:
                return self._queue.pop(0)

    async def pop_by_index(self, index: int):
        """
        Asynchronously pop an item from the queue by index and return it
        """
        async with self._condition:
            while not self._queue or index >= len(self._queue):
                await self._condition.wait()
            async with self._lock:
                return self._queue.pop(index)


class MemoryMessageBroker(MessageBroker):
    """
    An in-memory implementation of the MessageBroker for caching and retrieving messages.
    """
    _db = {}

    async def get_message(self, node_id: str) -> dict:
        queue: AsyncQueue | None = MemoryMessageBroker._db.get(node_id, None)

        counter = 0
        while counter < self.DRIVER_TIMEOUT * 2:
            if queue:
                message = await queue.get()
                return message

            await asyncio.sleep(0.5)

            if queue is None:
                queue = MemoryMessageBroker._db.get(node_id, None)

        raise MessageBrokerTimeoutException(
            f'Timed out waiting for message for node {node_id}.'
        )

    async def publish_message(self, node_id: str, message: dict):
        queue = MemoryMessageBroker._db.get(node_id, None)
        if queue is None:
            queue = AsyncQueue()
            MemoryMessageBroker._db[node_id] = queue

        await queue.put(message)
