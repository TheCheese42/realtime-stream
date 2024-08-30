import os
import time

from mysql.connector.errors import Error as ConnectorError

try:
    from database import Database
except ModuleNotFoundError:
    from .database import Database


def delete_daemon(db: Database):
    while True:
        try:
            for uuid in db.get_uuids():
                if time.time() - int(db.fetch_timestamp(uuid)) > (os.getenv(
                    "RTSTREAM_EXPIRATION_TIME"
                ) or 60 * 60 * 24):
                    db.delete_output(uuid)
        except ConnectorError:
            pass
        time.sleep(os.getenv("RTSTREAM_DELETE_INTERVAL") or 60)
