from dedi_link.model import Network, Node

from .node import NodeRepository


class NetworkRepository:
    """
    Abstract repository interface for managing networks.
    """
    def __init__(self, node_repository: NodeRepository):
        """
        Abstract repository interface for managing networks.
        :param node_repository: An instance of NodeRepository to manage nodes.
        """
        self.node_repository = node_repository

    async def get(self, network_id: str) -> Network:
        """
        Retrieve a network by its ID.
        :param network_id: The ID of the network to retrieve.
        :return: Network object or None if not found.
        """
        raise NotImplementedError

    async def filter(self,
                     *,
                     visible: bool | None = None,
                     registered: bool | None = None,
                     ) -> list[Network]:
        """
        Filter networks based on visibility, centralisation, and registration status.
        :param visible: Whether the network is visible for others to apply for joining.
        :param registered: Whether the network is registered in a public registry.
        :return: A list of Network objects that match the filter criteria.
        """
        raise NotImplementedError

    async def save(self, network: Network) -> None:
        """
        Save a network to the repository.
        :param network: Network object to save.
        :return: None
        """
        raise NotImplementedError

    async def delete(self, network_id: str) -> None:
        """
        Delete a network by its ID.
        :param network_id: The ID of the network to delete.
        :return: None
        """
        raise NotImplementedError

    async def update(self, network: Network) -> None:
        """
        Update an existing network in the repository.
        :param network: Network object to update.
        :return: None
        """
        raise NotImplementedError

    async def get_nodes(self, network_id: str) -> list[Node]:
        """
        Retrieve all nodes in a network by its ID.
        :param network_id: The ID of the network to retrieve nodes from.
        :return: List of Node objects in the network.
        """
        network = await self.get(network_id)

        if not network:
            return []

        nodes = await self.node_repository.batch_get(network.node_ids)

        return nodes

    async def add_node(self, network_id: str, node: Node) -> None:
        """
        Add a node to a network.
        :param network_id: The ID of the network to add the node to.
        :param node: The Node object to add to the network.
        """
        raise NotImplementedError
