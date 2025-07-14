from dedi_link.model import User

from dedi_gateway.model.user import UserRepository


class MemoryUserRepository(UserRepository):
    """
    In-memory implementation of the UserRepository interface.
    """
    def __init__(self, db: dict):
        """
        Initialise the MemoryUserRepository with a dictionary.
        :param db: A dictionary to act as the in-memory database.
        """
        self.db = db

    async def get(self, user_id: str) -> User | None:
        user = self.db.get(user_id)

        return User.from_dict(user) if user else None

    async def save(self, user: User) -> None:
        if self.db.get(user.user_id):
            raise ValueError(f'User with ID {user.user_id} already exists.')

        self.db[user.user_id] = user.to_dict()

    async def delete(self, user_id: str) -> None:
        if user_id not in self.db:
            raise ValueError(f'User with ID {user_id} does not exist.')

        self.db.pop(user_id)

    async def update(self, user: User) -> None:
        if not self.db.get(user.user_id):
            raise ValueError(f'User with ID {user.user_id} does not exist.')

        self.db[user.user_id] = user.to_dict()
