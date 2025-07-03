from typing import Mapping, Any

from dedi_gateway.etc.enums import AuthMessageStatus
from .auth_message import AuthRequest, AuthInvite


class NetworkMessageRepository:
    """
    Abstract repository interface for managing network messages.
    """
    async def save_sent_request(self,
                                target_url: str,
                                request: AuthRequest | AuthInvite,
                                requires_polling: bool = False,
                                ):
        """
        Save a request that has been sent to a target URL.
        :param target_url: The URL to which the request was sent
        :param request: The request object to save
        :param requires_polling: Whether the request requires polling for a response
        """
        raise NotImplementedError

    async def save_received_request(self,
                                    request: AuthRequest | AuthInvite,
                                    ):
        """
        Save a request that has been received.
        :param request: The request object to save
        """
        raise NotImplementedError

    async def get_requests(self,
                           sent: bool = None,
                           status: list[AuthMessageStatus] = None,
                           ) -> list[dict]:
        """
        Retrieve requests based on their direction and status.
        :param sent: If True, retrieve sent requests; if False, retrieve received
            requests; if None, retrieve both.
        :param status: List of statuses to filter requests by. If None, all
            statuses are included.
        :return: List of requests matching the criteria.
        """
        raise NotImplementedError

    async def get_received_request(self,
                                   request_id: str,
                                   ) -> Mapping[str, Any]:
        """
        Retrieve a specific received request by its ID.
        :param request_id: The ID of the request to retrieve.
        :return: The request data if found, otherwise None.
        """
        raise NotImplementedError

    async def update_request_status(self,
                                    request_id: str,
                                    status: AuthMessageStatus,
                                    ) -> None:
        """
        Update the status of a request.
        :param request_id: The ID of the request to update.
        :param status: The new status to set for the request.
        """
        raise NotImplementedError
