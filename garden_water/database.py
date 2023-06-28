from sqlalchemy import Boolean, Column, DateTime, Integer, Interval, String, create_engine
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import declarative_base, sessionmaker

from garden_water.models import Timer, TimerId, TimersContainer, IdentifiableTimer

Base = declarative_base()


class _DbTimer(Base):
    __tablename__ = "timers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration = Column(Interval, nullable=False)
    enabled = Column(Boolean, nullable=False)


class TimersDatabase(TimersContainer):
    def __init__(self, database_url: str):
        self._db_engine = create_engine(database_url)
        Base.metadata.create_all(self._db_engine)
        self._DbSession = sessionmaker(bind=self._db_engine)

    def get_all(self) -> tuple[IdentifiableTimer]:
        with self._DbSession() as session:
            db_timers = session.query(_DbTimer).all()
        return tuple(
            IdentifiableTimer(
                id=TimerId(db_timer.id),
                name=db_timer.name,
                start_time=db_timer.start_time,
                duration=db_timer.duration,
                enabled=db_timer.enabled,
            )
            for db_timer in db_timers
        )

    def get(self, timer_id: TimerId) -> IdentifiableTimer:
        with self._DbSession() as session:
            try:
                db_timer = session.query(_DbTimer).filter(_DbTimer.id == timer_id).one()
            except NoResultFound as e:
                raise KeyError(timer_id) from e
        return IdentifiableTimer(
            id=TimerId(db_timer.id),
            name=db_timer.name,
            start_time=db_timer.start_time,
            duration=db_timer.duration,
            enabled=db_timer.enabled,
        )

    def add(self, timer: Timer) -> IdentifiableTimer:
        identifier = timer.id if isinstance(timer, IdentifiableTimer) else None
        with self._DbSession() as session:
            db_timer = _DbTimer(
                id=identifier,
                name=timer.name,
                start_time=timer.start_time,
                duration=timer.duration,
                enabled=timer.enabled,
            )
            session.add(db_timer)
            try:
                session.commit()
            except IntegrityError as e:
                raise ValueError(f"Timer with ID {timer.id} already exists") from e

            return IdentifiableTimer.from_timer(timer, TimerId(db_timer.id))

    def remove(self, timer_id: TimerId) -> bool:
        with self._DbSession() as session:
            result = session.query(_DbTimer).filter(_DbTimer.id == timer_id).delete()
            assert result in (0, 1)
            session.commit()
        return result == 1
