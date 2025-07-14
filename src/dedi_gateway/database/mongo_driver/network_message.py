from typing import Mapping, Any
from pymongo.asynchronous.database import AsyncDatabase
from dedi_link.etc.enums import AuthMessageStatus
from dedi_link.model import AuthRequest, AuthInvite

from dedi_gateway.etc.errors import NetworkMessageNotFoundException
from dedi_gateway.model.network_message import NetworkMessageRepository


class MongoNetworkMessageRepository(NetworkMessageRepository):
    """
    MongoDB implementation of the NetworkMessageRepository interface.
    """

    def __init__(self, db: AsyncDatabase):
        """
        Initialise the MongoNetworkMessageRepository with a MongoDB database instance.
        :param db: MongoDB database instance.
        """
        self.db = db
        self.sent_requests = db['messages.requests.sent']
        self.received_requests = db['messages.requests.received']

    async def save_sent_request(self,
                                target_url: str,
                                request: AuthRequest | AuthInvite,
                                requires_polling: bool = False,
                                ):
        payload = {
            'targetUrl': target_url,
            'request': request.to_dict(),
            'requiresPolling': requires_polling,
            'status': AuthMessageStatus.PENDING.value,
        }

        await self.sent_requests.insert_one(payload)

    async def save_received_request(self,
                                    request: AuthRequest | AuthInvite,
                                    ):
        payload = {
            'request': request.to_dict(),
            'status': AuthMessageStatus.PENDING.value,
        }

        await self.received_requests.insert_one(payload)

    async def get_requests(self,
                           sent: bool = None,
                           status: list[AuthMessageStatus] = None,
                           ) -> list[dict]:
        query = {}
        docs = []

        if status:
            query['status'] = {'$in': [s.value for s in status]}

        if sent is not True:
            cursor = self.received_requests.find(query)

            async for doc in cursor:
                docs.append(doc)

        if sent is not False:
            cursor = self.sent_requests.find(query)

            async for doc in cursor:
                docs.append(doc)

        return docs

    async def get_received_request(self,
                                   request_id: str,
                                   ) -> Mapping[str, Any]:
        payload = await self.received_requests.find_one({'request.metadata.messageId': request_id})

        if not payload:
            raise NetworkMessageNotFoundException(
                f'Received request with ID {request_id} not found.'
            )

        return payload

    async def get_sent_request(self,
                               request_id: str,
                               ) -> Mapping[str, Any]:
        payload = await self.sent_requests.find_one({'request.metadata.messageId': request_id})

        if not payload:
            raise NetworkMessageNotFoundException(
                f'Sent request with ID {request_id} not found.'
            )

        return payload

    async def update_request_status(self,
                                    request_id: str,
                                    status: AuthMessageStatus,
                                    ) -> None:
        result = await self.received_requests.update_one(
            {'request.metadata.messageId': request_id},
            {'$set': {'status': status.value}}
        )

        if result.matched_count == 0:
            result = await self.sent_requests.update_one(
                {'request.metadata.messageId': request_id},
                {'$set': {'status': status.value}}
            )

        if result.matched_count == 0:
            raise NetworkMessageNotFoundException(
                f'Request with ID {request_id} not found.'
            )
