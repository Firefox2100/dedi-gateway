import asyncio
from typing import AsyncGenerator

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
            while True:
                async with self._lock:
                    if index < len(self._queue):
                        return self._queue.pop(index)
                await self._condition.wait()


class MemoryMessageBroker(MessageBroker):
    """
    An in-memory implementation of the MessageBroker for caching and retrieving messages.
    """
    _messages = {}
    _responses = {}

    async def get_message(self, node_id: str) -> dict | None:
        queue: AsyncQueue | None = MemoryMessageBroker._messages.get(node_id, None)

        counter = 0
        while counter < self.DRIVER_TIMEOUT * 2:
            if queue:
                try:
                    message = await queue.pop_by_index(0)
                    return message
                except IndexError:
                    pass

            await asyncio.sleep(0.5)

            if queue is None:
                queue = MemoryMessageBroker._messages.get(node_id, None)

            counter += 1

        return None

    async def publish_message(self, node_id: str, message: dict):
        queue = MemoryMessageBroker._messages.get(node_id, None)
        if queue is None:
            queue = AsyncQueue()
            MemoryMessageBroker._messages[node_id] = queue

        await queue.put(message)

    async def add_to_response(self,
                              message: dict,
                              ):
        queue = MemoryMessageBroker._responses.get(message['metadata']['messageId'], None)
        if queue is None:
            queue = AsyncQueue()
            MemoryMessageBroker._responses[message['metadata']['messageId']] = queue

        await queue.put(message)

    async def response_generator(self,
                                 message_id: str,
                                 message_count: int = 1,
                                 ) -> AsyncGenerator[dict, None]:
        queue: AsyncQueue | None = MemoryMessageBroker._responses.get(message_id, None)
        time_counter = 0
        message_counter = 0

        while message_counter < message_count and time_counter < self.DRIVER_TIMEOUT * 2:
            if queue:
                try:
                    response = await queue.pop_by_index(0)
                    message_counter += 1
                    time_counter = 0
                    yield response
                except IndexError:
                    pass

            await asyncio.sleep(0.5)
            time_counter += 1

            if queue is None:
                queue = MemoryMessageBroker._responses.get(message_id, None)

        if message_counter < message_count:
            raise MessageBrokerTimeoutException(
                f'Timeout while waiting for response for message ID: {message_id}'
            )
