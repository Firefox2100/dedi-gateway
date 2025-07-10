import json
import importlib.resources as pkg_resources

from dedi_gateway.etc.consts import CONFIG_PATH
from dedi_gateway.etc.errors import MessageConfigurationNotFoundException, \
    MessageConfigurationParsingException


class MessageConfig:
    """
    A class representing a message configuration.
    """
    def __init__(self,
                 base_package: str,
                 config_id: str,
                 *,
                 response: str = None,
                 preceding: str = None,
                 asynchronous: bool = False,
                 destination: str = None,
                 ):
        """
        A class representing a message configuration.
        :param base_package: The base package for the message configuration,
            in reverse domain notation (e.g., 'com.example.package').
        :param config_id: The unique identifier for the message configuration,
            e.g., 'com.example.package.config-id'.
        :param response: If the message has a response, this should be set to the
            corresponding type ID for the response.
        :param preceding: If the message is a response and cannot be sent
            without a preceding message, this should be set to the corresponding
            type ID for the preceding message.
        :param asynchronous: Whether the message response can be processed asynchronously.
            If True, the response shall not be waited for, and the handlers may return immediately.
        :param destination: Where to proxy this message once received.
        """
        self.base_package = base_package
        self.config_id = config_id
        self.response = response
        self.preceding = preceding
        self.asynchronous = asynchronous
        self.destination = destination


class NetworkMessageRegistry:
    _packages = []
    _configurations: dict[str, MessageConfig] = {}

    @classmethod
    def load_package(cls, package_path: str):
        """
        Load a package configuration from the specified path.
        :param package_path: The path to the package configuration file.
        """
        try:
            # Read the package configuration file
            with open(package_path, encoding='utf-8') as file:
                file_content = file.read()
                package_data = json.loads(file_content)

                if package_data['basePackage'] in cls._packages:
                    raise MessageConfigurationParsingException(
                        f'Package {package_data["basePackage"]} already loaded.'
                    )

                for config_data in package_data['messages']:
                    config = MessageConfig(
                        base_package=package_data['basePackage'],
                        config_id=config_data['id'],
                        response=f'{package_data["basePackage"]}.{config_data.get("response")}'
                            if config_data.get('response') else None,
                        preceding=f'{package_data["basePackage"]}.{config_data.get("precedence")}'
                            if config_data.get('precedence') else None,
                        asynchronous=config_data.get('async', False),
                    )

                    cls._configurations[f'{config.base_package}.{config.config_id}'] = config
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

        # Load proxy destinations from config file
        with open(CONFIG_PATH / 'proxy.json', encoding='utf-8') as file:
            proxy_configs = json.load(file)

            for proxy_config in proxy_configs:
                for config_id, config in cls._configurations.items():
                    if config_id.startswith(proxy_config['messageId']):
                        config.destination = proxy_config['destination']

    def get_configuration(self, config_id: str) -> MessageConfig:
        """
        Get a message configuration by its ID.
        :param config_id: The unique identifier for the message configuration.
        :return: The MessageConfig instance corresponding to the given ID.
        """
        if config_id not in self._configurations:
            raise MessageConfigurationNotFoundException(
                f'Message configuration with ID {config_id} not found.'
            )
        return self._configurations[config_id]
