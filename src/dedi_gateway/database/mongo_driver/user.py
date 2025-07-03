from pymongo.asynchronous.database import AsyncDatabase

from dedi_gateway.model.user import User, UserRepository


class MongoUserRepository(UserRepository):
    """
    MongoDB implementation of the UserRepository interface.
    """
    def __init__(self, db: AsyncDatabase):
        """
        Initialise the MongoUserRepository with a MongoDB database instance.
        :param db: MongoDB database instance.
        """
        self.db = db
        self.collection = db['users']

    async def get(self, user_id: str) -> User | None:
        user_data = await self.collection.find_one({'userId': user_id})

        if user_data:
            return User.from_dict(user_data)

        return None

    async def save(self, user: User) -> None:
        await self.collection.update_one(
            {'userId': user.user_id},
            {'$set': user.to_dict()},
            upsert=True
        )

    async def delete(self, user_id: str) -> None:
        await self.collection.delete_one({'userId': user_id})

    async def update(self, user: User) -> None:
        await self.collection.update_one(
            {'userId': user.user_id},
            {'$set': user.to_dict()}
        )
