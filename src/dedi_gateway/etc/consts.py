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
