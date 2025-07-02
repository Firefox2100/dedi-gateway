import time
from uuid import uuid4

from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.errors import JoiningNetworkException
from dedi_gateway.etc.powlib import solve
from dedi_gateway.kms import get_active_kms
from dedi_gateway.database import get_active_db
from ..network_message import MessageMetadata, AuthRequest
from ..network import Network
from ..node import Node
from .network_interface import NetworkInterface


class AuthInterface(NetworkInterface):
    """
    A utility interface to handle authentication and authorisation related operations.
    """
    async def send_join_request(self,
                                target_url: str,
                                network_id: str,
                                justification: str = None,
                                ):
        """
        Request to join a network from a node.
        :param target_url: The URL of the target node to send the request to
        :param network_id: The ID of the network to join
        :param justification: Optional justification for joining the network
        :return:
        """
        kms = get_active_kms()
        db = get_active_db()

        # Retrieve the network information from target server
        visible_networks = await self._session.raw_get(
            url=f'{target_url}/service/networks',
        )
        target_network = next(
            (net for net in visible_networks if net['networkId'] == network_id),
            None,
        )

        if not target_network:
            raise JoiningNetworkException(
                f'Network with ID {network_id} not found on {target_url}',
                404,
            )
        if 'centralUrl' in target_network:
            # Network has a central permission management node
            if target_network['centralUrl'] != target_url:
                raise JoiningNetworkException(
                    f'Network with ID {network_id} is managed by a central node '
                    f'at {target_network["centralUrl"]}, '
                    f'but the request was sent to {target_url}.'
                )

        # Get and solve the security challenge
        challenge = await self._session.raw_get(
            url=f'{target_url}/service/challenge',
        )
        challenge_solution = solve(
            nonce=challenge['nonce'],
            difficulty=challenge['difficulty'],
        )

        # Create a placeholder network
        network = Network(
            network_id=network_id,
            network_name=target_network['networkName'],
            description=target_network['description'],
            visible=True,
            registered=target_network['registered'],
            instance_id=str(uuid4()),
        )
        await db.networks.save(network)
        network_public_key = await kms.generate_network_node_key(
            network_id=network_id,
        )

        # Prepare and send the join request
        join_request = AuthRequest(
            metadata=MessageMetadata(
                network_id=network_id,
                node_id=network.instance_id,
                message_id=str(uuid4()),
                timestamp=time.time(),
            ),
            node=Node(
                node_id=network.instance_id,
                node_name=SERVICE_CONFIG.service_name,
                url=SERVICE_CONFIG.access_url,
                description=SERVICE_CONFIG.service_description,
                public_key=network_public_key,
            ),
            challenge_nonce=challenge['nonce'],
            challenge_solution=challenge_solution,
            justification=justification or 'No justification provided',
        )
        join_response = await self._session.raw_post(
            url=f'{target_url}/service/requests',
            json=join_request.to_dict(),
        )

        # Store the request in the database
        await db.messages.save_sent_request(
            target_url=target_url,
            request=join_request,
            requires_polling=not join_response.get('reachable', False)
        )
