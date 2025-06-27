from dedi_gateway.model.user import UserRepository


class Database:
    @property
    def users(self) -> UserRepository:
        """
        Get the user repository for managing users in the database.
        :return: UserRepository instance.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
