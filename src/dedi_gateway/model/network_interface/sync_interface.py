from copy import deepcopy
from dedi_link.etc.enums import SyncRequestType
from dedi_link.model import NetworkMessage, MessageMetadata, SyncIndex, SyncNode, SyncRequest, \
    Node

from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.database import get_active_db
from dedi_gateway.cache import get_active_broker
from dedi_gateway.kms import get_active_kms
from .network_interface import NetworkInterface


class SyncInterface(NetworkInterface):
    """
    A utility interface to handle state synchronisation related operations.
    """
    async def sync_known_nodes(self,
                               network_id: str,
                               ):
        """
        Send a message including all known nodes in the network to the entire network.
        :param network_id: The ID of the network to synchronise.
        """
        db = get_active_db()
        kms = get_active_kms()
        network = await db.networks.get(network_id)
        known_nodes = await db.networks.get_nodes(network_id)

        # Add this node itself
        known_nodes.append(Node(
            node_id=network.instance_id,
            node_name=SERVICE_CONFIG.service_name,
            url=SERVICE_CONFIG.access_url,
            description=SERVICE_CONFIG.service_description,
            public_key=await kms.get_network_node_public_key(network_id=network.network_id),
        ))

        # Strip all data index and other volatile fields
        known_nodes = list(known_nodes)
        for n in known_nodes:
            n.data_index = None
            n.approved = False

        # Send the message
        sync_message = SyncNode(
            metadata=MessageMetadata(
                network_id=network_id,
                node_id=network.instance_id,
            ),
            nodes=known_nodes,
        )

        await self.broadcast_message(
            message=sync_message,
        )

    async def process_node_sync_message(self,
                                        message: SyncNode,
                                        ):
        """
        Process a SyncNode message to update the known nodes in the network.
        :param message: The SyncNode message containing the nodes to synchronise.
        """
        db = get_active_db()
        broker = get_active_broker()
        known_nodes = await db.networks.get_nodes(message.metadata.network_id)
        network = await db.networks.get(message.metadata.network_id)

        for new_node in message.nodes:
            if new_node.node_id == network.instance_id:
                # Skip processing for the current node itself
                continue

            # Check if the node already exists
            existing_node = next((n for n in known_nodes if n.node_id == new_node.node_id), None)
            if existing_node and existing_node != new_node:
                if existing_node.node_id != message.metadata.node_id:
                    # Attempt to retrieve the latest data from that specific node
                    sync_request = SyncRequest(
                        metadata=MessageMetadata(
                            network_id=message.metadata.network_id,
                            node_id=message.metadata.node_id,
                        ),
                        target=SyncRequestType.INSTANCE,
                    )

                    await self.send_message(
                        message=sync_request,
                        node=existing_node,
                    )
                    results = [
                        rsp async for rsp in broker.response_generator(
                            sync_request.metadata.message_id
                        )
                    ]
                    node_sync_response = SyncNode.from_dict(results[0])
                    n = deepcopy(node_sync_response.nodes[0])
                    n.approved = existing_node.approved
                else:
                    n = deepcopy(new_node)
                    n.approved = existing_node.approved

                await db.nodes.update(n)
            elif not existing_node:
                # New node, add it to the database
                n = deepcopy(new_node)
                n.approved = False
                n.data_index = {}

                await db.networks.add_node(
                    network_id=message.metadata.network_id,
                    node=n,
                )

    async def sync_data_index(self,
                              network_id: str,
                              ):
        """
        Send a message to synchronise the data index across all nodes in the network.
        :param network_id: The ID of the network to synchronise.
        """
        db = get_active_db()
        data_index = await db.get_data_index()

        sync_message = SyncIndex(
            metadata=MessageMetadata(
                network_id=network_id,
                node_id=SERVICE_CONFIG.instance_id,
            ),
            data_index=data_index,
        )

        await self.broadcast_message(
            message=sync_message,
        )

    async def process_data_index_sync_message(self,
                                              message: SyncIndex,
                                              ):
        """
        Process a SyncIndex message to update the data index in the database.
        :param message: The SyncIndex message containing the data index to synchronise.
        """
        db = get_active_db()
        node = await db.nodes.get(message.metadata.node_id)
        node.data_index = message.data_index

        await db.nodes.update(node)

    async def process_sync_message(self,
                                   message: NetworkMessage,
                                   ):
        """
        Generic interface to route the message to the appropriate handler based on its type.
        :param message: The network message to process.
        """
        if isinstance(message, SyncNode):
            await self.process_node_sync_message(message)
        elif isinstance(message, SyncIndex):
            await self.process_data_index_sync_message(message)
        else:
            raise ValueError(f"Unsupported sync message type: {message.message_type}")
