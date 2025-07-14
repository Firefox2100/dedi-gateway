from dedi_link.model import User


class UserRepository:
    """
    Abstract repository interface for managing users.
    """
    async def get(self, user_id: str) -> User | None:
        """
        Retrieve a user by their ID.
        :param user_id: The ID of the user to retrieve.
        :return: User object or None if not found.
        """
        raise NotImplementedError

    async def save(self, user: User) -> None:
        """
        Save a user to the repository.
        :param user: User object to save.
        :return: None
        """
        raise NotImplementedError

    async def delete(self, user_id: str) -> None:
        """
        Delete a user from the repository.
        :param user_id: The ID of the user to delete.
        :return: None
        """
        raise NotImplementedError

    async def update(self, user: User) -> None:
        """
        Update an existing user in the repository.
        :param user: User object with updated data.
        :return: None
        """
        raise NotImplementedError
