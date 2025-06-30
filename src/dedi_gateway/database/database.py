from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.model.user import UserRepository


class Database:
    @property
    def users(self) -> UserRepository:
        """
        Get the user repository for managing users in the database.
        :return: UserRepository instance.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


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
        from .mongo import MongoDatabase
        _active_db = MongoDatabase()

        return _active_db

    return None
