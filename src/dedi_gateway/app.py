import asyncio
from quart import Quart

from dedi_gateway.view import management_blueprint, service_blueprint


def create_app() -> Quart:
    """
    Create and configure the Quart application.

    :return: Configured Quart application instance
    """
    app = Quart(__name__)

    # Register blueprints
    app.register_blueprint(management_blueprint, url_prefix='/manage')
    app.register_blueprint(service_blueprint, url_prefix='/service')

    return app


if __name__ == '__main__':
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config.from_mapping(
        bind=['0.0.0.0:5321'],
        use_reloader=False,
    )
    asgi_app = create_app()

    asyncio.run(serve(asgi_app, config))
