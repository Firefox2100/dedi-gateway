import asyncio
from quart import Quart

from dedi_gateway.etc.consts import SCHEDULER
from dedi_gateway.etc.utils import scheduler_add_initial_jobs
from dedi_gateway.model.network_message.registry import NetworkMessageRegistry
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

    NetworkMessageRegistry.load_packages()

    @app.before_serving
    async def startup():
        scheduler_add_initial_jobs()
        if not SCHEDULER.running:
            SCHEDULER.start()
        else:
            SCHEDULER.resume()

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
