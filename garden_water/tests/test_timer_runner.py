from datetime import timedelta
from typing import Iterable

import pytest

from garden_water.tests._common import create_example_timer
from garden_water.timer_runner import TimerRunner
from garden_water.timers.collections.memory import InMemoryIdentifiableTimersCollection
from garden_water.timers.serialisation import deserialise_daytime
from garden_water.timers.timers import DayTime, TimeInterval


def _create_timer_runner(start_duration_pairs: Iterable[tuple[str, timedelta]]) -> TimerRunner:
    timers = (create_example_timer(start_time, duration) for start_time, duration in start_duration_pairs)
    return TimerRunner(InMemoryIdentifiableTimersCollection(timers))


def _calculate_on_off_times(timers_start_duration_pairs: Iterable[tuple[str, timedelta]]) -> tuple[TimeInterval, ...]:
    timer_runner = _create_timer_runner(timers_start_duration_pairs)
    return timer_runner.calculate_on_off_times()


def _to_time_interval(serialised_start_time: str, serialised_end_time: str) -> TimeInterval:
    return TimeInterval(deserialise_daytime(serialised_start_time), deserialise_daytime(serialised_end_time))


class TestTimerRunner:
    def test_calculate_on_off_times_none(self):
        on_off_times = _calculate_on_off_times(())
        assert len(on_off_times) == 0

    def test_calculate_on_off_times_single(self):
        on_off_times = _calculate_on_off_times((("00:00:00", timedelta(minutes=10)),))
        assert len(on_off_times) == 1
        assert on_off_times[0] == _to_time_interval("00:00:00", "00:10:00")

    def test_calculate_on_off_times_wrap_around_midnight(self):
        on_off_times = _calculate_on_off_times((("23:55:00", timedelta(minutes=10)),))
        assert len(on_off_times) == 1
        assert on_off_times[0] == _to_time_interval("23:55:00", "00:05:00")

    def test_calculate_on_off_times_never_off(self):
        with pytest.raises(ValueError):
            _calculate_on_off_times(
                (
                    ("00:01:00", timedelta(minutes=180)),
                    ("23:00:00", timedelta(hours=5)),
                    ("01:00:00", timedelta(hours=23)),
                )
            )

    def test_calculate_on_off_times_multiple_no_overlaps(self):
        on_off_times = _calculate_on_off_times(
            (
                ("00:00:00", timedelta(minutes=10)),
                ("02:00:00", timedelta(minutes=30)),
                ("01:00:00", timedelta(minutes=20)),
            )
        )
        assert len(on_off_times) == 3
        assert on_off_times[0] == _to_time_interval("00:00:00", "00:10:00")
        assert on_off_times[1] == _to_time_interval("01:00:00", "01:20:00")
        assert on_off_times[2] == _to_time_interval("02:00:00", "02:30:00")

    def test_calculate_on_off_times_repeat(self):
        on_off_times = _calculate_on_off_times(
            (
                ("00:00:00", timedelta(minutes=10)),
                ("00:00:00", timedelta(minutes=10)),
                ("00:00:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_times) == 1
        assert on_off_times[0] == _to_time_interval("00:00:00", "00:10:00")

    def test_calculate_on_off_times_all_overlaps(self):
        on_off_times = _calculate_on_off_times(
            (
                ("00:00:00", timedelta(minutes=10)),
                ("00:05:00", timedelta(minutes=10)),
                ("00:10:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_times) == 1
        assert on_off_times[0] == _to_time_interval("00:00:00", "00:20:00")

    def test_calculate_on_off_times_two_separate_overlaps(self):
        on_off_times = _calculate_on_off_times(
            (
                ("00:00:00", timedelta(minutes=10)),
                ("00:05:00", timedelta(minutes=15)),
                ("01:00:00", timedelta(minutes=10)),
                ("02:00:00", timedelta(minutes=30)),
                ("02:05:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_times) == 3
        assert on_off_times[0] == _to_time_interval("00:00:00", "00:20:00")
        assert on_off_times[1] == _to_time_interval("01:00:00", "01:10:00")
        assert on_off_times[2] == _to_time_interval("02:00:00", "02:30:00")

    def test_calculate_on_off_times_with_merge_over_midnight(self):
        on_off_times = _calculate_on_off_times(
            (
                ("23:50:00", timedelta(minutes=10)),
                ("01:00:00", timedelta(hours=1)),
                ("23:55:00", timedelta(minutes=10)),
                ("00:05:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_times) == 2
        assert on_off_times[0] == _to_time_interval("01:00:00", "02:00:00")
        assert on_off_times[1] == _to_time_interval("23:50:00", "00:15:00")

    def test_calculate_on_off_times_with_merge_over_midnight_many(self):
        on_off_times = _calculate_on_off_times(
            (
                ("00:05:00", timedelta(minutes=10)),
                ("23:00:00", timedelta(hours=23)),
                ("01:00:00", timedelta(hours=1)),
                ("23:55:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_times) == 1
        assert on_off_times[0] == _to_time_interval("23:00:00", "22:00:00")

    def test_calculate_on_off_times_merge_regression_1(self):
        on_off_times = _calculate_on_off_times(
            (
                ("00:01:00", timedelta(minutes=180)),
                ("02:00:00", timedelta(hours=5)),
                ("01:00:00", timedelta(hours=23)),
            )
        )
        assert len(on_off_times) == 1
        assert on_off_times[0] == _to_time_interval("00:01:00", "00:00:00")

    def test_calculate_on_off_times_merge_regression_2(self):
        on_off_times = _calculate_on_off_times(
            (
                ("00:01:00", timedelta(minutes=180)),
                ("23:00:00", timedelta(hours=5)),
                ("01:00:00", timedelta(hours=2)),
            )
        )
        assert len(on_off_times) == 1
        assert on_off_times[0] == _to_time_interval("23:00:00", "04:00:00")

    def test_calculate_on_off_times_merge_regression_3(self):
        on_off_times = _calculate_on_off_times(
            (
                ("00:01:00", timedelta(minutes=180)),
                ("23:00:00", timedelta(hours=5)),
            )
        )
        assert len(on_off_times) == 1
        assert on_off_times[0] == _to_time_interval("23:00:00", "04:00:00")
