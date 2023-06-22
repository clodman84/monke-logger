import queue
import sqlite3
from dataclasses import dataclass
from datetime import datetime

sqlite3.register_adapter(datetime, lambda x: int(x.timestamp()))
sqlite3.register_converter("timestamp", lambda x: datetime.fromtimestamp(int(x)))


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(
        "data.db", detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False
    )
    connection.execute("pragma foreign_keys = ON")
    return connection


class ConnectionPool:
    _q = queue.SimpleQueue()

    def __init__(self):
        self.connection = None

    def __enter__(self) -> sqlite3.Connection:
        try:
            self.connection = self._q.get_nowait()
        except queue.Empty:
            self.connection = connect()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.connection.rollback()
        else:
            self.connection.commit()
        self._q.put(self.connection)

    @classmethod
    def close(cls):
        while not cls._q.empty():
            cls._q.get_nowait().close()


@dataclass
class Theme:
    id: int
    created_on: datetime
    name: str

    @classmethod
    def new(cls, created_on: datetime, name: str):
        with ConnectionPool() as connection:
            connection.execute(
                "INSERT INTO themes VALUES(?, ?, ?)",
                (None, created_on, name),
            )
        with ConnectionPool() as connection:
            cursor = connection.execute(
                "SELECT * FROM themes WHERE created_on = ? AND name = ?",
                (created_on, name),
            )
        return cls(*cursor.fetchone())

    def get_types(self, display_type):
        with ConnectionPool() as connection:
            cursor = connection.execute(
                "SELECT * FROM types WHERE theme_id = ? AND display_type = ? ORDER BY created_on DESC",
                (self.id, display_type),
            )
        return [DataType(*row[:2], self, *row[3:]) for row in cursor.fetchall()]


@dataclass
class DataPoint:
    type_id: int
    created_on: datetime
    timestamp: datetime
    val: int | float

    def write(self) -> None:
        with ConnectionPool() as connection:
            connection.execute(
                "INSERT INTO data VALUES(?, ?, ?, ?)",
                (self.type_id, self.created_on, self.timestamp, self.val),
            )

    def __str__(self):
        return f"Type: {self.type_id} Value: {self.val}"


@dataclass
class DataType:
    id: int
    created_on: datetime
    theme: Theme
    name: str
    unit: str
    display_type: str
    representation: str

    @classmethod
    def new(
        cls,
        created_on,
        theme: Theme,
        name,
        unit=None,
        display_type=None,
        representation=None,
    ):
        with ConnectionPool() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO types VALUES(?, ?, ?, ?, ?, ?, ?)",
                (
                    None,
                    created_on,
                    theme.id,
                    name,
                    unit,
                    display_type,
                    representation,
                ),
            )
        with ConnectionPool() as connection:
            cursor = connection.execute(
                "SELECT * FROM types WHERE name = ? AND theme_id = ?", (name, theme.id)
            )
            row = cursor.fetchone()
            return cls(*row[:2], theme, *row[3:])

    def get_data_points(self) -> list[DataPoint]:
        with ConnectionPool() as connection:
            cursor = connection.execute(
                "SELECT * FROM data WHERE type_id = ? ORDER BY timestamp ASC",
                (self.id,),
            )
            return [DataPoint(*row) for row in cursor.fetchall()]


def get_all_themes() -> list[Theme]:
    with ConnectionPool() as connection:
        cursor = connection.execute("SELECT * FROM themes;")
    return list(map(lambda x: Theme(*x), cursor.fetchall()))


def setup_db():
    with open("schema.sql") as file:
        query = "".join(file.readlines())
    with connect() as connection:
        connection.executescript(query)
    connection.close()


# this is out here on purpose
setup_db()
