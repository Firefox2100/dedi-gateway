from ..database import Database
from .network import MemoryNetworkRepository
from .node import MemoryNodeRepository
from .user import MemoryUserRepository


class MemoryDatabase(Database):
    """
    In-memory implementation of the Database interface.
    This is intended for development and demonstration purposes only.
    Do not use in production.
    """
    _networks = {}
    _nodes = {}
    _users = {}

    @property
    def networks(self) -> MemoryNetworkRepository:
        return MemoryNetworkRepository(
            db=self._networks,
            node_repository=self.nodes,
        )

    @property
    def nodes(self) -> MemoryNodeRepository:
        return MemoryNodeRepository(self._nodes)

    @property
    def users(self) -> MemoryUserRepository:
        return MemoryUserRepository(self._users)
