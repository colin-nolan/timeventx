from typing import Iterable

from garden_water.timers.collections.abc import IdentifiableTimersCollection
from garden_water.timers.serialisation import deserialise_daytime, serialise_daytime
from garden_water.timers.timers import IdentifiableTimer, Timer, TimerId

# from sqlalchemy import CHAR, Column, Integer, Interval, String, create_engine
# from sqlalchemy.exc import IntegrityError, NoResultFound
# from sqlalchemy.orm import declarative_base, sessionmaker


# Base = declarative_base()
#
#
# class _DbTimer(Base):
#     __tablename__ = "timers"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String, nullable=False)
#     start_time = Column(CHAR(8), nullable=False)
#     duration = Column(Interval, nullable=False)
#
#
# class TimersDatabase(IdentifiableTimersCollection):
#     def __init__(self, database_url: str):
#         self._db_engine = create_engine(database_url)
#         Base.metadata.create_all(self._db_engine)
#         self._DbSession = sessionmaker(bind=self._db_engine)
#
#     def __iter__(self) -> Iterable[IdentifiableTimer]:
#         with self._DbSession() as session:
#             db_timers = session.query(_DbTimer).all()
#         yield from (
#             IdentifiableTimer(
#                 timer_id=TimerId(db_timer.id),
#                 name=db_timer.name,
#                 start_time=deserialise_daytime(db_timer.start_time),
#                 duration=db_timer.duration,
#             )
#             for db_timer in db_timers
#         )
#
#     def __len__(self) -> int:
#         with self._DbSession() as session:
#             return session.query(_DbTimer).count()
#
#     def get(self, timer_id: TimerId) -> IdentifiableTimer:
#         with self._DbSession() as session:
#             try:
#                 db_timer = session.query(_DbTimer).filter(_DbTimer.id == timer_id).one()
#             except NoResultFound as e:
#                 raise KeyError(timer_id) from e
#         return IdentifiableTimer(
#             timer_id=TimerId(db_timer.id),
#             name=db_timer.name,
#             start_time=deserialise_daytime(db_timer.start_time),
#             duration=db_timer.duration,
#         )
#
#     def add(self, timer: Timer | IdentifiableTimer) -> IdentifiableTimer:
#         timer_id = timer.id if isinstance(timer, IdentifiableTimer) else None
#
#         with self._DbSession() as session:
#             db_timer = _DbTimer(
#                 id=timer_id,
#                 name=timer.name,
#                 start_time=serialise_daytime(timer.start_time),
#                 duration=timer.duration,
#             )
#             session.add(db_timer)
#             try:
#                 session.commit()
#             except IntegrityError as e:
#                 raise ValueError(f"Timer with ID {timer_id} already exists") from e
#
#             return IdentifiableTimer.from_timer(timer, TimerId(db_timer.id))
#
#     def remove(self, timer_id: TimerId) -> bool:
#         with self._DbSession() as session:
#             result = session.query(_DbTimer).filter(_DbTimer.id == timer_id).delete()
#             assert result in (0, 1)
#             session.commit()
#         return result == 1


class TimersDatabase(IdentifiableTimersCollection):
    def __init__(self, database_url: str):
        raise NotImplementedError()

    def __iter__(self) -> Iterable[IdentifiableTimer]:
        raise NotImplementedError()

    def __len__(self) -> int:
        raise NotImplementedError()

    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        raise NotImplementedError()

    def add(self, timer: Timer | IdentifiableTimer) -> IdentifiableTimer:
        raise NotImplementedError()

    def remove(self, timer_id: TimerId) -> bool:
        raise NotImplementedError()