import random
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from mysql.connector import connect
from mysql.connector.types import ParamsSequenceOrDictType, RowType


def _gen_uuid() -> str:
    """Generate a uuid with the length of 6."""
    # Alphanumeric ASCII except O (uppercase letter "o") and 0 (zero)
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNPQRSTUWVXYZ123456789"  # noqa
    return "".join([random.choice(allowed_chars) for _ in range(6)])


class Database:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        port: str = "3306",
    ) -> None:
        self.using_sqlite = False
        self.connection = connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
        )
        self.cursor = self.connection.cursor()
        self.p = "%s"
        self.lock: Optional[Lock] = None

    @classmethod
    def init_sqlite(cls, path: Path) -> "Database":
        obj = cls.__new__(cls)
        obj.using_sqlite = True
        obj.connection = sqlite3.connect(path, check_same_thread=False)
        obj.cursor = obj.connection.cursor()
        obj.p = "?"
        obj.lock = Lock()
        return obj

    def create_output(self) -> str:
        """
        Create a new output entry. Returns the uuid of the new output.
        """
        uuid = _gen_uuid()
        ts = str(int(time.time()))
        self._create(
            "outputs", (
                "uuid", "output", "timestamp"
            ), (uuid, "", ts)
        )
        return uuid

    def delete_output(self, uuid: str) -> None:
        self._execute_query(
            query=f"DELETE FROM outputs WHERE uuid = {self.p}",
            params=(uuid,),
        )

    def get_output(self, uuid: str) -> str:
        return self._fetch_value("outputs", uuid, "output")

    def append_to_output(self, uuid: str, content: str) -> None:
        output = self._fetch_value("outputs", uuid, "output")
        new_output = output + content
        self._update("outputs", uuid, "output", new_output)

    def fetch_timestamp(self, uuid: str) -> int:
        return int(self._fetch_value("outputs", uuid, "timestamp"))

    def update_timestamp(self, uuid: str) -> None:
        self._update("outputs", uuid, "timestamp", str(int(time.time())))

    def has_output(self, uuid: str) -> bool:
        return bool(self._fetch_data(
            f"SELECT * FROM outputs WHERE uuid = {self.p}",
            params=(uuid,),
        ))

    def get_uuids(self) -> list[str]:
        result = self._fetch_data("SELECT uuid FROM outputs")
        if result:
            return result[0]
        return result

    def _execute_query(
        self,
        query: str,
        params: ParamsSequenceOrDictType = (),
    ) -> None:
        with self.lock:
            self._ensure_connected()
            self.cursor.execute(query, params)
            self.connection.commit()

    def _fetch_data(
        self,
        query: str,
        params: ParamsSequenceOrDictType = (),
    ) -> list[RowType]:
        with self.lock:
            self._ensure_connected()
            self.cursor.execute(query, params)
            return self.cursor.fetchall()

    def _fetch_value(
        self,
        table: str,
        uuid: str,
        field: str,
    ):
        result = self._fetch_data(
            f"SELECT {field} FROM {table} WHERE uuid = {self.p}",
            params=(uuid,)
        )
        try:
            value = result[0][0]  # Twice cause result is like `[("en_US",)]`
        except IndexError:
            value = None
        return value

    def _update(
        self,
        table: str,
        uuid: str,
        field: str,
        value: Any,
    ):
        if self._fetch_data(
            f"SELECT * FROM {table} WHERE uuid = {self.p}",
            params=(uuid,),
        ):
            self._execute_query(
                f"UPDATE {table} SET {field} = {self.p} WHERE uuid = {self.p}",
                params=(value, uuid),
            )
        else:
            raise RuntimeError(
                f"Entry with uuid {uuid} in table {table} doesn't exist."
            )

    def _create(self, table: str, fields: tuple[str], values: tuple[Any]):
        self._execute_query(
            f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join([self.p] * len(values))})",  # noqa
            params=values,
        )

    def _ensure_connected(self):
        if self.using_sqlite:
            return
        if not self.connection.is_connected():
            self.connection.reconnect(10)

    def close(self) -> None:
        self.cursor.close()
        self.connection.close()
