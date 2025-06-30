import logging
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceConfig(BaseSettings):
    """
    Configuration settings for the Decentralised Discovery Gateway service.
    """
    model_config = SettingsConfigDict(env_prefix='DG_')

    application_name: str = Field(
        'dedi-gateway',
        description='Name of the application'
    )
    logging_level: str = Field(
        'INFO',
        description='Logging level for the application'
    )

    ema_factor: float = Field(
        0.3,
        description='Exponential Moving Average factor for node scores',
    )

    database_driver: str = Field(
        'mongo',
        description='Database driver to use for the service',
    )
    mongodb_host: str = Field(
        'localhost',
        description='Host for the MongoDB database',
    )
    mongodb_port: int = Field(
        27017,
        description='Port for the MongoDB database',
    )
    mongodb_db_name: str = Field(
        'dedi-gateway',
        description='Name of the MongoDB database to use',
    )

    broker_driver: str = Field(
        'redis',
        description='Message broker driver to use for the service',
    )
    redis_host: str = Field(
        'localhost',
        description='Redis host for the message broker',
    )
    redis_port: int = Field(
        6379,
        description='Redis port for the message broker',
    )


SERVICE_CONFIG = ServiceConfig()        # type: ignore

LOGGER = logging.getLogger(SERVICE_CONFIG.application_name)
LOGGER.setLevel(SERVICE_CONFIG.logging_level.upper())

if not LOGGER.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setLevel(SERVICE_CONFIG.logging_level.upper())

    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(process)d] [%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z'
    )
    console_handler.setFormatter(formatter)

    LOGGER.addHandler(console_handler)

LOGGER.debug('Service configuration loaded: %s', SERVICE_CONFIG.model_dump_json(indent=2))
