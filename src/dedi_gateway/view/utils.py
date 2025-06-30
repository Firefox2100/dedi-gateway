from functools import wraps
from quart import jsonify

from dedi_gateway.etc.consts import LOGGER
from dedi_gateway.etc.errors import DediGatewayException


def exception_handler(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except DediGatewayException as e:
            response = jsonify({'error': e.message})
            response.status_code = e.status_code

            if e.status_code == 401:
                # Add WWW-Authenticate header
                response.headers['WWW-Authenticate'] = 'Signature realm="dedi-link"'

            LOGGER.exception('Dedi Gateway Exception: %s', e.message)

            return response
        except Exception as e:
            response = jsonify({'error': str(e)})
            response.status_code = 500

            LOGGER.exception('Internal Server Error')

            return response

    return wrapper
