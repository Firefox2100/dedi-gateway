import logging
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from apscheduler.schedulers.asyncio import AsyncIOScheduler


CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent / 'conf'
SCHEDULER = AsyncIOScheduler()


class ServiceConfig(BaseSettings):
    """
    Configuration settings for the Decentralised Discovery Gateway service.
    """
    model_config = SettingsConfigDict(
        env_prefix='DG_',
        env_file=CONFIG_PATH / '.env',
        env_file_encoding='utf-8',
    )

    application_name: str = Field(
        'dedi-gateway',
        description='Name of the application'
    )
    access_url: str = Field(
        'http://localhost:5321',
        description='Publicly accessible URL for the service',
    )
    service_name: str = Field(
        'Decentralised Discovery Gateway',
        description='Name of the service',
    )
    service_description: str = Field(
        'A decentralised discovery gateway for federated networks',
        description='Description of the service',
    )
    logging_level: str = Field(
        'INFO',
        description='Logging level for the application'
    )

    ema_factor: float = Field(
        0.3,
        description='Exponential Moving Average factor for node scores',
    )
    challenge_difficulty: int = Field(
        22,
        description='Difficulty level for Proof of Work challenges, '
                    'by how many leading zeros are required in the hash',
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

    cache_driver: str = Field(
        'redis',
        description='Cache driver to use for the service',
    )
    redis_host: str = Field(
        'localhost',
        description='Redis host for the cache',
    )
    redis_port: int = Field(
        6379,
        description='Redis port for the cache',
    )

    kms_driver: str = Field(
        'vault',
        description='Key Management Service driver to use for the service',
    )
    vault_url: str = Field(
        'http://localhost:8200',
        description='URL for the HashiCorp Vault service',
    )
    vault_role_id: str = Field(
        'dedi-gateway-role',
        description='Role ID for the HashiCorp Vault service',
    )
    vault_secret_id: str = Field(
        'dedi-gateway-secret',
        description='Secret ID for the HashiCorp Vault service',
    )
    vault_kv_engine: str = Field(
        'kv',
        description='KV engine name for the HashiCorp Vault service',
    )
    vault_kv_path: str = Field(
        'dedi-gateway',
        description='Root path for the KV store used by the '
                    'Decentralised Discovery Gateway service',
    )
    vault_transit_engine: str = Field(
        'transit',
        description='Transit engine name for the HashiCorp Vault service',
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
