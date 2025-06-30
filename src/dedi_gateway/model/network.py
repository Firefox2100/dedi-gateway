import uuid

from .base_model import BaseModel
from .node import Node, NodeRepository


class Network(BaseModel):
    def __init__(self,
                 network_id: str,
                 network_name: str,
                 *,
                 description: str = '',
                 node_ids: list[str] | None = None,
                 visible: bool = False,
                 centralised: bool = False,
                 registered: bool = False,
                 instance_id: str = None,
                 ):
        """
        A network that contains nodes which agreed to share data among each other.

        A network is a logical abstraction of a group of nodes that accepts (partially)
        others credentials and allows access to their data.

        :param network_id: The unique ID of the network
        :param network_name: The name of the network
        :param description: A description of the network
        :param node_ids: The IDs of the nodes in the network
        :param visible: Whether the network is visible to others to apply for joining
        :param centralised: Whether the network has a centralised node for permission and identity management
        :param registered: Whether the network is registered in a public registry
        :param instance_id: The unique ID of the network instance
        """
        self.network_id = network_id
        self.network_name = network_name
        self.description = description
        self.visible = visible
        self.instance_id = instance_id or str(uuid.uuid4())
        self.node_ids = node_ids or []

    def __eq__(self, other):
        if not isinstance(other, Network):
            return NotImplemented

        return all([
            self.network_id == other.network_id,
            self.network_name == other.network_name,
            self.description == other.description,
            self.visible == other.visible,
            self.node_ids == other.node_ids,
        ])

    def __hash__(self):
        return hash(
            (
                self.network_id,
                self.network_name,
                self.description,
                self.visible,
                tuple(self.node_ids),
            )
        )

    @classmethod
    def from_dict(cls,
                  payload: dict,
                  ) -> 'Network':
        """
        Build a Network object from a dictionary.
        :param payload: The dictionary containing network data
        :return: Network object
        """
        if 'networkId' not in payload or not payload['networkId']:
            payload['networkId'] = str(uuid.uuid4())

        if 'instanceId' not in payload or not payload['instanceId']:
            payload['instanceId'] = str(uuid.uuid4())

        return cls(
            network_id=payload['networkId'],
            network_name=payload['networkName'],
            description=payload['description'],
            node_ids=payload.get('nodeIds', []),
            visible=payload['visible'],
            instance_id=payload['instanceId'],
        )

    def to_dict(self) -> dict:
        """
        Serialise the Network object to a dictionary.
        :return: Dictionary containing network data
        """
        return {
            'networkId': self.network_id,
            'networkName': self.network_name,
            'description': self.description,
            'nodeIds': self.node_ids,
            'visible': self.visible,
            'instanceId': self.instance_id,
        }


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

    async def get(self, network_id: str) -> Network | None:
        """
        Retrieve a network by its ID.
        :param network_id: The ID of the network to retrieve.
        :return: Network object or None if not found.
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
