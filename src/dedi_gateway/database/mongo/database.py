from pymongo import AsyncMongoClient

from ..database import Database
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
            raise ValueError("MongoDB client is not set. Call set_client() first.")
        return self._client[self._db_name]

    @property
    def users(self):
        """
        User repository for managing users in the MongoDB database.
        :return:
        """
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
