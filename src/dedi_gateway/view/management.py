from quart import Blueprint, request

from dedi_gateway.database import get_active_db
from dedi_gateway.model import Network

management_blueprint = Blueprint('management', __name__)


@management_blueprint.route('/networks', methods=['GET'])
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
