import uuid
from typing import Mapping, Any

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
                 registered: bool = False,
                 instance_id: str = None,
                 central_node: str = None,
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
        :param registered: Whether the network is registered in a public registry
        :param instance_id: The unique ID of the network instance
        :param central_node: The ID of the central node for permission and identity management.
            None if the permission is decentralised.
        """
        self.network_id = network_id
        self.network_name = network_name
        self.description = description
        self.visible = visible
        self.registered = registered
        self.instance_id = instance_id or str(uuid.uuid4())
        self.node_ids = node_ids or []
        self.central_node = central_node

    def __eq__(self, other):
        if not isinstance(other, Network):
            return NotImplemented

        return all([
            self.network_id == other.network_id,
            self.network_name == other.network_name,
            self.description == other.description,
            self.visible == other.visible,
            self.registered == other.registered,
            self.node_ids == other.node_ids,
            self.central_node == other.central_node,
        ])

    def __hash__(self):
        return hash(
            (
                self.network_id,
                self.network_name,
                self.description,
                self.visible,
                self.registered,
                self.central_node,
                tuple(self.node_ids),
            )
        )

    @classmethod
    def from_dict(cls,
                  payload: Mapping[str, Any],
                  ) -> 'Network':
        """
        Build a Network object from a dictionary.
        :param payload: The dictionary containing network data
        :return: Network object
        """
        network_id = payload.get('networkId')
        if not network_id:
            network_id = str(uuid.uuid4())

        instance_id = payload.get('instanceId')
        if not instance_id:
            instance_id = str(uuid.uuid4())

        return cls(
            network_id=network_id,
            network_name=payload['networkName'],
            description=payload['description'],
            node_ids=payload.get('nodeIds', []),
            visible=payload.get('visible', False),
            registered=payload.get('registered', False),
            instance_id=instance_id,
            central_node=payload.get('centralNode', None),
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
            'registered': self.registered,
            'instanceId': self.instance_id,
            'centralNode': self.central_node,
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
