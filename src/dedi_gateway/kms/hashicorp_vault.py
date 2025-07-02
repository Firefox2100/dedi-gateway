import hvac
from hvac.exceptions import InvalidRequest, InvalidPath

from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.errors import KmsKeyManagementException, NetworkRequestFailedException
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

    async def generate_user_key(self, user_id: str) -> str | None:
        try:
            self.client.secrets.transit.create_key(
                name=f'user-{user_id}',
                key_type='rsa-4096',
                mount_point=SERVICE_CONFIG.vault_transit_engine,
            )
        except InvalidRequest:
            return None

        self.client.secrets.transit.update_key_configuration(
            name=user_id,
            deletion_allowed=True,
            mount_point=SERVICE_CONFIG.vault_transit_engine,
        )

        return await self.get_local_user_public_key(user_id)

    async def generate_network_node_key(self, network_id: str) -> str:
        try:
            self.client.secrets.transit.create_key(
                name=f'network-{network_id}',
                key_type='rsa-4096',
                mount_point=SERVICE_CONFIG.vault_transit_engine,
            )
        except InvalidRequest as e:
            raise NetworkRequestFailedException(
                f'Unexpected error while generating network key for '
                f'{network_id} in HashiCorp Vault.',
            ) from e

        self.client.secrets.transit.update_key_configuration(
            name=network_id,
            deletion_allowed=True,
            mount_point=SERVICE_CONFIG.vault_transit_engine,
        )

        return await self.get_local_user_public_key(network_id)

    async def get_local_user_public_key(self,
                                        user_id: str,
                                        previous_version = False,
                                        ) -> str:
        try:
            key_info = self.client.secrets.transit.read_key(
                name=f'user-{user_id}',
                mount_point=SERVICE_CONFIG.vault_transit_engine,
            )

            versions = map(int, key_info['data']['keys'].keys())
            latest_version = max(versions)

            if previous_version:
                latest_version -= 1

            if latest_version < 0:
                raise KmsKeyManagementException(
                    f'No previous version of key {user_id} found in HashiCorp Vault.',
                    status_code=404,
                )

            return key_info['data']['keys'][str(latest_version)]['public_key']
        except (InvalidPath, ValueError) as e:
            raise KmsKeyManagementException(
                f'User key {user_id} not found in HashiCorp Vault.',
                status_code=404,
            ) from e

    async def get_network_node_public_key(self,
                                          network_id: str,
                                          previous_version=False,
                                          ) -> str:
        try:
            key_info = self.client.secrets.transit.read_key(
                name=f'network-{network_id}',
                mount_point=SERVICE_CONFIG.vault_transit_engine,
            )

            versions = map(int, key_info['data']['keys'].keys())
            latest_version = max(versions)

            if previous_version:
                latest_version -= 1

            if latest_version < 0:
                raise KmsKeyManagementException(
                    f'No previous version of key {network_id} found in HashiCorp Vault.',
                    status_code=404,
                )

            return key_info['data']['keys'][str(latest_version)]['public_key']
        except (InvalidPath, ValueError) as e:
            raise KmsKeyManagementException(
                f'Network key {network_id} not found in HashiCorp Vault.',
                status_code=404,
            ) from e
