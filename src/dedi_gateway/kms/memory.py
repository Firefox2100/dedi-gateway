import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

from dedi_gateway.etc.errors import KmsKeyManagementException
from .kms import Kms


class MemoryKms(Kms):
    """
    In-memory implementation of the KMS interface.
    This is intended for development and demonstration purposes only.
    Do not use in production.
    """
    _user_keys: dict = {}
    _network_node_keys: dict = {}
    _network_management_keys: dict = {}

    async def generate_network_node_key(self, network_id: str) -> str:
        private_key, public_key = self._generate_rsa_key_pair()

        self._network_node_keys[network_id] = {
            'privateKey': private_key,
            'publicKey': public_key,
        }

        return public_key

    async def generate_network_management_key(self, network_id: str) -> tuple[str, str]:
        private_key, public_key = self._generate_rsa_key_pair()

        self._network_management_keys[network_id] = {
            'privateKey': private_key,
            'publicKey': public_key,
        }

        return private_key, public_key

    async def store_network_management_key(self,
                                           public_key: str,
                                           network_id: str,
                                           private_key: str | None = None,
                                           ):
        payload: dict[str, str | dict] = {
            'publicKey': public_key,
        }
        if private_key:
            payload['privateKey'] = private_key

        if network_id in self._network_management_keys:
            payload['previousKey'] = {
                'publicKey': self._network_management_keys[network_id]['publicKey'],
            }
            if private_key:
                payload['previousKey']['privateKey'] = \
                    self._network_management_keys[network_id]['privateKey']

        self._network_management_keys[network_id] = payload

    async def get_network_node_public_key(self,
                                          network_id: str,
                                          previous_version=False,
                                          ) -> str:
        network_keys = self._network_node_keys.get(network_id)

        if not network_keys:
            raise KmsKeyManagementException(
                f'Network node key for {network_id} not found in memory KMS.'
            )

        if previous_version:
            if 'previousKey' not in network_keys:
                raise KmsKeyManagementException(
                    f'No previous version of key {network_id} found in memory KMS.'
                )

            return network_keys['previousKey']['publicKey']

        return network_keys['publicKey']

    async def get_network_management_public_key(self,
                                                network_id: str,
                                                previous_version=False,
                                                ) -> str:
        network_keys = self._network_management_keys.get(network_id)

        if not network_keys:
            raise KmsKeyManagementException(
                f'Network management key for {network_id} not found in memory KMS.'
            )

        if previous_version:
            if 'previousKey' not in network_keys:
                raise KmsKeyManagementException(
                    f'No previous version of key {network_id} found in memory KMS.'
                )

            return network_keys['previousKey']['publicKey']

        return network_keys['publicKey']

    async def get_network_management_private_key(self,
                                                 network_id: str,
                                                 ):
        network_keys = self._network_management_keys.get(network_id)

        if not network_keys:
            raise KmsKeyManagementException(
                f'Network management key for {network_id} not found in memory KMS.'
            )

        private_key = network_keys.get('privateKey')

        if not private_key:
            raise KmsKeyManagementException(
                f'Private key for network management {network_id} not found in memory KMS.'
            )

        return private_key

    async def sign_payload(self,
                           payload: str,
                           network_id: str,
                           ) -> str:
        network_node_key = self._network_node_keys.get(network_id)
        if not network_node_key:
            raise KmsKeyManagementException(
                f'Network node key for {network_id} not found in memory KMS.'
            )

        private_pem = network_node_key['privateKey']
        private_key = serialization.load_pem_private_key(
            private_pem.encode(),
            password=None,
        )

        signature = private_key.sign(
            payload.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256()
        )

        return base64.b64encode(signature).decode()
