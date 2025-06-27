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


SERVICE_CONFIG = ServiceConfig()        # type: ignore
