import json
import time
import asyncio
import secrets
from quart import Blueprint, request, websocket, abort

from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.enums import MessageType
from dedi_gateway.etc.powlib import validate
from dedi_gateway.cache import get_active_broker, get_active_cache
from dedi_gateway.database import get_active_db
from dedi_gateway.model.network_message import AuthRequest, AuthInvite
from dedi_gateway.model.network_interface import AuthInterface


service_blueprint = Blueprint("service", __name__)


@service_blueprint.route('/status', methods=['GET'])
async def get_service_status():
    """
    Get the status of the service.
    :return: Current service status
    """
    return {
        'status': 'running',
    }


@service_blueprint.route('/challenge', methods=['GET'])
async def get_challenge():
    """
    Generate a Proof of Work challenge for request validation.

    This is to prevent spam and abuse of the unprotected endpoints by enforcing a
    CPU cost for each request.
    :return: The nonce and difficulty level for the challenge.
    """
    nonce = secrets.token_hex(16)
    difficulty = SERVICE_CONFIG.challenge_difficulty
    timestamp = int(time.time())

    cache = get_active_cache()
    await cache.store_challenge(
        nonce=nonce,
        difficulty=difficulty,
        timestamp=timestamp,
    )

    return {
        'nonce': nonce,
        'difficulty': difficulty
    }, 200


@service_blueprint.route('/networks', methods=['GET'])
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

    return network_response


@service_blueprint.route('/requests', methods=['POST'])
async def submit_request():
    """
    Submit a join request or invite to the service.
    :return:
    """
    data = await request.get_json()

    if not data:
        abort(400, 'No data provided in request.')

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

    if message_type == MessageType.AUTH_REQUEST:
        # Request to join a network
        auth_request = AuthRequest.from_dict(data)
        await db.messages.save_received_request(
            request=auth_request,
        )

        reachable = await AuthInterface().check_node_connectivity(auth_request.node.url)
    elif message_type == MessageType.AUTH_INVITE:
        # Invite to join a network
        auth_invite = AuthInvite.from_dict(data)
        await db.messages.save_received_request(
            request=auth_invite,
        )

        reachable = await AuthInterface().check_node_connectivity(auth_invite.node.url)
    else:
        return abort(400, 'Invalid message type specified.')

    return {
        'status': 'success',
        'reachable': reachable,
    }


@service_blueprint.websocket('/websocket')
async def service_websocket():
    """
    WebSocket endpoint for server-to-server communication.
    Accepts functional messages from other servers.
    """
    broker = get_active_broker()

    try:
        bootstrap_string = await websocket.receive()
        bootstrap_message = json.loads(bootstrap_string)

        node_id = bootstrap_message.get('nodeId')
    except json.decoder.JSONDecodeError:
        await websocket.send(json.dumps({
            'error': 'Invalid JSON format in bootstrap message.'
        }))
        abort(400, 'Invalid JSON format in bootstrap message.')

    pong_event = asyncio.Event()
    pong_event.set()

    async def send_loop():
        while True:
            try:
                message = await broker.get_message(node_id)

                if not message:
                    # Ping the client and wait for pong
                    pong_event.clear()
                    await websocket.send(json.dumps({'ping': True}))

                    try:
                        await asyncio.wait_for(pong_event.wait(), timeout=10)
                    except asyncio.TimeoutError:
                        await websocket.send(json.dumps({'error': 'Pong timeout'}))
                        abort(408, 'Client did not respond to ping')
                else:
                    await pong_event.wait()
                    await websocket.send(json.dumps(message))

                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                raise
            except Exception:
                abort(500, 'An error occurred while processing the message.')

    async def receive_loop():
        while True:
            try:
                client_message = await websocket.receive()
                try:
                    data = json.loads(client_message)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({'error': 'Invalid JSON format'}))
                    continue

                if data.get('pong'):
                    pong_event.set()
                    continue

                #TODO: Implement the actual message handling logic
                # await handle_client_message(node_id, data)
            except asyncio.CancelledError:
                raise
            except Exception:
                await websocket.send(json.dumps({'error': 'Unhandled error receiving message'}))

    send_task = asyncio.create_task(send_loop())
    receive_task = asyncio.create_task(receive_loop())

    try:
        await asyncio.gather(send_task, receive_task)
    except asyncio.CancelledError:
        send_task.cancel()
        receive_task.cancel()
        await websocket.close(1000)
        raise
