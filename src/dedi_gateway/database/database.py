from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.errors import ConfigurationParsingException
from dedi_gateway.model.network import NetworkRepository
from dedi_gateway.model.network_message import NetworkMessageRepository
from dedi_gateway.model.node import NodeRepository
from dedi_gateway.model.user import UserRepository


class Database:
    @property
    def networks(self) -> NetworkRepository:
        """
        Get the network repository for managing networks in the database.
        :return: NetworkRepository instance.
        """
        raise NotImplementedError

    @property
    def messages(self) -> NetworkMessageRepository:
        """
        Get the network message repository for managing messages in the database.
        :return: NetworkMessageRepository instance.
        """
        raise NotImplementedError

    @property
    def nodes(self) -> NodeRepository:
        """
        Get the node repository for managing nodes in the database.
        :return: NodeRepository instance.
        """
        raise NotImplementedError

    @property
    def users(self) -> UserRepository:
        """
        Get the user repository for managing users in the database.
        :return: UserRepository instance.
        """
        raise NotImplementedError

    async def save_data_index(self,
                              data_index: dict,
                              ):
        """
        Save the data index to the database.
        :param data_index: The data index to save, as a dictionary.
        """
        raise NotImplementedError

    async def get_data_index(self) -> dict:
        """
        Retrieve the data index from the database.
        :return: The data index as a dictionary.
        """
        raise NotImplementedError


_active_db: Database | None = None


def get_active_db() -> Database | None:
    """
    Return the active database set by configuration
    :return: Database instance based on the configuration.
    """
    global _active_db

    if _active_db is not None:
        return _active_db

    if SERVICE_CONFIG.database_driver == 'mongo':
        from pymongo import AsyncMongoClient
        from .mongo_driver import MongoDatabase

        mongo_client = AsyncMongoClient(
            host=SERVICE_CONFIG.mongodb_host,
            port=SERVICE_CONFIG.mongodb_port,
        )
        MongoDatabase.set_client(
            client=mongo_client,
            db_name=SERVICE_CONFIG.mongodb_db_name,
        )

        _active_db = MongoDatabase()

        return _active_db
    elif SERVICE_CONFIG.database_driver == 'memory':
        from .memory import MemoryDatabase

        _active_db = MemoryDatabase()

        return _active_db
    else:
        raise ConfigurationParsingException(
            f'Unsupported database driver: {SERVICE_CONFIG.database_driver}'
        )
