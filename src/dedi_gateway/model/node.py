from dedi_link.model import Node


class NodeRepository:
    """
    Abstract repository interface for managing nodes.
    """
    async def get(self, node_id: str) -> Node | None:
        """
        Retrieve a node by its ID.
        :param node_id: The ID of the node to retrieve.
        :return: Network object or None if not found.
        """
        raise NotImplementedError

    async def batch_get(self, node_ids: list[str]) -> list[Node]:
        """
        Retrieve multiple nodes by their IDs.
        :param node_ids: The list of node IDs to retrieve.
        :return: A list of Node objects.
        """
        raise NotImplementedError

    async def filter(self,
                     *,
                     approved: bool | None = None,
                     ) -> list[Node]:
        """
        Filter nodes based on approval status.
        :param approved: Whether the node is approved for message exchange.
        :return: A list of Node objects that match the filter criteria.
        """
        raise NotImplementedError

    async def save(self, node: Node) -> None:
        """
        Save a node to the repository.
        :param node: Node object to save.
        :return: None
        """
        raise NotImplementedError

    async def delete(self, node_id: str) -> None:
        """
        Delete a node by its ID.
        :param node_id: The ID of the node to delete.
        :return: None
        """
        raise NotImplementedError

    async def update(self, node: Node) -> None:
        """
        Update an existing node in the repository.
        :param node: Node object to update.
        :return: None
        """
        raise NotImplementedError
