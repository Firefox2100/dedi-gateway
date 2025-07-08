import asyncio
import socket
import ipaddress
import json
import time
from urllib.parse import urlparse
from typing import AsyncGenerator
import httpx
import websockets

from dedi_gateway.etc.consts import LOGGER
from dedi_gateway.etc.enums import ConnectivityType, TransportType
from dedi_gateway.etc.errors import NetworkRequestFailedException, NodeNotFoundException, \
    NodeNotApprovedException
from dedi_gateway.cache import get_active_broker, get_active_cache
from dedi_gateway.database import get_active_db
from dedi_gateway.kms import get_active_kms
from dedi_gateway.model.node import Node
from dedi_gateway.model.route import Route
from dedi_gateway.model.network_message import NetworkMessage, AuthConnect, MessageMetadata


async def authenticate_network_message(message: NetworkMessage,
                                       signature: str | None = None,
                                       ):
    """
    Authenticate the incoming network message.
    :param message: The network message to authenticate.
    :param signature: The signature of the message, if available.
    :return: True if authentication is successful, False otherwise.
    """
    from dedi_gateway.kms import get_active_kms
    from dedi_gateway.database import get_active_db

    network_id = message.metadata.network_id
    sender_id = message.metadata.node_id
    db = get_active_db()
    kms = get_active_kms()

    # Check if the node is registered and enabled
    network_nodes = await db.networks.get_nodes(network_id)
    node = None
    for n in network_nodes:
        if n.node_id == sender_id:
            node = n
            break

    if not node:
        raise NodeNotFoundException(
            f'Node with ID {sender_id} not found in network {network_id}.'
        )
    if not node.approved:
        raise NodeNotApprovedException(
            f'Node with ID {sender_id} is not approved in network {network_id}.'
        )

    # Verify the signature of the message
    return await kms.verify_signature(
        payload=json.dumps(message.to_dict()),
        public_pem=node.public_key,
        signature=signature,
    )


class NetworkDriver:
    """
    A utility class to handle network requests
    """
    def __init__(self,
                 client: httpx.AsyncClient = None,
                 ):
        if client is not None:
            self._client = client
        else:
            self._client = httpx.AsyncClient(
                headers={
                    'Content-Type': 'application/json',
                },
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """
        Close the internal client
        """
        await self._client.aclose()

    async def check_connectivity(self,
                                 url: str,
                                 ) -> bool:
        """
        Perform a connectivity check to a given URL.
        :param url: The URL to dial back at
        :return: True if the dial-back was successful, False otherwise
        """
        try:
            LOGGER.debug('Checking connectivity to URL: %s', url)
            # Parse the URL first
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                # Reachability check only for HTTP/HTTPS URLs
                raise ValueError(f'Invalid URL scheme: {parsed.scheme}')

            host = parsed.hostname
            # Check if the host is a local IP or a loopback address
            addresses = socket.getaddrinfo(host, None)
            for family, _, _, _, sockaddr in addresses:
                ip = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private or \
                        ip_obj.is_loopback or \
                        ip_obj.is_reserved or \
                        ip_obj.is_link_local:
                    # Local address or loopback address, not reachable
                    return False

            LOGGER.debug('Resolved URL is not a local address, proceeding with connectivity check')

            # Try a connection with a new client to prevent malicious endpoint attacks
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=2.0,
                    read=2.0,
                    write=2.0,
                    pool=2.0,
                ),
                headers={'Accept-Encoding': 'identity'},
            ) as client:
                response = await client.get(url)

            LOGGER.debug('Connectivity check response status code: %d', response.status_code)

            return response.status_code == 200
        except (httpx.RequestError, httpx.HTTPStatusError, asyncio.TimeoutError, ValueError):
            return False

    async def raw_get(self,
                      url: str,
                      params: dict = None,
                      headers: dict = None,
                      ) -> dict:
        """
        A raw method to perform a GET request.
        :param url: The URL to request
        :param params: Optional parameters to include in the request
        :param headers: Optional headers to include in the request
        :return: JSON response from the server
        """
        try:
            LOGGER.info('Performing GET request to %s', url)
            response = await self._client.get(
                url=url,
                params=params,
                headers=headers,
            )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise NetworkRequestFailedException(
                    message=f'GET request to {url} failed with '
                            f'status code {e.response.status_code}',
                    status_code=e.response.status_code,
                ) from e

            return response.json()
        except NetworkRequestFailedException:
            raise
        except Exception as e:
            raise NetworkRequestFailedException(
                message=f'Error performing GET request to {url}',
            ) from e

    async def raw_post(self,
                       url: str,
                       payload: dict = None,
                       headers: dict = None,
                       ):
        """
        A raw method to perform a POST request.
        :param url: The URL to request
        :param payload: The payload to send in the request
        :param headers: Optional headers to include in the request
        :return: JSON response from the server
        """
        try:
            LOGGER.info('Performing POST request to %s', url)
            response = await self._client.post(
                url=url,
                json=payload,
                headers=headers,
            )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise NetworkRequestFailedException(
                    message=f'POST request to {url} failed with '
                            f'status code {e.response.status_code}',
                    status_code=e.response.status_code,
                ) from e

            return response.json()
        except NetworkRequestFailedException:
            raise
        except Exception as e:
            raise NetworkRequestFailedException(
                message=f'Error performing POST request to {url}',
            ) from e

    async def raw_stream(self,
                         url: str,
                         params: dict = None,
                         payload: dict = None,
                         headers: dict = None,
                         ) -> AsyncGenerator[str, None]:
        """
        A raw method to stream SSE-style events as an async generator.
        Only 'data:' lines are yielded.
        :param url: The URL to stream from
        :param params: Optional parameters to include in the request
        :param payload: Optional JSON payload to send in the request
        :param headers: Optional headers to include in the request
        :yield: String content of each 'data:' event
        """
        try:
            LOGGER.info('Performing stream request to %s', url)
            async with self._client.stream(
                'POST',
                url,
                params=params,
                json=payload,
                headers=headers,
            ) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    raise NetworkRequestFailedException(
                        message=f'Stream request to {url} failed with '
                                f'status code {e.response.status_code}',
                        status_code=e.response.status_code,
                    ) from e

                async for line in response.aiter_lines():
                    if line.startswith('data:'):
                        yield line[len('data:'):].strip()

        except NetworkRequestFailedException:
            raise
        except Exception as e:
            raise NetworkRequestFailedException(
                message=f'Error performing stream request to {url}',
            ) from e

    async def post_message(self,
                           network_message: NetworkMessage,
                           url: str,
                           ):
        """
        Post a network message to a given URL.
        :param network_message: The network message to post
        :param url: The URL to post the message to
        :return: The response from the server
        """
        kms = get_active_kms()

        return await self.raw_post(
            url=url,
            payload=network_message.to_dict(),
            headers={
                'Message-Signature': await kms.sign_payload(
                    payload=json.dumps(network_message.to_dict()),
                    network_id=network_message.metadata.network_id,
                )
            }
        )


class NetworkInterface:
    """
    An operation interface to handle network related operations.
    """
    def __init__(self,
                 driver: NetworkDriver = None,
                 ):
        if driver is not None:
            self._session = driver
        else:
            self._session = NetworkDriver()

    async def _websocket_handler(self,
                                 node_id: str,
                                 url: str,
                                 connection_message: AuthConnect,
                                 ):
        """
        Handler for establishing and maintaining a WebSocket connection.
        :param node_id: The ID of the node to connect to
        :param url: The URL to connect to for WebSocket communication
        :param connection_message: The message to send upon connection
        """
        from . import process_network_message

        broker = get_active_broker()
        kms = get_active_kms()
        async with websockets.connect(url) as websocket:
            connection_signature = await kms.sign_payload(
                payload=json.dumps(connection_message.to_dict()),
                network_id=connection_message.metadata.network_id
            )

            await websocket.send(json.dumps({
                'message': connection_message.to_dict(),
                'signature': connection_signature,
            }))

            LOGGER.info('WebSocket connection established with node %s', node_id)

            async def send_loop():
                while True:
                    message = await broker.get_message(node_id)
                    if message:
                        LOGGER.info('Sending message to node %s with WebSocket', node_id)
                        LOGGER.debug('Message content: %s', message)
                        await websocket.send(json.dumps(message))

                    await asyncio.sleep(0.1)

            async def receive_loop():
                async for payload in websocket:
                    try:
                        data = json.loads(payload)
                        LOGGER.info('Received message from node %s with WebSocket', node_id)
                        LOGGER.debug('Message content: %s', data)
                    except json.JSONDecodeError:
                        await websocket.send(json.dumps({'error': 'Invalid JSON format'}))
                        continue

                    if data.get('ping'):
                        await websocket.send(json.dumps({'pong': True}))
                        continue

                    message_data = data['message']
                    signature = data['signature']

                    if not await authenticate_network_message(
                            message=message_data,
                            signature=signature,
                    ):
                        await websocket.send(json.dumps({'error': 'Authentication failed'}))
                        continue

                    await process_network_message(data)

            await asyncio.gather(
                send_loop(),
                receive_loop(),
            )

    async def _establish_connection(self,
                                    network_id: str,
                                    node: Node,
                                    ):
        """
        Establish and maintain connection to a node. Use websockets if possible, or fall
        back to HTTP requests / SSE connections.
        :param network_id: The ID of the network to which the node belongs
        :param node: The node to connect to
        :return:
        """
        from . import process_network_message

        LOGGER.info('Establishing connection to node %s', node.node_id)
        db = get_active_db()
        network = await db.networks.get(network_id)

        auth_connect_message = AuthConnect(
            metadata=MessageMetadata(
                network_id=network_id,
                node_id=network.instance_id
            )
        )

        if await self.check_node_connectivity(
            node.url,
        ):
            LOGGER.info(
                'Node %s is reachable, attempting to establish WebSocket connection',
                node.node_id,
            )
            # Parse the url and change the scheme
            cache = get_active_cache()
            parsed_url = urlparse(node.url)
            if parsed_url.scheme not in ['http', 'https']:
                raise ValueError(f'Invalid URL scheme: {parsed_url.scheme}')

            ws_scheme = 'wss' if parsed_url.scheme == 'https' else 'ws'
            ws_url = f'{ws_scheme}://{parsed_url.netloc}/service/websocket'

            last_failure: float | None = None

            # Try to establish a WebSocket connection
            await cache.save_route(
                route=Route(
                    network_id=network_id,
                    node_id=node.node_id,
                    connectivity_type=ConnectivityType.DIRECT,
                    transport_type=TransportType.WEBSOCKET,
                    outbound=True,
                )
            )
            while last_failure is None or time.time() - last_failure > 60:
                try:
                    await self._websocket_handler(
                        node_id=node.node_id,
                        url=ws_url,
                        connection_message=auth_connect_message,
                    )
                except Exception as e:
                    LOGGER.error(
                        'WebSocket connection to node %s failed: %s',
                        node.node_id,
                        e,
                    )
                    last_failure = time.time()

            if time.time() - last_failure < 60:
                # Node is reachable, but WebSocket connection failed
                # Could be WebSocket is not supported through the load balancer
                LOGGER.info(
                    'WebSocket connection to node %s failed, falling back to SSE',
                    node.node_id,
                )

                last_failure = None
                await cache.save_route(
                    route=Route(
                        network_id=network_id,
                        node_id=node.node_id,
                        connectivity_type=ConnectivityType.DIRECT,
                        transport_type=TransportType.SSE,
                        outbound=True,
                    )
                )
                while last_failure is None or time.time() - last_failure > 60:
                    try:
                        async for event in self._session.raw_stream(
                            url=f'{node.url.rstrip("/")}/service/event',
                            payload=auth_connect_message.to_dict(),
                            headers={
                                'Message-Signature': await get_active_kms().sign_payload(
                                    payload=json.dumps(auth_connect_message.to_dict()),
                                    network_id=network_id,
                                )
                            }
                        ):
                            LOGGER.info(
                                'Received event from node %s',
                                node.node_id,
                            )
                            LOGGER.debug('Event content: %s', event)

                            await process_network_message(
                                json.loads(event),
                            )
                    except Exception as e:
                        last_failure = time.time()
                        LOGGER.error(
                            'SSE connection to node %s failed: %s',
                            node.node_id,
                            e,
                        )

            await cache.delete_route(
                node_id=node.node_id,
            )
            raise NetworkRequestFailedException(
                message=f'Failed to establish connection to node {node.node_id} '
                        f'after multiple attempts.',
                status_code=500,
            )

        # Both failed, try relaying through a different node
        # TODO: Implement relay logic
        raise NotImplementedError(
            'Relay logic is not implemented yet.',
        )

    async def check_node_connectivity(self,
                                      node_url: str,
                                      ) -> bool:
        """
        Check the connectivity to a node by its URL.
        :param node_url: The root URL of the node to check connectivity for
        :return: True if the node is reachable, False otherwise
        """
        target_url = f'{node_url.rstrip("/")}/service/status'

        return await self._session.check_connectivity(
            url=target_url,
        )

    async def establish_connection(self,
                                   network_id: str,
                                   node: Node,
                                   ) -> None:
        """
        Start a background task to connect to a node in the network.
        :param network_id: The ID of the network to which the node belongs
        :param node: The node to connect to
        :return: None
        """
        asyncio.create_task(
            self._establish_connection(
                network_id=network_id,
                node=node,
            )
        )
