from ..database import Database
from .network import MemoryNetworkRepository
from .network_message import MemoryNetworkMessageRepository
from .node import MemoryNodeRepository
from .user import MemoryUserRepository


class MemoryDatabase(Database):
    """
    In-memory implementation of the Database interface.
    This is intended for development and demonstration purposes only.
    Do not use in production.
    """
    _networks = {}
    _messages = {}
    _nodes = {}
    _users = {}
    _data_index = {}

    @property
    def networks(self) -> MemoryNetworkRepository:
        return MemoryNetworkRepository(
            db=self._networks,
            node_repository=self.nodes,
        )

    @property
    def messages(self) -> MemoryNetworkMessageRepository:
        return MemoryNetworkMessageRepository(self._messages)

    @property
    def nodes(self) -> MemoryNodeRepository:
        return MemoryNodeRepository(self._nodes)

    @property
    def users(self) -> MemoryUserRepository:
        return MemoryUserRepository(self._users)

    async def save_data_index(self,
                              data_index: dict,
                              ):
        MemoryDatabase._data_index = data_index

    async def get_data_index(self) -> dict:
        return self._data_index
