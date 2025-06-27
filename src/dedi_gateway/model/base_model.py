from enum import Enum
from typing import Optional, Callable, Type, TypeVar


BaseModelT = TypeVar('BaseModelT', bound='BaseModel')


class BaseModel:
    """
    Base class providing dynamic child registration and factory methods for creating instances
    """
    child_registry: Optional[dict[Enum, tuple[Type['BaseModel'], Callable[[dict], Enum] | None]]]

    @staticmethod
    def deep_eq(a: dict, b: dict) -> bool:
        """
        Compare two dictionaries deeply for equality, ignoring order of keys or lists
        :param a: The first dictionary to compare
        :param b: The second dictionary to compare
        :return: True if the dictionaries are equal, False otherwise
        """
        if isinstance(a, dict) and isinstance(b, dict):
            if set(a.keys()) != set(b.keys()):
                return False

            return all(BaseModel.deep_eq(a[key], b[key]) for key in a)
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return False

            b_remaining = list(b)

            for a_item in a:
                found = False
                for i, b_item in enumerate(b_remaining):
                    if BaseModel.deep_eq(a_item, b_item):
                        found = True
                        del b_remaining[i]
                        break
                if not found:
                    return False

            return True
        else:
            return a == b

    @classmethod
    def register_child(cls: Type[BaseModelT],
                       id_var: Enum,
                       mapping_function: Callable[[dict], Enum] = None,
                       ):
        """
        Register a child class
        :param id_var: The enum value to use for the mapping
        :param mapping_function: A function to map the payload to the enum value
        """
        def decorator(child_class: Type[BaseModelT]):
            if not hasattr(cls, 'child_registry'):
                raise ValueError(
                    'Parent class does not implement child registry. Is it a base model?'
                )

            cls.child_registry[id_var] = (child_class, mapping_function)
            return child_class

        return decorator

    @classmethod
    def factory_from_id(cls: Type[BaseModelT], payload: dict, id_var: Enum):
        """
        Raw method for creating an instance of (usually) a child class from a dictionary

        By following the mapping defined as a class attribute

        :param payload:
        :param id_var:
        :return:
        """
        if not cls.child_registry:
            # No known mapping, just create the class itself
            return cls.from_dict(payload)

        if id_var not in cls.child_registry:
            raise ValueError(f'{id_var} not found in the defined mapping')

        mapping_target = cls.child_registry[id_var]

        if mapping_target[1] is None:
            # Basic mapping, create the object by calling the from_dict method
            return mapping_target[0].from_dict(payload)

        # A deeper mapping function provided, get the new id_var and call factory again
        new_id_var = mapping_target[1](payload)
        return mapping_target[0].factory_from_id(payload, new_id_var)

    @classmethod
    def factory(cls, payload: dict):
        """
        Encapsulated method to create an object from a dictionary

        This is meant to be overridden by the child classes to provide handle the id_var
        creation internally, and exposing a convenient API to the caller. By default, it
        calls the to_dict method directly to prevent unexpected behavior

        :param payload: The dictionary containing the data
        """
        return cls.from_dict(payload)

    @classmethod
    def from_dict(cls: Type[BaseModelT], payload: dict) -> BaseModelT:
        """
        Build an instance from a dictionary

        :param payload: The data dictionary containing the instance data
        :return: An instance of the model
        """
        raise NotImplementedError('Method must be implemented by the child class')

    def to_dict(self) -> dict:
        """
        Serialize the instance to a dictionary

        :return: A dictionary representation of the instance
        """
        raise NotImplementedError('Method must be implemented by the child class')
