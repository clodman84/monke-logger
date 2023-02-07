import functools
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
    return sqlite3.connect("data.db", detect_types=sqlite3.PARSE_DECLTYPES)


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
                f"INSERT INTO {self.theme}_benchmarks VALUES(?, ?, ?)",
                (self.datetime, self.name, self.value),
            )

    def __str__(self):
        return f"{self.datetime.strftime('%d/%m/%Y %H:%M:%S')} | {self.theme} | {self.value}"


@dataclass()
class Record:
    theme: str
    datetime: datetime
    values: dict

    def write_record(self, conn=None):
        query = (
            f"INSERT INTO {self.theme}_records (timestamp, {', '.join(self.values.keys())}) "
            f"VALUES(?{',?'*len(self.values)});"
        )
        with conn if conn else connect() as connection:
            connection.execute(query, (self.datetime, *self.values.values()))

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
        connection.executescript(
            f"""
        CREATE TABLE IF NOT EXISTS {theme}_benchmarks(
            timestamp TIMESTAMP,
            name TEXT,
            value INTEGER
        );

        CREATE TABLE IF NOT EXISTS {theme}_records(
            timestamp TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS themes(
            themes TEXT PRIMARY KEY
        );
        """
        )
        connection.execute("INSERT OR IGNORE INTO themes VALUES(?)", (theme,))


def create_record(theme, name, conn=None) -> None:
    with conn if conn else connect() as connection:
        create_theme(theme, connection)
        connection.execute(f"ALTER TABLE {theme}_records ADD {name} INTEGER;")


def view_themes(conn=None) -> list[str]:
    with conn if conn else connect() as connection:
        cursor = connection.execute("SELECT * FROM themes;")
        return list(itertools.chain(*cursor.fetchall()))


def view_benchmarks(theme: str, conn=None) -> list[Benchmark]:
    with conn if conn else connect() as connection:
        cursor = connection.execute(f"SELECT * FROM {theme}_benchmarks")
        benchmarks = [Benchmark(theme, *row) for row in cursor.fetchall()]
    return benchmarks


def view_records(theme: str) -> list[Record]:
    with connect() as connection:
        connection.row_factory = functools.partial(record_factory, theme)
        cursor = connection.execute(f"SELECT * FROM {theme}_records")
        records = list(cursor.fetchall())
    connection.close()
    return records


def fill_it_with_junk():
    create_theme("exercise")  # <- This is how you make a theme
    create_record("exercise", "arms")  # <- Records store daily activities
    create_record("exercise", "shoulder")  # !! Records should be made only once !!
    for _ in range(15):
        # Records objects are responsible for dealing with this data.
        # Create one of these with a theme, a date, and a dictionary storing the values you want to write
        # In this case, the dictionary store the 'intensity' or something, the numbers are given meaning by
        # the user.
        # r = Record(<theme>, <time>, <values>)
        # then r.write_record() will write the data into the database.
        Record("exercise", datetime.now(), {"arms": 10}).write_record()
        Record("exercise", datetime.now(), {"arms": 10, "shoulder": 15}).write_record()

    # you can create multiple themes
    create_theme("study")
    create_record("study", "maths")
    create_record("study", "chemistry")
    for _ in range(15):
        Record("study", datetime.now(), {"maths": 10}).write_record()
        Record("study", datetime.now(), {"maths": 10, "chemistry": 15}).write_record()

    # Benchmarks only have one value and can be anything, you do not have to create a record for these
    for _ in range(10):
        Benchmark("exercise", datetime.now(), "pushups", 10).write_benchmark()

    for i in range(10):
        Benchmark("study", datetime.now(), f"Mock Test {i + 1}", 100).write_benchmark()


if __name__ == "__main__":
    print("creating and filling the database with junk")
    print("_" * 25)
    fill_it_with_junk()
    print("Exercise:")
    for line in view_records("exercise"):
        # view_records and view_benchmarks both return a list of Records and Benchmarks respectively
        print(line)

    for line in view_benchmarks("exercise"):
        print(line)

    print("_" * 25)
    print("Study:")
    for line in view_records("study"):
        print(line)

    for line in view_benchmarks("study"):
        print(line)
