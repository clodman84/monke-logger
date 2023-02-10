import functools
import itertools
import sqlite3
import time
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
    theme: str
    datetime: datetime
    name: str
    value: float

    def write_benchmark(self, conn=None):
        # look into adapters and convertors and all that later for this, maybe a __conform__ or something
        with conn if conn else connect() as connection:
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


def record_factory(theme, cursor: sqlite3.Cursor, row: tuple) -> Record:
    values = {}
    time = row[0]
    for idx, col in enumerate(cursor.description):
        column_name = col[0]
        if column_name == "timestamp":
            continue
        values[col[0]] = row[idx]
    return Record(theme, time, values)


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
        cursor = connection.execute(f"SELECT * FROM {theme}_benchmarks ORDER BY name")
        benchmarks = [Benchmark(theme, *row) for row in cursor.fetchall()]
    # splitting the benchmarks by name
    sorted_benchmarks = [
        list(group) for _, group in itertools.groupby(benchmarks, key=lambda x: x.name)
    ]
    return sorted_benchmarks


def view_records(theme: str) -> list[Record]:
    with connect() as connection:
        connection.row_factory = functools.partial(record_factory, theme)
        cursor = connection.execute(f"SELECT * FROM {theme}_records")
        records = list(cursor.fetchall())
    connection.close()
    return records


def setup_db():
    with open("schema.sql") as file:
        query = "".join(file.readlines())
    with connect() as connection:
        connection.executescript(query)
    connection.close()


def fill_it_with_junk():
    create_theme("exercise")  # <- This is how you make a theme
    create_record("exercise", "arms")  # <- Records store daily activities
    create_record("exercise", "shoulder")  # !! Records should be made only once !!
    for _ in range(5):
        # Records objects are responsible for dealing with this data.
        # Create one of these with a theme, a date, and a dictionary storing the values you want to write
        # In this case, the dictionary store the 'intensity' or something, the numbers are given meaning by
        # the user.
        # r = Record(<theme>, <time>, <values>)
        # then r.write_record() will write the data into the database.
        time.sleep(1)
        Record("exercise", datetime.now(), {"arms": 10, "shoulder": 15}).write_record()

    # you can create multiple themes
    create_theme("study")
    create_record("study", "maths")
    create_record("study", "chemistry")
    for _ in range(5):
        time.sleep(1)
        Record("study", datetime.now(), {"maths": 10, "chemistry": 15}).write_record()

    create_benchmark("exercise", "pushups")
    create_benchmark("study", "Mock Test")

    # Benchmarks only have one value and can be anything, you do not have to create a record for these
    for _ in range(10):
        Benchmark("exercise", datetime.now(), "pushups", 10).write_benchmark()

    for i in range(10):
        Benchmark("study", datetime.now(), f"Mock Test", 100).write_benchmark()


if __name__ == "__main__":
    setup_db()
    fill_it_with_junk()
