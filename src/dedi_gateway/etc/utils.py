import json
from functools import wraps
from quart import jsonify, websocket, has_websocket_context
from werkzeug.exceptions import HTTPException

from dedi_gateway.etc.consts import LOGGER, SCHEDULER
from dedi_gateway.etc.errors import DediGatewayException


def exception_handler(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except DediGatewayException as e:
            message = {'error': e.message}
            status_code = e.status_code

            LOGGER.exception('Dedi Gateway Exception: %s', e.message)

            if has_websocket_context():
                await websocket.send(json.dumps(message))
                await websocket.close(code=4000 + status_code)
                return
            else:
                response = jsonify(message)
                response.status_code = status_code
                if status_code == 401:
                    response.headers['WWW-Authenticate'] = 'Signature realm="dedi-link"'
                return response

        except HTTPException as e:
            message = {'error': e.description}
            LOGGER.exception('HTTP Exception: %s', e.description)

            if has_websocket_context():
                await websocket.send(json.dumps(message))
                await websocket.close(code=4000 + e.code)
                return

            response = jsonify(message)
            response.status_code = e.code
            return response

        except Exception as e:
            message = {'error': str(e)}
            LOGGER.exception('Internal Server Error')

            if has_websocket_context():
                await websocket.send(json.dumps(message))
                await websocket.close(code=4500)
                return

            response = jsonify(message)
            response.status_code = 500
            return response

    return wrapper


def scheduler_add_initial_jobs():
    """
    Add jobs that are tied to application cycle, and should be run regardless of
    the operations handled.
    """
