import asyncio
import socket
import ipaddress
from urllib.parse import urlparse
import httpx

from dedi_gateway.etc.errors import NetworkRequestFailedException


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

            # Try a connection with a new client to prevent malicious endpoint attacks
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=2.0,
                    read=2.0,
                    write=2.0,
                    pool=2.0,
                ),
                follow_redirects=False,
                headers={'Accept-Encoding': 'identity'},
            ) as client:
                response = await client.get(url)

            return response.status_code == 200
        except (httpx.RequestError, httpx.HTTPStatusError, asyncio.TimeoutError, ValueError):
            return False

    async def raw_get(self,
                      url: str,
                      params: dict = None,
                      ) -> dict:
        """
        A raw method to perform a GET request.
        :param url: The URL to request
        :param params: Optional parameters to include in the request
        :return: JSON response from the server
        """
        try:
            response = await self._client.get(
                url=url,
                params=params,
            )

            if response.status_code != 200:
                raise NetworkRequestFailedException(
                    message=f'GET request to {url} failed with status code {response.status_code}',
                    status_code=response.status_code,
                )

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
                       ):
        """
        A raw method to perform a POST request.
        :param url: The URL to request
        :param payload: The payload to send in the request
        :return: JSON response from the server
        """
        try:
            response = await self._client.post(
                url=url,
                json=payload,
            )

            if response.status_code != 200:
                raise NetworkRequestFailedException(
                    message=f'POST request to {url} failed with status code {response.status_code}',
                    status_code=response.status_code,
                )

            return response.json()
        except NetworkRequestFailedException:
            raise
        except Exception as e:
            raise NetworkRequestFailedException(
                message=f'Error performing POST request to {url}',
            ) from e


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
