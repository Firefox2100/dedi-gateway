from dedi_link.model import Node

from dedi_gateway.etc.errors import NetworkNotFoundException
from dedi_gateway.model.network import Network, NetworkRepository
from .node import MemoryNodeRepository


class MemoryNetworkRepository(NetworkRepository):
    """
    In-memory implementation of the NetworkRepository interface.
    """
    def __init__(self, db, node_repository: MemoryNodeRepository):
        """
        Initialise the MemoryNetworkRepository with a NodeRepository instance.
        :param node_repository: NodeRepository instance for managing nodes.
        """
        super().__init__(node_repository)
        self.db = db

    async def get(self, network_id: str) -> Network:
        network_data = self.db.get(network_id)

        if not network_data:
            raise NetworkNotFoundException(
                f'Network with ID {network_id} not found.'
            )

        return Network.from_dict(network_data)

    async def filter(self,
                     *,
                     visible: bool | None = None,
                     registered: bool | None = None,
                     ) -> list[Network]:
        networks = list(self.db.values())

        if visible is not None:
            networks = [n for n in networks if n['visible'] == visible]
        if registered is not None:
            networks = [n for n in networks if n['registered'] == registered]

        return [Network.from_dict(n) for n in networks]

    async def save(self, network: Network) -> None:
        if network.network_id in self.db:
            raise ValueError(f'Network with ID {network.network_id} already exists.')

        self.db[network.network_id] = network.to_dict()

    async def delete(self, network_id: str) -> None:
        if network_id not in self.db:
            raise ValueError(f'Network with ID {network_id} does not exist.')

        del self.db[network_id]

    async def update(self, network: Network) -> None:
        if network.network_id not in self.db:
            raise ValueError(f'Network with ID {network.network_id} does not exist.')

        self.db[network.network_id] = network.to_dict()

    async def add_node(self, network_id: str, node: Node) -> None:
        await self.node_repository.save(node)

        if network_id not in self.db:
            raise ValueError(f'Network with ID {network_id} does not exist.')

        network_dict = self.db[network_id]
        network_dict['nodeIds'].append(node.node_id)
