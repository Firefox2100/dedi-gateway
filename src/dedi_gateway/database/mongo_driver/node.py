from pymongo.asynchronous.database import AsyncDatabase

from dedi_gateway.model.node import Node, NodeRepository


class MongoNodeRepository(NodeRepository):
    """
    MongoDB implementation of the UserRepository interface.
    """
    def __init__(self,
                 db: AsyncDatabase,
                 ):
        """
        Initialise the MongoUserRepository with a MongoDB database instance.
        :param db: MongoDB database instance.
        """
        self.db = db
        self.collection = db['nodes']

    async def get(self, node_id: str) -> Node | None:
        node = await self.collection.find_one({'nodeId': node_id})

        return Node.from_dict(node) if node else None

    async def batch_get(self, node_ids: list[str]) -> list[Node]:
        cursor = self.collection.find({'nodeId': {'$in': node_ids}})

        nodes = []
        async for node in cursor:
            nodes.append(Node.from_dict(node))

        return nodes

    async def filter(self,
                     *,
                     approved: bool | None = None,
                     ) -> list[Node]:
        query = {}
        if approved is not None:
            query['approved'] = approved

        cursor = self.collection.find(query)
        nodes = []

        async for node in cursor:
            nodes.append(Node.from_dict(node))

        return nodes

    async def save(self, node: Node) -> None:
        await self.collection.update_one(
            {'nodeId': node.node_id},
            {'$set': node.to_dict()},
            upsert=True
        )

    async def delete(self, node_id: str) -> None:
        await self.collection.delete_one({'nodeId': node_id})

    async def update(self, node: Node) -> None:
        await self.collection.update_one(
            {'nodeId': node.node_id},
            {'$set': node.to_dict()}
        )
