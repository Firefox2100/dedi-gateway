from quart import Blueprint, request

from dedi_gateway.etc.enums import AuthMessageStatus
from dedi_gateway.etc.utils import exception_handler
from dedi_gateway.kms import get_active_kms
from dedi_gateway.database import get_active_db
from dedi_gateway.model import Network
from dedi_gateway.model.network_interface import AuthInterface

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
        return {'error': 'No data provided'}, 400

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
        return {'error': 'No data provided'}, 400

    auth_interface = AuthInterface()
    await auth_interface.send_join_request(
        target_url=data['targetUrl'],
        network_id=data['networkId'],
        justification=data.get('justification', None)
    )

    return {'message': 'Join request sent successfully'}, 202


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
        return {'error': 'No data provided'}, 400

    db = get_active_db()
    network = await db.networks.get(network_id)

    if not network:
        return {'error': 'Network not found'}, 404

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
    :return:
    """
    db = get_active_db()

    sent = request.args.get('sent', None)
    status = request.args.getlist('status')

    auth_requests = await db.messages.get_requests(
        sent=sent,
        status=[AuthMessageStatus(s) for s in status] if status else None,
    )

    return auth_requests
