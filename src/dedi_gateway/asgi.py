"""
ASGI application entry point for Decentralised Discovery Gateway
"""


from dedi_gateway.app import create_app


application = create_app()
