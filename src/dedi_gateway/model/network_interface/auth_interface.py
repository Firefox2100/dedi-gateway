import asyncio
from copy import deepcopy
from uuid import uuid4
from dedi_link.etc.enums import AuthMessageStatus
from dedi_link.model import MessageMetadata, AuthRequest, AuthInvite, AuthRequestResponse, \
    AuthInviteResponse, Node, Network

from dedi_gateway.etc.consts import SERVICE_CONFIG, LOGGER
from dedi_gateway.etc.errors import JoiningNetworkException, InvitingNodeException, \
    NetworkRequestFailedException
from dedi_gateway.etc.powlib import PowDriver
from dedi_gateway.kms import get_active_kms
from dedi_gateway.database import get_active_db
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
        driver = PowDriver()
        challenge = await self._session.raw_get(
            url=f'{target_url}/service/challenge',
        )
        challenge_solution = driver.solve(
            nonce=challenge['nonce'],
            difficulty=challenge['difficulty'],
        )

        # Create a placeholder network
        network = Network(
            network_id=f'pending-{network_id}',
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
        join_response = await self._session.post_message(
            url=f'{target_url}/service/requests',
            network_message=join_request,
        )

        # Store the request in the database
        await db.messages.save_sent_request(
            target_url=target_url,
            request=join_request,
            requires_polling=not join_response.get('reachable', False)
        )

    async def send_join_invite(self,
                               target_url: str,
                               network_id: str,
                               justification: str = None,
                               ):
        """
        Invite another node to join a network this node is part of.
        :param target_url: The URL of the target node to send the invite to
        :param network_id: The ID of the network to invite the node to
        :param justification: Optional justification for inviting the node
        """
        kms = get_active_kms()
        db = get_active_db()

        # Load the network from the database
        network = await db.networks.get(network_id)
        if network.central_node and network.central_node != network.instance_id:
            raise InvitingNodeException(
                f'Network {network_id} has a central node at {network.central_node}, '
                'which is not the current node.'
            )

        # Get and solve the security challenge
        driver = PowDriver()
        challenge = await self._session.raw_get(
            url=f'{target_url}/service/challenge',
        )
        challenge_solution = driver.solve(
            nonce=challenge['nonce'],
            difficulty=challenge['difficulty'],
        )

        # Prepare and send the join invite
        network.node_ids = []
        join_invite = AuthInvite(
            metadata=MessageMetadata(
                network_id=network.network_id,
                node_id=network.instance_id,
            ),
            node=Node(
                node_id=network.instance_id,
                node_name=SERVICE_CONFIG.service_name,
                url=SERVICE_CONFIG.access_url,
                description=SERVICE_CONFIG.service_description,
                public_key=await kms.get_network_node_public_key(network_id=network.network_id),
            ),
            network=network,
            challenge_nonce=challenge['nonce'],
            challenge_solution=challenge_solution,
            management_key={
                'publicKey': await kms.get_network_management_public_key(
                    network_id=network.network_id,
                )
            },
            justification=justification or 'No justification provided',
        )
        if network.central_node is None:
            # Decentralised network, the management key can be shared
            join_invite.management_key['privateKey'] = \
                await kms.get_network_management_private_key(
                    network_id=network.network_id,
                )
        join_response = await self._session.post_message(
            url=f'{target_url}/service/requests',
            network_message=join_invite,
        )

        # Store the request in the database
        await db.messages.save_sent_request(
            target_url=target_url,
            request=join_invite,
            requires_polling=not join_response.get('reachable', False)
        )

    async def process_join_request(self,
                                   request: AuthRequest,
                                   approve: bool,
                                   justification: str = None,
                                   ):
        """
        Process a received join request from another node.
        :param request: The join request to process
        :param approve: Whether to approve or reject the request
        :param justification: Optional justification for the decision
        :return:
        """
        db = get_active_db()
        kms = get_active_kms()
        await db.messages.update_request_status(
            request_id=request.metadata.message_id,
            status=AuthMessageStatus.ACCEPTED if approve else AuthMessageStatus.REJECTED,
        )

        network = await db.networks.get(request.metadata.network_id)
        metadata = MessageMetadata(
            message_id=request.metadata.message_id,
            network_id=request.metadata.network_id,
            node_id=network.instance_id,
        )

        if approve:
            auth_response = AuthRequestResponse(
                metadata=metadata,
                approved=True,
                node=Node(
                    node_id=network.instance_id,
                    node_name=SERVICE_CONFIG.service_name,
                    url=SERVICE_CONFIG.access_url,
                    description=SERVICE_CONFIG.service_description,
                    public_key=await kms.get_network_node_public_key(
                        network_id=request.metadata.network_id,
                    ),
                ),
                network=network,
                justification=justification or 'No justification provided',
                management_key={
                    'publicKey': await kms.get_network_management_public_key(
                        network_id=request.metadata.network_id,
                    )
                }
            )

            if network.central_node is None:
                # Decentralised network, the management key can be shared
                auth_response.management_key['privateKey'] = \
                    await kms.get_network_management_private_key(
                        network_id=request.metadata.network_id,
                    )

            # Save the node to the network
            new_node = deepcopy(request.node)
            new_node.approved = True
            new_node.data_index = {}

            await db.networks.add_node(
                network_id=request.metadata.network_id,
                node=new_node,
            )
        else:
            auth_response = AuthRequestResponse(
                metadata=metadata,
                approved=False,
                justification=justification or 'No justification provided',
            )

        # Try sending the response to the requester
        try:
            await self._session.post_message(
                url=f'{request.node.url}/service/responses',
                network_message=auth_response,
            )

            await asyncio.sleep(1)

            if approve:
                await self.establish_connection(
                    network_id=request.metadata.network_id,
                    node=request.node,
                )
        except NetworkRequestFailedException as e:
            # Sending failed, wait for the requester to poll for the response
            LOGGER.info(
                'Failed to send join request response to %s: %s',
                request.node.url,
                str(e),
            )

    async def process_join_invite(self,
                                  invite: AuthInvite,
                                  approve: bool,
                                  justification: str = None,
                                  ):
        """
        Process a received join invite from another node.
        :param invite: The join invite to process
        :param approve: Whether to approve or reject the invite
        :param justification: The justification for the decision
        :return:
        """
        db = get_active_db()
        kms = get_active_kms()
        await db.messages.update_request_status(
            request_id=invite.metadata.message_id,
            status=AuthMessageStatus.ACCEPTED if approve else AuthMessageStatus.REJECTED,
        )

        network = deepcopy(invite.network)
        network.node_ids = []
        network.instance_id = str(uuid4())
        metadata = MessageMetadata(
            message_id=invite.metadata.message_id,
            network_id=invite.metadata.network_id,
            node_id=network.instance_id,
        )

        if approve:
            await db.networks.save(network)
            await kms.store_network_management_key(
                network_id=network.network_id,
                public_key=invite.management_key['publicKey'],
                private_key=invite.management_key.get('privateKey', None),
            )
            await kms.generate_network_node_key(network.network_id)

            auth_response = AuthInviteResponse(
                metadata=metadata,
                approved=True,
                node=Node(
                    node_id=network.instance_id,
                    node_name=SERVICE_CONFIG.service_name,
                    url=SERVICE_CONFIG.access_url,
                    description=SERVICE_CONFIG.service_description,
                    public_key=await kms.get_network_node_public_key(
                        network_id=invite.metadata.network_id,
                    ),
                ),
                justification=justification or 'No justification provided',
            )

            new_node = deepcopy(invite.node)
            new_node.approved = True
            new_node.data_index = {}

            await db.networks.add_node(
                network_id=invite.metadata.network_id,
                node=new_node,
            )
        else:
            auth_response = AuthInviteResponse(
                metadata=metadata,
                approved=False,
                justification=justification or 'No justification provided',
            )

        # Try sending the response to the inviter
        try:
            await self._session.post_message(
                url=f'{invite.node.url}/service/responses',
                network_message=auth_response,
            )

            await asyncio.sleep(1)

            if approve:
                await self.establish_connection(
                    network_id=invite.metadata.network_id,
                    node=invite.node,
                )
        except NetworkRequestFailedException as e:
            # Sending failed, wait for the requester to poll for the response
            LOGGER.info(
                'Failed to send join request response to %s: %s',
                invite.node.url,
                str(e),
            )
