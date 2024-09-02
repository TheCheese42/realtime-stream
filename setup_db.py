"""Run this to initially set up a new database."""
import os
import sqlite3
from pathlib import Path

import dotenv
from mysql.connector import Error, connect

CREATE_QUERY = """CREATE TABLE `outputs` (
                    `uuid` char(6) NOT NULL PRIMARY KEY,
                    `output` text DEFAULT "" NOT NULL,
                    `timestamp` varchar(20) NOT NULL
                )"""


def setup_mysql(
    host: str,
    port: str,
    username: str,
    password: str,
    database: str,
) -> None:
    """
    Setup an mysql database. ONLY USE THIS WHEN A DATABASE ISN'T SET UP YET.

    :param host: IP to the DB host.
    :type host: str
    :param port: Port to the DB host. Usually 3306.
    :type port: str
    :param username: Mysql username.
    :type username: str
    :param password: Mysql password.
    :type password: str
    :param database: Database name in the target server.
    :type database: str
    """
    with connect(
        host=host,
        port=port,
        user=username,
        password=password,
        database=database,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_QUERY)
            connection.commit()


def setup_sqlite(path: Path) -> None:
    """
    Setup an sqlite database. ONLY USE THIS WHEN A DATABASE ISN'T SET UP YET.
    """
    with sqlite3.connect(path) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(CREATE_QUERY)
            connection.commit()
        finally:
            cursor.close()


if __name__ == "__main__":
    dotenv.load_dotenv(Path(__file__).parent / ".env")
    use_sqlite = os.getenv("RTS_USE_SQLITE") == "1"
    sqlite_path = os.getenv("RTS_SQLITE_PATH")
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USERNAME")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")
    port = os.getenv("MYSQL_PORT")

    def malformed_dotenv(missing_key: str):
        raise RuntimeError(f"Malformed .env: Missing key '{missing_key}'")

    if host is None and not use_sqlite:
        malformed_dotenv("MYSQL_HOST")
    if user is None and not use_sqlite:
        malformed_dotenv("MYSQL_USERNAME")
    if password is None and not use_sqlite:
        malformed_dotenv("MYSQL_PASSWORD")
    if database is None and not use_sqlite:
        malformed_dotenv("MYSQL_DATABASE")

    if use_sqlite:
        setup_sqlite(sqlite_path)
    else:
        setup_mysql(
            host=host,
            port=port or "3306",
            username=user,
            password=password,
            database=database,
        )
