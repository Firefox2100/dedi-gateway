from ..base_model import BaseModel
from .message_metadata import MessageMetadata


class NetworkMessage(BaseModel):
    def __init__(self,
                 metadata: MessageMetadata,
                 ):
        self.metadata = metadata
