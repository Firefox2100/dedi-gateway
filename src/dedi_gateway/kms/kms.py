class KMS:
    """
    Abstract interface for Key Management Service (KMS) operations.
    """
    async def generate_user_key(self, user_id: str) -> str:
        """
        Generate a user-specific key pair for encryption and signing.
        :param user_id:
        :return: The user public key. Private key is not exported if the KMS
                 implementation supports it.
        """
        raise NotImplementedError("generate_user_key must be implemented by subclasses")

    async def generate_service_key(self) -> str:
        """
        Generate a service-specific key pair for encryption and signing.
        :return: The generated service key.
        """
        raise NotImplementedError("generate_service_key must be implemented by subclasses")
