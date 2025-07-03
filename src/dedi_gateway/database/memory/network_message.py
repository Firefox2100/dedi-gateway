from dedi_gateway.etc.enums import AuthMessageStatus
from dedi_gateway.model.network_message import NetworkMessageRepository, AuthRequest, AuthInvite


class MemoryNetworkMessageRepository(NetworkMessageRepository):
    """
    In-memory implementation of the NetworkMessageRepository interface.
    """
    def __init__(self, db: dict):
        """
        Initialise the NetworkMessageRepository with a dictionary.
        :param db: A dictionary to act as the in-memory database.
        """
        self.db = db

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

        if 'sentRequests' not in self.db:
            self.db['sentRequests'] = {}

        self.db['sentRequests'][request.metadata.message_id] = payload

    async def save_received_request(self,
                                    request: AuthRequest | AuthInvite,
                                    ):
        payload = {
            'request': request.to_dict(),
            'status': AuthMessageStatus.PENDING.value,
        }

        if 'receivedRequests' not in self.db:
            self.db['receivedRequests'] = {}

        self.db['receivedRequests'][request.metadata.message_id] = payload

    async def get_requests(self,
                           sent: bool = None,
                           status: list[AuthMessageStatus] = None,
                           ) -> list[dict]:
        docs = []

        if sent is not True:
            received_requests = self.db.get('receivedRequests', {})
            for request in received_requests.values():
                if status is None or request['status'] in [s.value for s in status]:
                    docs.append(request)

        if sent is not False:
            sent_requests = self.db.get('sentRequests', {})
            for request in sent_requests.values():
                if status is None or request['status'] in [s.value for s in status]:
                    docs.append(request)

        return docs
