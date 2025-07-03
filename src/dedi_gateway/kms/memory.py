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

    async def generate_user_key(self, user_id: str) -> str | None:
        private_key, public_key = self._generate_rsa_key_pair()

        self._user_keys[user_id] = {
            'privateKey': private_key,
            'publicKey': public_key,
        }

        return public_key

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

    async def get_local_user_public_key(self,
                                        user_id: str,
                                        previous_version=False,
                                        ) -> str:
        user_keys = self._user_keys.get(user_id)

        if not user_keys:
            raise KmsKeyManagementException(
                f'User key for {user_id} not found in memory KMS.'
            )

        if previous_version:
            if 'previousKey' not in user_keys:
                raise KmsKeyManagementException(
                    f'No previous version of key {user_id} found in memory KMS.'
                )

            return user_keys['previousKey']['publicKey']

        return user_keys['publicKey']

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
