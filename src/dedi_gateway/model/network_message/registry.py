import json
import importlib.resources as pkg_resources

from dedi_gateway.etc.errors import MessageConfigurationNotFoundException, \
    MessageConfigurationParsingException


class MessageConfig:
    def __init__(self,
                 base_package: str,
                 config_id: str,
                 response: 'MessageConfig' = None,
                 asynchronous: bool = False,
                 ):
        """
        A class representing a message configuration.
        :param base_package: The base package for the message configuration,
            in reverse domain notation (e.g., 'com.example.package').
        :param config_id: The unique identifier for the message configuration,
            e.g., 'com.example.package.config-id'.
        :param response: If the message has a response, this should be set to the
            corresponding MessageConfig instance for the response.
        :param asynchronous:
        """


class NetworkMessageRegistry:
    _packages = []

    @classmethod
    def load_package(cls, package_path: str):
        """
        Load a package configuration from the specified path.
        :param package_path: The path to the package configuration file.
        """
        try:
            # Read the package configuration file
            with open(package_path, 'r') as file:
                file_content = file.read()
                package_data = json.loads(file_content)

                if package_data['basePackage'] in cls._packages:
                    raise MessageConfigurationParsingException(
                        f'Package {package_data["basePackage"]} already loaded.'
                    )
        except FileNotFoundError as e:
            raise MessageConfigurationNotFoundException(
                f'Package configuration file not found: {package_path}'
            ) from e
        except json.JSONDecodeError as e:
            raise MessageConfigurationParsingException(
                f'Error decoding JSON from package configuration file: {package_path}. Error: {e}'
            ) from e


    @classmethod
    def load_packages(cls):
        """
        Load package configurations from the data files
        """
        config_path = pkg_resources.files('dedi_gateway.data.messages')
        for package in config_path.iterdir():
            if package.is_file():
                cls.load_package(str(package))
