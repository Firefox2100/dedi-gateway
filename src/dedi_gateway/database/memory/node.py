from dedi_gateway.model.node import Node, NodeRepository



class MemoryNodeRepository(NodeRepository):
    """
    In-memory implementation of the UserRepository interface.
    """

    def __init__(self,
                 db: dict,
                 ):
        """
        Initialise the MongoUserRepository with an in-memory database instance.
        :param db: A dictionary representing the in-memory database.
        """
        self.db = db

    async def get(self, node_id: str) -> Node | None:
        node = self.db.get(node_id)

        return Node.from_dict(node) if node else None

    async def batch_get(self, node_ids: list[str]) -> list[Node]:
        nodes = []

        for node_id in node_ids:
            node = await self.get(node_id)
            if node:
                nodes.append(node)

        return nodes

    async def filter(self,
                     *,
                     approved: bool | None = None,
                     ) -> list[Node]:
        nodes = list(self.db.values())

        if approved is not None:
            nodes = [n for n in nodes if n['approved'] == approved]

        return [Node.from_dict(n) for n in nodes]

    async def save(self, node: Node) -> None:
        if self.db.get(node.node_id):
            raise ValueError(f'Node with ID {node.node_id} already exists.')

        self.db[node.node_id] = node.to_dict()

    async def delete(self, node_id: str) -> None:
        if node_id not in self.db:
            raise ValueError(f'Node with ID {node_id} does not exist.')

        self.db.pop(node_id)

    async def update(self, node: Node) -> None:
        if not self.db.get(node.node_id):
            raise ValueError(f'Node with ID {node.node_id} does not exist.')

        self.db[node.node_id] = node.to_dict()
