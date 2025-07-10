import json

from dedi_gateway.database import get_active_db
from dedi_gateway.cache import get_active_broker
from dedi_gateway.kms import get_active_kms
from ..network_message import NetworkMessage, MessageMetadata, CustomMessage, NetworkMessageRegistry
from .network_interface import NetworkInterface, NetworkDriver, authenticate_network_message
from .auth_interface import AuthInterface
from .sync_interface import SyncInterface


_proxy_driver = NetworkDriver()


async def process_network_message(message: NetworkMessage):
    """
    Handler for incoming network messages.
    :return:
    """
    db = get_active_db()
    broker = get_active_broker()
    kms = get_active_kms()

    if isinstance(message, CustomMessage):
        message_registry = NetworkMessageRegistry()
        message_config = message_registry.get_configuration(message.message_type)

        if message_config.preceding:
            # This message is a response to another message, no need to proxy it
            await broker.add_to_response(message.to_dict())
        else:
            rsp = await _proxy_driver.raw_post(
                url=message_config.destination,
                payload=message.message_data,
                headers=message.message_header
            )

            if not message_config.asynchronous and message_config.response:
                # Response is needed, generate response message
                network = await db.networks.get(message.metadata.network_id)

                response_message = CustomMessage(
                    metadata=MessageMetadata(
                        network_id=message.metadata.network_id,
                        node_id=network.instance_id,
                        message_id=message.metadata.message_id,
                    ),
                    message_type=message_config.response,
                    message_data=rsp
                )

                await broker.publish_message(
                    node_id=message.metadata.node_id,
                    message={
                        'message': response_message.to_dict(),
                        'signature': await kms.sign_payload(
                            payload=json.dumps(response_message.to_dict()),
                            network_id=response_message.metadata.network_id,
                        ),
                    }
                )
