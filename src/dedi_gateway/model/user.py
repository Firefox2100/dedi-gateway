from typing import Mapping, Any

from .base_model import BaseModel


class UserIdentity:
    """
    A class representing a user's identity in the system.

    A user may be linked to multiple identity services or providers (IdPs),
    and this class encapsulates the user's ID in a specific IdP.
    """
    def __init__(self, idp: str, user_id: str):
        self.idp = idp
        self.user_id = user_id

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the UserIdentity to a dictionary representation.

        :return: Dictionary representation of the UserIdentity.
        """
        return {
            'idp': self.idp,
            'userId': self.user_id
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "UserIdentity":
        """
        Create a UserIdentity instance from a dictionary.

        :param data: Dictionary containing 'idp' and 'userId'.
        :return: UserIdentity instance.
        """
        return cls(
            idp=data['idp'],
            user_id=data['userId']
        )


class User(BaseModel):
    def __init__(self,
                 user_id: str,
                 identities: list[UserIdentity] = None,
                 ):
        self.user_id = user_id
        self.identities = identities or []

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the User to a dictionary representation.

        :return: Dictionary representation of the User.
        """
        return {
            'userId': self.user_id,
            'identities': [identity.to_dict() for identity in self.identities]
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "User":
        """
        Create a User instance from a dictionary.

        :param data: Dictionary containing 'userId' and 'identities'.
        :return: User instance.
        """
        identities = [UserIdentity.from_dict(identity) for identity in data.get('identities', [])]
        return cls(
            user_id=data['userId'],
            identities=identities
        )


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
