import json
import asyncio
import secrets
from copy import deepcopy
from quart import Blueprint, Response, request, websocket, abort

from dedi_gateway.etc.consts import SERVICE_CONFIG, LOGGER
from dedi_gateway.etc.enums import MessageType, AuthMessageStatus, ConnectivityType, TransportType
from dedi_gateway.etc.powlib import validate
from dedi_gateway.etc.utils import exception_handler
from dedi_gateway.cache import get_active_broker, get_active_cache
from dedi_gateway.database import get_active_db
from dedi_gateway.kms import get_active_kms
from dedi_gateway.model.node import Node
from dedi_gateway.model.route import Route
from dedi_gateway.model.network_message import AuthRequest, AuthInvite, AuthRequestResponse, \
    AuthInviteResponse, AuthConnect, NetworkMessage, MessageMetadata
from dedi_gateway.model.network_interface import AuthInterface, process_network_message, \
    authenticate_network_message


service_blueprint = Blueprint("service", __name__)


@service_blueprint.route('/status', methods=['GET'])
@exception_handler
async def get_service_status():
    """
    Get the status of the service.
    :return: Current service status
    """
    return {
        'status': 'running',
    }


@service_blueprint.route('/challenge', methods=['GET'])
@exception_handler
async def get_challenge():
    """
    Generate a Proof of Work challenge for request validation.

    This is to prevent spam and abuse of the unprotected endpoints by enforcing a
    CPU cost for each request.
    :return: The nonce and difficulty level for the challenge.
    """
    nonce = secrets.token_hex(16)
    difficulty = SERVICE_CONFIG.challenge_difficulty

    LOGGER.debug(
        'Generating challenge with nonce: %s, difficulty: %d',
        nonce,
        difficulty
    )

    cache = get_active_cache()
    await cache.save_challenge(
        nonce=nonce,
        difficulty=difficulty,
    )

    return {
        'nonce': nonce,
        'difficulty': difficulty
    }, 200


@service_blueprint.route('/networks', methods=['GET'])
@exception_handler
async def get_visible_networks():
    """
    Get a list of visible networks to apply for joining.
    :return: A stripped list of visible networks, with only necessary information.
    """
    db = get_active_db()

    networks = await db.networks.filter(visible=True)
    network_response = []

    for network in networks:
        payload = {
            'networkId': network.network_id,
            'networkName': network.network_name,
            'description': network.description,
            'registered': network.registered,
        }

        if network.central_node:
            # Network has a central permission management node, needs to join from there
            if network.central_node == network.instance_id:
                # This is the central node
                payload['centralUrl'] = SERVICE_CONFIG.access_url
            else:
                central_node = await db.nodes.get(network.central_node)
                payload['centralUrl'] = central_node.url

        network_response.append(payload)

    LOGGER.debug('Returning %d visible networks', len(network_response))

    return network_response


@service_blueprint.route('/requests', methods=['POST'])
@exception_handler
async def submit_request():
    """
    Submit a join request or invite to the service.
    :return:
    """
    data = await request.get_json()
    signature = request.headers.get('Message-Signature')

    if not data:
        abort(400, 'No data provided in request.')
    if not signature:
        abort(400, 'No signature provided in request headers.')

    cache = get_active_cache()
    challenge_nonce = data['challenge']['nonce']
    challenge_solution = data['challenge']['solution']

    challenge_difficulty = await cache.get_challenge(challenge_nonce)

    if not challenge_difficulty:
        abort(403, 'Invalid challenge nonce.')

    if not validate(
        nonce=challenge_nonce,
        difficulty=challenge_difficulty,
        response=challenge_solution,
    ):
        abort(403, 'Invalid challenge solution.')

    message_type = MessageType(data['messageType'])
    db = get_active_db()
    kms = get_active_kms()

    if message_type == MessageType.AUTH_REQUEST:
        # Request to join a network
        auth_request = AuthRequest.from_dict(data)
        if not await kms.verify_signature(
            payload=json.dumps(auth_request.to_dict()),
            public_pem=auth_request.node.public_key,
            signature=signature,
        ):
            abort(403, 'Invalid signature for auth request.')

        await db.messages.save_received_request(
            request=auth_request,
        )

        LOGGER.info(
            'Received auth request from node %s for network %s',
            auth_request.node.node_id,
            auth_request.metadata.network_id,
        )
        LOGGER.debug(
            'Auth request content: %s',
            auth_request.to_dict()
        )

        reachable = await AuthInterface().check_node_connectivity(auth_request.node.url)
    elif message_type == MessageType.AUTH_INVITE:
        # Invite to join a network
        auth_invite = AuthInvite.from_dict(data)
        if not await kms.verify_signature(
            payload=json.dumps(auth_invite.to_dict()),
            public_pem=auth_invite.node.public_key,
            signature=signature,
        ):
            abort(403, 'Invalid signature for auth invite.')

        await db.messages.save_received_request(
            request=auth_invite,
        )

        LOGGER.info(
            'Received auth invite from node %s for network %s',
            auth_invite.node.node_id,
            auth_invite.metadata.network_id,
        )
        LOGGER.debug(
            'Auth invite content: %s',
            auth_invite.to_dict()
        )

        reachable = await AuthInterface().check_node_connectivity(auth_invite.node.url)
    else:
        return abort(400, 'Invalid message type specified.')

    LOGGER.info(
        'Destination node %s with URL %s is reachable: %s',
        data['node']['nodeId'],
        data['node']['nodeUrl'],
        str(reachable),
    )

    return {
        'status': 'success',
        'reachable': reachable,
    }


@service_blueprint.route('/requests/<request_id>', methods=['POST'])
@exception_handler
async def get_request_status(request_id):
    """
    Get the status of a specific join request or invite.

    This is used when the requester node is not reachable, and it shall check the status
    of the request it sent earlier.
    :param request_id: The ID of the request to check.
    :return:
    """
    data = await request.get_json()
    message_id = data.get('messageId')
    challenge_nonce = data.get('challenge')
    signature = request.headers.get('Message-Signature')

    if not message_id or not challenge_nonce:
        abort(400, 'Missing messageId or challenge in request data.')
    if not signature:
        abort(403, 'No signature provided in request headers.')

    db = get_active_db()
    kms = get_active_kms()
    request_payload = await db.messages.get_received_request(request_id)

    if not request_payload:
        abort(404, 'Request not found.')

    request_type = MessageType(request_payload['request']['messageType'])
    request_status = AuthMessageStatus(request_payload['status'])
    if request_type not in (MessageType.AUTH_REQUEST, MessageType.AUTH_INVITE):
        abort(400, 'Invalid request type specified.')

    if request_type == MessageType.AUTH_REQUEST:
        request_obj = AuthRequest.from_dict(request_payload['request'])

        if not await kms.verify_signature(
            payload=json.dumps(request_obj.to_dict()),
            public_pem=request_obj.node.public_key,
            signature=signature,
        ):
            abort(403, 'Invalid signature for auth request.')

        if request_status == AuthMessageStatus.PENDING:
            return {'status': AuthMessageStatus.PENDING.value}
        if request_status == AuthMessageStatus.REJECTED:
            return {'status': AuthMessageStatus.REJECTED.value}
        if request_status == AuthMessageStatus.ACCEPTED:
            # Request accepted, return the auth request response as well
            network = await db.networks.get(request_obj.metadata.network_id)
            auth_response = AuthRequestResponse(
                metadata=MessageMetadata(
                    message_id=request_obj.metadata.message_id,
                    network_id=request_obj.metadata.network_id,
                    node_id=network.instance_id,
                ),
                approved=True,
                node=Node(
                    node_id=network.instance_id,
                    node_name=SERVICE_CONFIG.service_name,
                    url=SERVICE_CONFIG.access_url,
                    description=SERVICE_CONFIG.service_description,
                    public_key=await kms.get_network_node_public_key(
                        network_id=request_obj.metadata.network_id,
                    ),
                ),
                network=network,
                justification='Request accepted, response generated automatically upon polling.',
                management_key={
                    'publicKey': await kms.get_network_management_public_key(
                        network_id=request_obj.metadata.network_id,
                    )
                }
            )

            return {
                'status': AuthMessageStatus.ACCEPTED.value,
                'response': auth_response.to_dict(),
            }
    elif request_type == MessageType.AUTH_INVITE:
        invite_obj = AuthInvite.from_dict(request_payload['request'])

        if not await kms.verify_signature(
            payload=json.dumps(invite_obj.to_dict()),
            public_pem=invite_obj.node.public_key,
            signature=signature,
        ):
            abort(403, 'Invalid signature for auth invite.')

        if request_status == AuthMessageStatus.PENDING:
            return {'status': AuthMessageStatus.PENDING.value}
        if request_status == AuthMessageStatus.REJECTED:
            return {'status': AuthMessageStatus.REJECTED.value}
        if request_status == AuthMessageStatus.ACCEPTED:
            network = await db.networks.get(invite_obj.metadata.network_id)
            auth_response = AuthInviteResponse(
                metadata=MessageMetadata(
                    message_id=invite_obj.metadata.message_id,
                    network_id=invite_obj.metadata.network_id,
                    node_id=network.instance_id,
                ),
                approved=True,
                node=Node(
                    node_id=network.instance_id,
                    node_name=SERVICE_CONFIG.service_name,
                    url=SERVICE_CONFIG.access_url,
                    description=SERVICE_CONFIG.service_description,
                    public_key=await kms.get_network_node_public_key(
                        network_id=invite_obj.metadata.network_id,
                    ),
                ),
                justification='Invitation accepted, response generated automatically upon polling.',
            )

            return {
                'status': AuthMessageStatus.ACCEPTED.value,
                'response': auth_response.to_dict(),
            }


@service_blueprint.route('/responses', methods=['POST'])
@exception_handler
async def submit_response():
    """
    Submit a response to a join request or invite.

    This is used for this node to know that the other party has processed the request
    :return:
    """
    data = await request.get_json()

    if not data:
        abort(400, 'No data provided in request.')

    db = get_active_db()
    kms = get_active_kms()

    request_id = data['metadata']['messageId']
    sent_request = await db.messages.get_sent_request(request_id)

    sent_request_type = MessageType(sent_request['request']['messageType'])
    response_type = MessageType(data['messageType'])

    if sent_request_type == MessageType.AUTH_REQUEST and \
            response_type == MessageType.AUTH_REQUEST_RESPONSE:
        request_obj = AuthRequest.from_dict(sent_request['request'])
        response_obj = AuthRequestResponse.from_dict(data)
        local_network = await db.networks.get(f'pending-{request_obj.metadata.network_id}')
        # Compare the network information and update the local network placeholder
        if not all([
            local_network.network_name == response_obj.network.network_name,
            local_network.description == response_obj.network.description,
            local_network.registered == response_obj.network.registered,
        ]):
            # Data mismatch
            abort(400, 'Response data does not match the original request.')

        if response_obj.approved:
            local_network.central_node = response_obj.network.central_node
            local_network.visible = response_obj.network.visible
            local_network.network_id = response_obj.network.network_id
            new_node = deepcopy(response_obj.node)
            new_node.data_index = {}
            new_node.score = 0
            new_node.approved = True

            await db.networks.save(local_network)
            await db.networks.add_node(
                network_id=local_network.network_id,
                node=new_node,
            )

            await kms.store_network_management_key(
                network_id=local_network.network_id,
                public_key=response_obj.management_key['publicKey'],
                private_key=response_obj.management_key.get('privateKey', None),
            )

        await db.networks.delete(f'pending-{request_obj.metadata.network_id}')
        await db.messages.update_request_status(
            request_id=request_id,
            status=AuthMessageStatus.ACCEPTED \
                if response_obj.approved else AuthMessageStatus.REJECTED,
        )
    elif sent_request_type == MessageType.AUTH_INVITE and \
            response_type == MessageType.AUTH_INVITE_RESPONSE:
        request_obj = AuthInvite.from_dict(sent_request['request'])
        response_obj = AuthInviteResponse.from_dict(data)
        local_network = await db.networks.get(request_obj.metadata.network_id)

        if response_obj.approved:
            new_node = deepcopy(response_obj.node)
            new_node.data_index = {}
            new_node.score = 0
            new_node.approved = True

            await db.networks.add_node(
                network_id=local_network.network_id,
                node=new_node,
            )

        await db.messages.update_request_status(
            request_id=request_id,
            status=AuthMessageStatus.ACCEPTED \
                if response_obj.approved else AuthMessageStatus.REJECTED,
        )
    else:
        abort(400, 'Invalid message type specified for response.')

    return {
        'status': 'success',
    }


@service_blueprint.websocket('/websocket')
@exception_handler
async def service_websocket():
    """
    WebSocket endpoint for server-to-server communication.
    Accepts functional messages from other servers.
    """
    broker = get_active_broker()
    cache = get_active_cache()

    try:
        auth_connect_string = await websocket.receive()
        auth_connect_data = json.loads(auth_connect_string)
        auth_connect_message = AuthConnect.from_dict(auth_connect_data['message'])

        if not await authenticate_network_message(
            message=auth_connect_message,
            signature=auth_connect_data['signature'],
        ):
            await websocket.send(json.dumps({
                'error': 'Authentication failed for WebSocket connection.'
            }))
            abort(403, 'Authentication failed for WebSocket connection.')
    except json.decoder.JSONDecodeError:
        await websocket.send(json.dumps({
            'error': 'Invalid JSON format in bootstrap message.'
        }))
        abort(400, 'Invalid JSON format in bootstrap message.')

    pong_event = asyncio.Event()
    pong_event.set()

    LOGGER.info(
        'Received WebSocket connection from node %s',
        auth_connect_message.metadata.node_id
    )
    await cache.save_route(
        route=Route(
            network_id=auth_connect_message.metadata.network_id,
            node_id=auth_connect_message.metadata.node_id,
            connectivity_type=ConnectivityType.DIRECT,
            transport_type=TransportType.WEBSOCKET,
        )
    )

    async def send_loop():
        while True:
            try:
                message = await broker.get_message(auth_connect_message.metadata.node_id)

                if not message:
                    # Ping the client and wait for pong
                    pong_event.clear()
                    LOGGER.debug(
                        'Pinging client for node %s',
                        auth_connect_message.metadata.node_id
                    )
                    await websocket.send(json.dumps({'ping': True}))

                    try:
                        await asyncio.wait_for(pong_event.wait(), timeout=10)
                    except asyncio.TimeoutError:
                        await websocket.send(json.dumps({'error': 'Pong timeout'}))
                        abort(408, 'Client did not respond to ping')
                else:
                    await pong_event.wait()
                    LOGGER.info(
                        'Sending message %s to node %s',
                        message['message']['metadata']['messageId'],
                        auth_connect_message.metadata.node_id
                    )
                    LOGGER.debug('Message content: %s', message)
                    await websocket.send(json.dumps(message))

                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                LOGGER.info(
                    'Send loop cancelled for node %s',
                    auth_connect_message.metadata.node_id
                )
                raise
            except Exception:
                abort(500, 'An error occurred while processing the message.')

    async def receive_loop():
        while True:
            try:
                client_message = await websocket.receive()
                try:
                    data = json.loads(client_message)
                    LOGGER.info(
                        'Received message from node %s',
                        auth_connect_message.metadata.node_id
                    )
                    LOGGER.debug('Message content: %s', data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({'error': 'Invalid JSON format'}))
                    continue

                if data.get('pong'):
                    pong_event.set()
                    LOGGER.debug(
                        'Received pong from node %s',
                        auth_connect_message.metadata.node_id
                    )
                    continue

                signature = data['signature']
                message = NetworkMessage.factory(data['message'])

                if not await authenticate_network_message(
                    message=message,
                    signature=signature,
                ):
                    await websocket.send(json.dumps({'error': 'Authentication failed'}))
                    continue

                await process_network_message(message)
            except asyncio.CancelledError:
                LOGGER.info(
                    'Receive loop cancelled for node %s',
                    auth_connect_message.metadata.node_id
                )
                raise
            except Exception as e:
                await websocket.send(
                    json.dumps({'error': f'Unhandled error receiving message: {str(e)}'})
                )
                LOGGER.exception(
                    'Unhandled error receiving message from node %s',
                    auth_connect_message.metadata.node_id
                )

    send_task = asyncio.create_task(send_loop())
    receive_task = asyncio.create_task(receive_loop())

    try:
        await asyncio.gather(send_task, receive_task)
    except asyncio.CancelledError:
        send_task.cancel()
        receive_task.cancel()
        await websocket.close(1000)
        raise
    finally:
        LOGGER.info(
            'WebSocket connection closed for node %s',
            auth_connect_message.metadata.node_id
        )
        await cache.delete_route(
            node_id=auth_connect_message.metadata.node_id,
        )


@service_blueprint.route('/message', methods=['POST'])
@exception_handler
async def handle_message():
    """
    Handle incoming messages from other nodes.

    This is used together with the SSE endpoint, where a client subscribes
    to this node to receive real-time updates, while using this endpoint to
    submit messages to the node.
    :return:
    """
    data = await request.get_json()
    signature = request.headers.get('Message-Signature')

    if not data:
        abort(400, 'No data provided in request.')
    if not signature:
        abort(400, 'No signature provided in request headers.')

    network_message = NetworkMessage.factory(data)
    if not await authenticate_network_message(
        message=network_message,
        signature=signature,
    ):
        abort(403, 'Authentication failed for incoming message.')

    LOGGER.info(
        'Received message %s from node %s',
        network_message.metadata.message_id,
        network_message.metadata.node_id
    )
    LOGGER.debug('Message content: %s', network_message.to_dict())

    await process_network_message(data)


@service_blueprint.route('/event', methods=['POST'])
@exception_handler
async def handle_sse():
    """
    Handle Server-Sent Events (SSE) for real-time updates.

    This is the fallback method for connections that do not support WebSockets.
    :return:
    """
    data = await request.get_json()
    if not data:
        abort(400, 'No data provided in request.')

    auth_connect_message = AuthConnect.from_dict(data)
    signature = request.headers.get('Message-Signature')

    if not await authenticate_network_message(
        message=auth_connect_message,
        signature=signature,
    ):
        abort(403, 'Authentication failed for SSE connection.')

    LOGGER.info(
        'Received SSE connection from node %s',
        auth_connect_message.metadata.node_id
    )
    cache = get_active_cache()
    await cache.save_route(
        route=Route(
            network_id=auth_connect_message.metadata.network_id,
            node_id=auth_connect_message.metadata.node_id,
            connectivity_type=ConnectivityType.DIRECT,
            transport_type=TransportType.SSE,
        )
    )

    async def event_stream():
        broker = get_active_broker()
        try:
            while True:
                message = await broker.get_message(auth_connect_message.metadata.node_id)

                if message:
                    LOGGER.info(
                        'Sending message %s to node %s via SSE',
                        message['metadata']['messageId'],
                        auth_connect_message.metadata.node_id
                    )
                    yield f"data: {json.dumps(message)}\n\n"
                else:
                    # Ping the client and wait for pong
                    LOGGER.debug(
                        'Pinging client for node %s via SSE',
                        auth_connect_message.metadata.node_id
                    )
                    yield "event: ping\ndata: {}\n\n"

                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            LOGGER.info(
                'Event stream cancelled for node %s',
                auth_connect_message.metadata.node_id
            )
            raise
        except Exception as e:
            LOGGER.exception(
                'Unhandled error in event stream for node %s: %s',
                auth_connect_message.metadata.node_id,
                str(e)
            )
            yield f"data: {{'error': '{str(e)}'}}\n\n"
        finally:
            LOGGER.info(
                'Node %s disconnected from SSE event stream',
                auth_connect_message.metadata.node_id
            )
            await cache.delete_route(
                node_id=auth_connect_message.metadata.node_id,
            )

    return Response(event_stream(), content_type='text/event-stream')
