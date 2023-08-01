from contextlib import contextmanager
from typing import Iterable

from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.serialisation import deserialise_daytime, serialise_daytime
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId

try:
    import usqlite3 as sqlite3
except ImportError:
    import sqlite3


class TimersDatabase(IdentifiableTimersCollection):
    TIMERS_TABLE_NAME = "Timer"

    @property
    @contextmanager
    def _db_connection(self) -> sqlite3.Connection:
        with sqlite3.connect(self._database_location) as connection:
            yield connection

    def _create_tables(self):
        with self._db_connection as connection:
            connection.executemany(
                f"""
                CREATE TABLE IF NOT EXISTS {TimersDatabase.TIMERS_TABLE_NAME} (name TEXT, year INT);
            """
            )

    def __init__(self, database_location: str):
        self.database_location = database_location

    def __iter__(self) -> Iterable[IdentifiableTimer]:
        with self._db_connection as connection:
            with connection.execute(f"SELECT * from {TimersDatabase.TIMERS_TABLE_NAME}") as cur:
                for row in cur:
                    print("stooge:", row)

        # with self._DbSession() as session:
        #     db_timers = session.query(_DbTimer).all()
        # yield from (
        #     IdentifiableTimer(
        #         timer_id=TimerId(db_timer.id),
        #         name=db_timer.name,
        #         start_time=deserialise_daytime(db_timer.start_time),
        #         duration=db_timer.duration,
        #     )
        #     for db_timer in db_timers
        # )

    def __len__(self) -> int:
        with self._DbSession() as session:
            return session.query(_DbTimer).count()

    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        with self._DbSession() as session:
            try:
                db_timer = session.query(_DbTimer).filter(_DbTimer.id == timer_id).one()
            except NoResultFound as e:
                raise KeyError(timer_id) from e
        return IdentifiableTimer(
            timer_id=TimerId(db_timer.id),
            name=db_timer.name,
            start_time=deserialise_daytime(db_timer.start_time),
            duration=db_timer.duration,
        )

    def add(self, timer: Timer | IdentifiableTimer) -> IdentifiableTimer:
        timer_id = timer.id if isinstance(timer, IdentifiableTimer) else None

        with self._DbSession() as session:
            db_timer = _DbTimer(
                id=timer_id,
                name=timer.name,
                start_time=serialise_daytime(timer.start_time),
                duration=timer.duration,
            )
            session.add(db_timer)
            try:
                session.commit()
            except IntegrityError as e:
                raise ValueError(f"Timer with ID {timer_id} already exists") from e

            return IdentifiableTimer.from_timer(timer, TimerId(db_timer.id))

    def remove(self, timer_id: TimerId) -> bool:
        with self._DbSession() as session:
            result = session.query(_DbTimer).filter(_DbTimer.id == timer_id).delete()
            assert result in (0, 1)
            session.commit()
        return result == 1
