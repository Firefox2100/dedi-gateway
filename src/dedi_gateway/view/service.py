import json
import asyncio
from quart import Blueprint, websocket, abort

from dedi_gateway.cache import get_active_broker


service_blueprint = Blueprint("service", __name__)


@service_blueprint.websocket("/websocket")
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
