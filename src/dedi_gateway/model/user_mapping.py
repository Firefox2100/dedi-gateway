from dedi_gateway.etc.enums import UserMappingType
from .base_model import BaseModel


class UserMapping(BaseModel):
    """
    A class controlling how user IDs are mapped to other user IDs.

    User ID mapping is implemented in the case where incoming ID (for
    example, from a different server) does not correspond directly to the
    local IDs used in this system, and mapping is required.
    """
    def __init__(self,
                 mapping_type: UserMappingType = UserMappingType.NO_MAPPING,
                 static_id: str = None,
                 dynamic_mapping: dict[str, str] = None,
                 ):
        """
        A class controlling how user IDs are mapped to other user IDs.

        User ID mapping is implemented in the case where incoming ID (for
        example, from a different server) does not correspond directly to the
        local IDs used in this system, and mapping is required.

        :param mapping_type: The type of mapping to use
        :param static_id: The static ID to map to if mapping type is static
        :param dynamic_mapping: The dynamic mapping to use, if mapping type is dynamic
        :raises ValueError: If the mapping type is static and no static ID is provided
        """
        self.mapping_type = mapping_type
        self.static_id = static_id
        self.dynamic_mapping = dynamic_mapping or {}

        if mapping_type == UserMappingType.STATIC and static_id is None:
            raise ValueError('Static ID is required for static mapping')

        if mapping_type == UserMappingType.DYNAMIC and not dynamic_mapping:
            raise ValueError('Dynamic mapping is required for dynamic mapping')

    def __eq__(self, other):
        if not isinstance(other, UserMapping):
            return NotImplemented

        if self.mapping_type != other.mapping_type:
            return False

        if self.mapping_type == UserMappingType.NO_MAPPING:
            return True
        elif self.mapping_type == UserMappingType.STATIC:
            return self.static_id == other.static_id
        elif self.mapping_type == UserMappingType.DYNAMIC:
            return not self.deep_eq(
                self.dynamic_mapping,
                other.dynamic_mapping,
            )

        return False

    def to_dict(self) -> dict:
        payload = {
            'mappingType': self.mapping_type.value,
        }

        if self.mapping_type == UserMappingType.STATIC:
            payload['staticId'] = self.static_id
        elif self.mapping_type == UserMappingType.DYNAMIC:
            payload['dynamicMapping'] = self.dynamic_mapping

        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> 'UserMapping':
        mapping_type = UserMappingType(payload.get('mappingType', UserMappingType.NO_MAPPING.value))
        static_id = payload.get('staticId')
        dynamic_mapping = payload.get('dynamicMapping')

        return UserMapping(
            mapping_type=mapping_type,
            static_id=static_id,
            dynamic_mapping=dynamic_mapping,
        )

    def map(self,
            user_id: str | None = None,
            ) -> str:
        """
        Map a user ID to a new user ID based on the mapping type

        :param user_id: The user ID to map
        :return: The mapped user ID
        :raises ValueError: If the mapping type is invalid or no user ID is provided
        """
        if self.mapping_type == UserMappingType.NO_MAPPING:
            if user_id is None:
                raise ValueError('No user ID provided')
            return user_id

        if self.mapping_type == UserMappingType.STATIC:
            return self.static_id

        if self.mapping_type == UserMappingType.DYNAMIC:
            if user_id is None:
                raise ValueError('No user ID provided')
            new_id = self.dynamic_mapping.get(user_id)

            if new_id is None:
                raise ValueError(f'User ID {user_id} not found in mapping')

            return new_id

        raise ValueError(f'Invalid mapping type {self.mapping_type}')
