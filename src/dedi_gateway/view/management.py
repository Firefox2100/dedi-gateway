from quart import Blueprint, request, abort

from dedi_gateway.etc.consts import LOGGER
from dedi_gateway.etc.errors import MessageBrokerTimeoutException
from dedi_gateway.etc.enums import AuthMessageStatus, MessageType
from dedi_gateway.etc.utils import exception_handler
from dedi_gateway.cache import get_active_broker
from dedi_gateway.kms import get_active_kms
from dedi_gateway.database import get_active_db
from dedi_gateway.model.network import Network
from dedi_gateway.model.network_message import AuthRequest, AuthInvite, NetworkMessageRegistry, \
    MessageMetadata, CustomMessage
from dedi_gateway.model.network_interface import NetworkInterface, AuthInterface

management_blueprint = Blueprint('management', __name__)


@management_blueprint.route('/networks', methods=['GET'])
@exception_handler
async def get_networks():
    """
    Retrieve a list of networks.
    :return: A JSON list of networks.
    """
    visible = request.args.get('visible', None)
    if visible is not None:
        visible = visible.lower() == 'true'
    registered = request.args.get('registered', None)
    if registered is not None:
        registered = registered.lower() == 'true'

    db = get_active_db()
    networks = await db.networks.filter(
        visible=visible,
        registered=registered
    )

    return [network.to_dict() for network in networks]


@management_blueprint.route('/networks', methods=['POST'])
@exception_handler
async def create_network():
    """
    Create a new network.
    :return: A JSON representation of the created network.
    """
    data = await request.get_json()
    if not data:
        abort(400, 'No data provided')

    network = Network.from_dict(data)

    if network.central_node:
        if network.central_node != network.instance_id:
            return {
                'error': f'Network with central node {network.central_node} cannot be created. '
                          'Central node must be the same as the instance ID.'
            }

    db = get_active_db()
    kms = get_active_kms()
    await db.networks.save(network)
    await kms.generate_network_management_key(network.network_id)
    await kms.generate_network_node_key(network.network_id)

    return network.to_dict(), 201


@management_blueprint.route('/networks/join', methods=['POST'])
@exception_handler
async def join_network():
    """
    Request to join a network on another node.
    :return:
    """
    data = await request.get_json()

    if not data:
        abort(400, 'No data provided')

    auth_interface = AuthInterface()
    await auth_interface.send_join_request(
        target_url=data['targetUrl'],
        network_id=data['networkId'],
        justification=data.get('justification', None)
    )

    return {'message': 'Join request sent successfully'}, 202


@management_blueprint.route('/networks/invite', methods=['POST'])
@exception_handler
async def invite_to_network():
    """
    Invite a node to join a network.
    :return:
    """
    data = await request.get_json()

    if not data:
        return {'error': 'No data provided'}, 400

    auth_interface = AuthInterface()
    await auth_interface.send_join_invite(
        target_url=data['targetUrl'],
        network_id=data['networkId'],
        justification=data.get('justification', None)
    )

    return {'message': 'Network invitation sent successfully'}, 202


@management_blueprint.route('/networks/<network_id>', methods=['GET'])
@exception_handler
async def get_network(network_id):
    """
    Retrieve a network by its ID.
    :param network_id: The ID of the network to retrieve.
    :return: A JSON representation of the network.
    """
    db = get_active_db()
    network = await db.networks.get(network_id)

    if not network:
        return {'error': 'Network not found'}, 404

    return network.to_dict()


@management_blueprint.route('/networks/<network_id>', methods=['PATCH'])
@exception_handler
async def update_network(network_id):
    """
    Update an existing network.
    :param network_id: The ID of the network to update.
    :return: A JSON representation of the updated network.
    """
    data = await request.get_json()
    if not data:
        abort(400, 'No data provided')

    db = get_active_db()
    network = await db.networks.get(network_id)

    if not network:
        abort(404, 'Network not found')

    for key, value in data.items():
        setattr(network, key, value)

    await db.networks.update(network)

    return network.to_dict()


@management_blueprint.route('/networks/<network_id>', methods=['DELETE'])
@exception_handler
async def delete_network(network_id):
    """
    Delete a network by its ID.
    :param network_id: The ID of the network to delete.
    :return: A success message.
    """
    db = get_active_db()
    await db.networks.delete(network_id)

    return {'message': 'Network deleted successfully'}, 204


@management_blueprint.route('/requests', methods=['GET'])
@exception_handler
async def get_network_requests():
    """
    Retrieve a list of join requests or invites, both sent and received.

    Filters can be applied to show only sent or received requests, pending
    or accepted requests, etc.
    :return: A JSON list of network requests and their statuses.
    """
    db = get_active_db()

    sent = request.args.get('sent', None)
    status = request.args.getlist('status')

    auth_requests = await db.messages.get_requests(
        sent=sent,
        status=[AuthMessageStatus(s) for s in status] if status else None,
    )

    return auth_requests


@management_blueprint.route('/requests/<request_id>', methods=['PATCH'])
@exception_handler
async def respond_to_request(request_id):
    """
    Respond to a join request or invite.
    :param request_id: The ID of the request to respond to.
    :return: A success message.
    """
    data = await request.get_json()
    if not data:
        abort(400, 'No data provided')

    db = get_active_db()
    auth_request = await db.messages.get_received_request(request_id)

    if auth_request['status'] != AuthMessageStatus.PENDING.value:
        return {'error': 'Request has already been processed'}, 400

    message_payload = auth_request['request']
    message_type = MessageType(message_payload['messageType'])
    auth_interface = AuthInterface()

    if message_type == MessageType.AUTH_REQUEST:
        request_obj = AuthRequest.from_dict(message_payload)
        await auth_interface.process_join_request(
            request=request_obj,
            approve=data.get('approve', False),
            justification=data.get('justification', None)
        )

        return {'message': 'Join request processed successfully'}, 200
    elif message_type == MessageType.AUTH_INVITE:
        invite_obj = AuthInvite.from_dict(message_payload)
        await auth_interface.process_join_invite(
            invite=invite_obj,
            approve=data.get('approve', False),
            justification=data.get('justification', None)
        )

        return {'message': 'Invite processed successfully'}, 200

    abort(400, 'Invalid request type')


@management_blueprint.route('/messages', methods=['POST'])
@exception_handler
async def send_message():
    """
    Send a message over the decentralised network.
    :return:
    """
    data = await request.get_json()
    if not data:
        abort(400, 'No data provided')

    message_payload = data['message']
    broadcast = data.get('broadcast', False)
    target_node = data.get('targetNode', None)

    try:
        message_type = MessageType(message_payload['messageType'])
        abort(400, f'Internal message type {message_type} cannot be sent directly.')
    except ValueError:
        pass

    message_registry = NetworkMessageRegistry()
    broker = get_active_broker()
    db = get_active_db()
    network_interface = NetworkInterface()
    message_config = message_registry.get_configuration(message_payload['messageType'])

    if not message_config:
        abort(400, f'Unknown message type {message_payload["messageType"]}.')

    message = CustomMessage.from_dict(message_payload)
    node = await db.nodes.get(target_node)

    if not node.approved:
        abort(403, f'Node {node.node_id} is not approved to communicate.')

    if broadcast:
        messages_sent = await network_interface.broadcast_message(
            message=message,
        )
    elif target_node:
        await network_interface.send_message(
            message=message,
            node=node,
        )
        messages_sent = 1
    else:
        abort(400, 'Either broadcast or targetNode must be specified.')

    responses = []
    try:
        async for rsp in broker.response_generator(
            message_id=message.metadata.message_id,
            message_count=messages_sent,
        ):
            responses.append(rsp)
    except MessageBrokerTimeoutException:
        LOGGER.warning(
            'Message %s received less responses than expected before timeout'
        )

    return {
        'deliveredCount': messages_sent,
        'responses': responses,
    }
