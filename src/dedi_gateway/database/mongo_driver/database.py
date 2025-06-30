from pymongo import AsyncMongoClient

from ..database import Database
from .network import MongoNetworkRepository
from .node import MongoNodeRepository
from .user import MongoUserRepository


class MongoDatabase(Database):
    """
    MongoDB implementation of the Database interface.
    """
    _client = None
    _db_name = 'dedi-gateway'

    @property
    def db(self):
        """
        Get the MongoDB database instance.
        :return: The MongoDB database instance.
        """
        if self._client is None:
            raise ValueError('MongoDB client is not set. Call set_client() first.')
        return self._client[self._db_name]

    @property
    def networks(self) -> MongoNetworkRepository:
        return MongoNetworkRepository(
            db=self.db,
            node_repository=self.nodes,
        )

    @property
    def nodes(self) -> MongoNodeRepository:
        return MongoNodeRepository(self.db)

    @property
    def users(self) -> MongoUserRepository:
        return MongoUserRepository(self.db)

    @classmethod
    def set_client(cls,
                   client: AsyncMongoClient,
                   db_name: str = 'dedi-gateway'
                   ):
        """
        Set the MongoDB client for the database.
        :param client: AsyncMongoClient instance.
        :param db_name: Name of the database to use.
        """
        cls._client = client
        cls._db_name = db_name
