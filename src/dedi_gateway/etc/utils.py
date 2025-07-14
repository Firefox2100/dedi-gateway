import json
import random
from datetime import datetime, timedelta
from functools import wraps
from quart import jsonify, websocket, has_websocket_context
from werkzeug.exceptions import HTTPException

from dedi_gateway.etc.consts import LOGGER, SCHEDULER
from dedi_gateway.etc.errors import DediGatewayException
from dedi_gateway.database import get_active_db
from dedi_gateway.model.network_interface import SyncInterface, establish_all_connections


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


async def sync_all_nodes():
    """
    Sync all nodes in all networks with the latest data.
    :return:
    """
    try:
        db = get_active_db()
        interface = SyncInterface()

        networks = await db.networks.filter()

        for network in networks:
            try:
                LOGGER.info('Syncing network %s', network.network_id)
                await interface.sync_known_nodes(network.network_id)
                LOGGER.info('Synchronised network %s successfully', network.network_id)
            except DediGatewayException as e:
                LOGGER.exception('Failed to sync network %s: %s', network.network_id, e.message)
            except Exception:
                LOGGER.exception('Unexpected error while syncing network %s', network.network_id)
    except Exception:
        LOGGER.exception('Synchronisation interrupted, not all networks were synced')


async def sync_all_index():
    """
    Sync all data indices across all networks.
    """
    try:
        db = get_active_db()
        interface = SyncInterface()

        networks = await db.networks.filter()

        for network in networks:
            try:
                LOGGER.info('Syncing data index for network %s', network.network_id)
                await interface.sync_data_index(network.network_id)
                LOGGER.info(
                    'Data index for network %s synchronised successfully',
                    network.network_id
                )
            except DediGatewayException as e:
                LOGGER.exception(
                    'Failed to sync data index for network %s: %s',
                    network.network_id,
                    e.message
                )
            except Exception:
                LOGGER.exception(
                    'Unexpected error while syncing data index for network %s',
                    network.network_id
                )
    except Exception:
        LOGGER.exception(
            'Synchronisation of data indices interrupted, not all networks were synced'
        )


def scheduler_add_initial_jobs():
    """
    Add jobs that are tied to application cycle, and should be run regardless of
    the operations handled.
    """
    # Establish all connections to nodes every 5 minutes
    SCHEDULER.add_job(
        establish_all_connections,
        'interval',
        minutes=5,
        id='establish_all_connections',
        replace_existing=True
    )

    # Sync with all networks every 24 hours
    next_run_time = datetime.now() + timedelta(seconds=random.randint(0, 300))

    SCHEDULER.add_job(
        sync_all_nodes,
        'interval',
        hours=24,
        id='sync_all_nodes',
        replace_existing=True,
        next_run_time=next_run_time
    )
    SCHEDULER.add_job(
        sync_all_index,
        'interval',
        hours=24,
        id='sync_all_index',
        replace_existing=True,
        next_run_time=next_run_time
    )
