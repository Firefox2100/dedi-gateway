from pymongo.asynchronous.database import AsyncDatabase
from dedi_link.model import Node, Network

from dedi_gateway.etc.errors import NetworkNotFoundException
from dedi_gateway.model.network import NetworkRepository
from .node import MongoNodeRepository


class MongoNetworkRepository(NetworkRepository):
    """
    MongoDB implementation of the NetworkRepository interface.
    """
    def __init__(self,
                 db: AsyncDatabase,
                 node_repository: MongoNodeRepository
                 ):
        """
        Initialise the MongoUserRepository with a MongoDB database instance.
        :param db: MongoDB database instance.
        :param node_repository: NodeRepository instance for managing nodes.
        """
        super().__init__(node_repository)

        self.db = db
        self.collection = db['networks']

    async def get(self, network_id: str) -> Network:
        network_data = await self.collection.find_one({'networkId': network_id})

        if network_data:
            return Network.from_dict(network_data)

        raise NetworkNotFoundException(
            f'Network with ID {network_id} not found.'
        )

    async def filter(self,
                     *,
                     visible: bool | None = None,
                     registered: bool | None = None,
                     ) -> list[Network]:
        filters = {}

        if visible is not None:
            filters['visible'] = visible
        if registered is not None:
            filters['registered'] = registered

        cursor = self.collection.find(filters)

        networks = []
        async for network_data in cursor:
            networks.append(Network.from_dict(network_data))

        return networks

    async def save(self, network: Network) -> None:
        await self.collection.update_one(
            {'networkId': network.network_id},
            {'$set': network.to_dict()},
            upsert=True
        )

    async def delete(self, network_id: str) -> None:
        await self.collection.delete_one({'networkId': network_id})

    async def update(self, network: Network) -> None:
        await self.collection.update_one(
            {'networkId': network.network_id},
            {'$set': network.to_dict()}
        )

    async def add_node(self, network_id: str, node: Node) -> None:
        await self.node_repository.save(node)

        await self.collection.update_one(
            {'networkId': network_id},
            {'$addToSet': {'nodeIds': node.node_id}}
        )
