"""
HashiCorp Vault Key Management Service (KMS) implementation.

This file contains implementation of the Kms interface, with the
HashiCorp Vault as the backend.
"""

import base64
import hvac
from hvac.exceptions import InvalidRequest, InvalidPath

from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.errors import KmsKeyManagementException
from .kms import Kms


class HcvKms(Kms):
    """
    HashiCorp Vault Key Management Service (KMS) implementation.
    """
    _client: hvac.Client = None

    @property
    def client(self) -> hvac.Client:
        """
        Get the HashiCorp Vault client instance.
        :return: The hvac.Client instance.
        """
        if self._client is None:
            raise ValueError('HashiCorp Vault client is not set. Call set_client() first.')
        return self._client

    @classmethod
    def set_client(cls,
                   client: hvac.Client,
                   ):
        """
        Set the HashiCorp Vault client for the KMS.
        :param client: hvac.Client instance configured to connect to HashiCorp Vault.
        """
        cls._client = client

    async def _read_transit_public_key(self,
                                       key_name: str,
                                       previous_version: bool = False,
                                       ):
        """
        Helper method to read the public key from the HashiCorp Vault Transit engine.
        :param key_name: The name of the key to read.
        :param previous_version: If True, retrieves the previous version of the secret.
        :return: The secret data as a dictionary.
        """
        try:
            key_info = self.client.secrets.transit.read_key(
                name=key_name,
                mount_point=SERVICE_CONFIG.vault_transit_engine,
            )

            versions = map(int, key_info['data']['keys'].keys())
            latest_version = max(versions)

            if previous_version:
                latest_version -= 1

            if latest_version < 1:
                raise KmsKeyManagementException(
                    f'No previous version of key {key_name} found in HashiCorp Vault.',
                    status_code=404,
                )

            return key_info['data']['keys'][str(latest_version)]['public_key']
        except (InvalidPath, ValueError) as e:
            raise KmsKeyManagementException(
                f'Key {key_name} not found in HashiCorp Vault.',
                status_code=404,
            ) from e

    async def _read_kv_secret(self,
                              path: str,
                              previous_version: bool = False,
                              ) -> dict:
        """
        Helper method to read a secret from the HashiCorp Vault KV store.
        :param path: The path to the secret in the KV store.
        :param previous_version: If True, retrieves the previous version of the secret.
        :return: The secret data as a dictionary.
        """
        try:
            # Read the secret metadata to determine the latest version
            secret_metadata = (self.client.secrets.kv.read_secret_metadata(
                path=f'{SERVICE_CONFIG.vault_kv_path}/{path}',
                mount_point=SERVICE_CONFIG.vault_kv_engine,
            ))

            latest_version = max([int(v) for v in secret_metadata['versions'].keys()])
            if previous_version:
                latest_version -= 1

            if latest_version < 1:
                raise KmsKeyManagementException(
                    f'Unable to find previous version of secret {path} in HashiCorp Vault.',
                    status_code=404,
                )

            # Read the specific version of the secret
            secret = self.client.secrets.kv.v2.read_secret_version(
                path=f'{SERVICE_CONFIG.vault_kv_path}/{path}',
                version=latest_version,
                mount_point=SERVICE_CONFIG.vault_kv_engine,
            )

            return secret['data']['data']
        except InvalidPath as e:
            raise KmsKeyManagementException(
                f'Secret {path} not found in HashiCorp Vault.',
                status_code=404,
            ) from e

    async def generate_network_node_key(self, network_id: str) -> str:
        """
        Generate a network-specific key pair for signing network messages.
        :return: The generated network public key. Private key is not exported.
        """
        try:
            self.client.secrets.transit.create_key(
                name=f'network-{network_id}',
                key_type='rsa-4096',
                mount_point=SERVICE_CONFIG.vault_transit_engine,
            )
        except InvalidRequest as e:
            raise KmsKeyManagementException(
                f'Unexpected error while generating network key for '
                f'{network_id} in HashiCorp Vault.',
            ) from e

        self.client.secrets.transit.update_key_configuration(
            name=network_id,
            deletion_allowed=True,
            mount_point=SERVICE_CONFIG.vault_transit_engine,
        )

        return await self.get_network_node_public_key(network_id)

    async def generate_network_management_key(self, network_id: str) -> tuple[str, str]:
        """
        Generate a network management key pair for managing network operations.
        :return: The generated network management private and public key pair.
        """
        private_key, public_key = self._generate_rsa_key_pair()

        self.client.secrets.kv.v2.create_or_update_secret(
            path=f'{SERVICE_CONFIG.vault_kv_path}/network/{network_id}',
            secret={
                'privateKey': private_key,
                'publicKey': public_key,
            },
            mount_point=SERVICE_CONFIG.vault_kv_engine,
        )

        return private_key, public_key

    async def store_network_management_key(self,
                                           public_key: str,
                                           network_id: str,
                                           private_key: str | None = None,
                                           ):
        """
        Store the network management key pair in the KMS.
        :param public_key: The public key to store.
        :param network_id: The network ID to associate with the key.
        :param private_key: The private key to store, if applicable.
        """
        payload = {
            'publicKey': public_key,
        }
        if private_key:
            payload['privateKey'] = private_key

        self.client.secrets.kv.v2.create_or_update_secret(
            path=f'{SERVICE_CONFIG.vault_kv_path}/network/{network_id}',
            secret=payload,
            mount_point=SERVICE_CONFIG.vault_kv_engine,
        )

    async def get_network_node_public_key(self,
                                          network_id: str,
                                          previous_version=False,
                                          ) -> str:
        return await self._read_transit_public_key(
            key_name=f'network-{network_id}',
            previous_version=previous_version,
        )

    async def get_network_management_public_key(self,
                                                network_id: str,
                                                previous_version=False,
                                                ) -> str:
        secret_data = await self._read_kv_secret(
            path=f'{SERVICE_CONFIG.vault_kv_path}/network/{network_id}',
            previous_version=previous_version,
        )
        return secret_data['publicKey']

    async def get_network_management_private_key(self,
                                                 network_id: str,
                                                 ):
        secret_data = await self._read_kv_secret(
            path=f'{SERVICE_CONFIG.vault_kv_path}/network/{network_id}',
        )

        private_key = secret_data.get('privateKey')

        if not private_key:
            raise KmsKeyManagementException(
                f'Private key for network {network_id} not found in HashiCorp Vault.',
                status_code=404,
            )

    async def sign_payload(self,
                           payload: str,
                           network_id: str,
                           ) -> str:
        try:
            response = self.client.secrets.transit.sign_data(
                name=f'network-{network_id}',
                hash_input=base64.b64encode(payload.encode()).decode(),
                hash_algorithm='sha2-256',
                signature_algorithm='pss',
                salt_length='auto',
                mount_point=SERVICE_CONFIG.vault_transit_engine,
            )

            signature = response['data']['signature']
            signature = signature.split(':')[-1]

            return signature
        except InvalidPath as e:
            raise KmsKeyManagementException(
                f'Network key {network_id} not found in HashiCorp Vault.',
                status_code=404,
            ) from e
        except InvalidRequest as e:
            raise KmsKeyManagementException(
                f'Error signing payload for network {network_id} in HashiCorp Vault.',
            ) from e
