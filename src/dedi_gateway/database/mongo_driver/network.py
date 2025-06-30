from typing import TYPE_CHECKING

from dedi_gateway.model.network import Network, NetworkRepository
from .node import MongoNodeRepository

if TYPE_CHECKING:
    from pymongo.asynchronous.database import AsyncDatabase


class MongoNetworkRepository(NetworkRepository):
    """
    MongoDB implementation of the UserRepository interface.
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

    async def get(self, network_id: str) -> Network | None:
        network_data = await self.collection.find_one({'networkId': network_id})

        if network_data:
            return Network.from_dict(network_data)

        return None

    async def filter(self,
                     *,
                     visible: bool | None = None,
                     centralised: bool | None = None,
                     registered: bool | None = None,
                     ) -> list[Network]:
        filters = {}

        if visible is not None:
            filters['visible'] = visible
        if centralised is not None:
            filters['centralised'] = centralised
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
