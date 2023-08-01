from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from typing import Iterable

from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.serialisation import deserialise_daytime, serialise_daytime
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId

try:
    import usqlite as sqlite3
except ImportError:
    import sqlite3


class TimersDatabase(IdentifiableTimersCollection):
    TIMERS_TABLE_NAME = "Timer"

    @staticmethod
    def _result_to_timer(result: tuple[int, str, str, int]) -> IdentifiableTimer:
        timer_id, name, start_time, duration = result

        return IdentifiableTimer(
            timer_id=timer_id,
            name=name,
            start_time=deserialise_daytime(start_time),
            duration=timedelta(seconds=duration),
        )

    @property
    @contextmanager
    def _db_connection(self) -> sqlite3.Connection:
        with sqlite3.connect(str(self.database_location)) as connection:
            yield connection

    def _create_tables(self):
        with self._db_connection as connection:
            connection.execute(
                f"""
                    CREATE TABLE IF NOT EXISTS {TimersDatabase.TIMERS_TABLE_NAME} (
                        id INTEGER, 
                        name VARCHAR NOT NULL, 
                        start_time CHAR(8) NOT NULL, 
                        duration INTEGER NOT NULL, 
                        PRIMARY KEY (id)
                    )
                """
            )

    def __init__(self, database_location: Path):
        self.database_location = database_location
        self._create_tables()

    def __iter__(self) -> Iterable[IdentifiableTimer]:
        with self._db_connection as connection:
            results = connection.execute(
                f"""
                    SELECT * FROM {TimersDatabase.TIMERS_TABLE_NAME}
                """
            ).fetchall()

        yield from (TimersDatabase._result_to_timer(result) for result in results)

    def __len__(self) -> int:
        with self._db_connection as connection:
            return connection.execute(f"SELECT COUNT(*) from {TimersDatabase.TIMERS_TABLE_NAME}").fetchone()[0]

    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        with self._db_connection as connection:
            result = connection.execute(
                f"""
                    SELECT * FROM {TimersDatabase.TIMERS_TABLE_NAME} WHERE id = ?
                """,
                (timer_id,),
            ).fetchone()
            if result is None:
                raise KeyError(timer_id)

        return TimersDatabase._result_to_timer(result)


    def add(self, timer: Timer | IdentifiableTimer) -> IdentifiableTimer:
        timer_id = timer.id if isinstance(timer, IdentifiableTimer) else None

        with self._db_connection as connection:
            try:
                result = connection.execute(
                    f"""
                        INSERT INTO {TimersDatabase.TIMERS_TABLE_NAME} (
                            id, name, start_time, duration
                        ) VALUES (
                            ?, ?, ?, ?
                        )
                    """,
                    (
                        timer_id,
                        timer.name,
                        serialise_daytime(timer.start_time),
                        timer.duration.total_seconds(),
                    ),
                )
            except sqlite3.IntegrityError as e:
                raise ValueError(f"Timer with ID already exists: {timer_id}") from e
            # If the table has a column of type INTEGER PRIMARY KEY then that column is another alias for the rowid.
            # https://www.sqlite.org/c3ref/last_insert_rowid.html
            timer_id = TimerId(result.lastrowid)

        return IdentifiableTimer.from_timer(timer, TimerId(timer_id))

    def remove(self, timer_id: TimerId) -> bool:
        with self._db_connection as connection:
            result = connection.execute(
                f"""
                    DELETE FROM {TimersDatabase.TIMERS_TABLE_NAME} WHERE id = ?
                """,
                (timer_id,),
            )
        return result.rowcount == 1
