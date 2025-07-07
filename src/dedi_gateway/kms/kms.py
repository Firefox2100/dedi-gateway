import base64
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from dedi_gateway.etc.consts import SERVICE_CONFIG
from dedi_gateway.etc.errors import ConfigurationParsingException


class Kms:
    """
    Abstract interface for Key Management Service (KMS) operations.
    """
    @staticmethod
    def _generate_rsa_key_pair() -> tuple[str, str]:
        """
        Utility method to generate an RSA-4096 key pair.
        :return: A tuple containing the private key and public key in PEM format.
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_pem.decode(), public_pem.decode()

    async def generate_user_key(self, user_id: str) -> str | None:
        """
        Generate a user-specific key pair for encryption and signing.
        :param user_id:
        :return: The user public key. Private key is not exported if the KMS
            implementation supports it.
        """
        raise NotImplementedError

    async def generate_network_node_key(self, network_id: str) -> str:
        """
        Generate a network-specific key pair for signing network messages.
        :return: The generated network public key. Private key is not exported if the KMS
            implementation supports it.
        """
        raise NotImplementedError

    async def generate_network_management_key(self, network_id: str) -> tuple[str, str]:
        """
        Generate a network management key pair for managing network operations.
        :return: The generated network management private and public key pair.
        """
        raise NotImplementedError

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
        raise NotImplementedError

    async def get_local_user_public_key(self,
                                        user_id: str,
                                        previous_version=False,
                                        ) -> str:
        """
        Get the public key for a local user
        :param user_id: The user ID to retrieve the public key for.
        :param previous_version: If True, retrieves the previous version of the key.
        :return: The user's public key in PEM format.
        """
        raise NotImplementedError

    async def get_network_node_public_key(self,
                                          network_id: str,
                                          previous_version=False,
                                          ) -> str:
        """
        Get the public key for a network for signing.
        :param network_id: The network ID to retrieve the public key for.
        :param previous_version: If True, retrieves the previous version of the key.
        :return: The network's public key in PEM format.
        """
        raise NotImplementedError

    async def get_network_management_public_key(self,
                                                network_id: str,
                                                previous_version=False,
                                                ) -> str:
        """
        Get the public key for a network management.
        :param network_id: The network ID to retrieve the public key for.
        :param previous_version: If True, retrieves the previous version of the key.
        :return: The network management's public key in PEM format.
        """
        raise NotImplementedError

    async def get_network_management_private_key(self,
                                                 network_id: str,
                                                 ) -> str:
        """
        Get the private key for a network management.
        :param network_id: The network ID to retrieve the private key for.
        :return: The network management's private key in PEM format.
        """
        raise NotImplementedError

    async def sign_payload(self,
                           payload: str,
                           network_id: str,
                           ) -> str:
        """
        Sign a payload with the network node key.
        :param payload: The payload to sign as a string.
        :param network_id: The network ID to use for signing.
        :return: The signature of the payload.
        """
        raise NotImplementedError

    async def verify_signature(self,
                               payload: str,
                               public_pem: str,
                               signature: str,
                               ) -> bool:
        """
        Verify a signature against a payload using the network node public key.
        :param payload: The payload to verify as a string.
        :param public_pem: The public key to use for verification in PEM format.
        :param signature: The signature to verify.
        :return: True if the signature is valid, False otherwise.
        """
        public_key = serialization.load_pem_public_key(
            public_pem.encode(),
        )

        try:
            public_key.verify(
                base64.b64decode(signature),
                payload.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except InvalidSignature:
            return False


_active_kms: Kms | None = None


def get_active_kms() -> Kms | None:
    """
    Return the active KMS (Key Management Service) set by configuration
    :return: KMS instance based on the configuration.
    """
    global _active_kms

    if _active_kms is not None:
        return _active_kms

    if SERVICE_CONFIG.kms_driver == 'vault':
        from hvac import Client
        from .hashicorp_vault import HcvKms

        vault_client = Client(
            url=SERVICE_CONFIG.vault_url,
        )
        vault_client.auth.approle.login(
            role_id=SERVICE_CONFIG.vault_role_id,
            secret_id=SERVICE_CONFIG.vault_secret_id,
        )
        HcvKms.set_client(
            client=vault_client,
        )

        _active_kms = HcvKms()

        return _active_kms
    elif SERVICE_CONFIG.kms_driver == 'memory':
        from .memory import MemoryKms

        _active_kms = MemoryKms()

        return _active_kms
    else:
        raise ConfigurationParsingException(
            f'Unsupported KMS driver: {SERVICE_CONFIG.kms_driver}'
        )
