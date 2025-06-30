from quart import Blueprint, request

from dedi_gateway.database import get_active_db
from dedi_gateway.model import Network
from .utils import exception_handler

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
    centralised = request.args.get('centralised', None)
    if centralised is not None:
        centralised = centralised.lower() == 'true'
    registered = request.args.get('registered', None)
    if registered is not None:
        registered = registered.lower() == 'true'

    db = get_active_db()
    networks = await db.networks.filter(
        visible=visible,
        centralised=centralised,
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

    db = get_active_db()
    await db.networks.save(network)

    return network.to_dict(), 201


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
