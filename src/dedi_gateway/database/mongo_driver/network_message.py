from typing import TYPE_CHECKING

from dedi_gateway.etc.enums import AuthMessageStatus
from dedi_gateway.model.network_message import NetworkMessageRepository, AuthRequest, AuthInvite

if TYPE_CHECKING:
    from pymongo.asynchronous.database import AsyncDatabase


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
