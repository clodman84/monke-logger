import itertools
import sqlite3
from dataclasses import dataclass
from datetime import datetime


def adapt_datetime_epoch(val: datetime):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())


def convert_timestamp(val):
    """Convert Unix epoch timestamp to datetime.datetime object."""
    return datetime.fromtimestamp(int(val))


sqlite3.register_adapter(datetime, adapt_datetime_epoch)
sqlite3.register_converter("timestamp", convert_timestamp)


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect("data.db", detect_types=sqlite3.PARSE_DECLTYPES)
    connection.execute("pragma foreign_keys = ON")
    return connection


@dataclass()
class Benchmark:
    datetime: datetime
    theme: str
    name: str
    value: float

    def write_benchmark(self, conn=None):
        with conn if conn else connect() as connection:
            create_benchmark(self.theme, self.name, connection)
            connection.execute(
                f"INSERT INTO benchmarks VALUES(?, ?, ?, ?)",
                (self.datetime, self.theme, self.name, self.value),
            )

    def __str__(self):
        return f"{self.datetime.strftime('%d/%m/%Y %H:%M:%S')} | {self.theme} | {self.value}"


@dataclass()
class Record:
    theme: str
    datetime: datetime
    values: dict

    def write_record(self, conn=None):
        query = f"INSERT INTO records VALUES(?, ?, ?, ?)"
        with conn if conn else connect() as connection:
            connection.executemany(
                query,
                tuple(
                    (self.datetime, self.theme, key, value)
                    for key, value in self.values.items()
                ),
            )

    def __str__(self):
        return f"{self.datetime.strftime('%d/%m/%Y %H:%M:%S')} | {self.theme} | {self.values}"


def create_theme(theme: str, conn=None) -> None:
    with conn if conn else connect() as connection:
        connection.execute("INSERT OR IGNORE INTO themes VALUES(?)", (theme,))


def create_record(theme, name, conn=None) -> None:
    with conn if conn else connect() as connection:
        connection.execute(
            f"INSERT OR IGNORE INTO themes_records_bridge VALUES(?, ?)", (theme, name)
        )


def create_benchmark(theme, name, conn=None) -> None:
    with conn if conn else connect() as connection:
        connection.execute(
            f"INSERT OR IGNORE INTO themes_benchmarks_bridge VALUES(?, ?)",
            (theme, name),
        )


def view_themes(conn=None) -> list[str]:
    with conn if conn else connect() as connection:
        cursor = connection.execute("SELECT * FROM themes;")
    return list(itertools.chain(*cursor.fetchall()))


def view_benchmarks(theme: str, conn=None) -> list[list[Benchmark]]:
    with conn if conn else connect() as connection:
        cursor = connection.execute(
            f"SELECT * FROM benchmarks WHERE theme = ? ORDER BY benchmark_name, timestamp DESC",
            (theme,),
        )
        benchmarks = [Benchmark(*row) for row in cursor.fetchall()]
    # splitting the benchmarks by name
    sorted_benchmarks = [
        list(group) for _, group in itertools.groupby(benchmarks, key=lambda x: x.name)
    ]
    return sorted_benchmarks


def view_records(theme: str) -> list[Record]:
    with connect() as connection:
        cursor = connection.execute(
            f"SELECT * FROM records WHERE theme = ? ORDER BY timestamp", (theme,)
        )
    grouped_records_by_timestamp = [
        Record(theme, t, {x[2]: x[3] for x in group})
        for t, group in itertools.groupby(cursor.fetchall(), key=lambda x: x[0])
    ]
    connection.close()
    return grouped_records_by_timestamp


def view_record_types(theme: str, conn=None):
    with conn if conn else connect() as connection:
        cursor = connection.execute(
            "SELECT record_name from themes_records_bridge WHERE theme = ?", (theme,)
        )
    return list(itertools.chain(*cursor.fetchall()))


def setup_db():
    with open("schema.sql") as file:
        query = "".join(file.readlines())
    with connect() as connection:
        connection.executescript(query)
    connection.close()


if __name__ == "__main__":
    Record("exercise", datetime.now(), {"arms": 10}).write_record()
    setup_db()
