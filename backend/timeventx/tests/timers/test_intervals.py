from datetime import timedelta
from typing import Iterable

import pytest

from timeventx.timers.intervals import TimeInterval, merge_and_sort_intervals
from timeventx.timers.serialisation import deserialise_daytime


def _to_time_interval(serialised_start_time: str, serialised_end_time: str) -> TimeInterval:
    return TimeInterval(deserialise_daytime(serialised_start_time), deserialise_daytime(serialised_end_time))


def _merge_and_sort_intervals(intervals: Iterable[tuple[str, timedelta]]) -> tuple[TimeInterval, ...]:
    return merge_and_sort_intervals(
        tuple(
            TimeInterval(
                deserialise_daytime(serialised_start_time), deserialise_daytime(serialised_start_time) + duration
            )
            for serialised_start_time, duration in intervals
        )
    )


class TestTimerRunner:
    def test_calculate_on_off_intervals_none(self):
        on_off_intervals = _merge_and_sort_intervals(())
        assert len(on_off_intervals) == 0

    def test_calculate_on_off_intervals_single(self):
        on_off_intervals = _merge_and_sort_intervals((("00:00:00", timedelta(minutes=10)),))
        assert len(on_off_intervals) == 1
        assert on_off_intervals[0] == _to_time_interval("00:00:00", "00:10:00")

    def test_calculate_on_off_intervals_wrap_around_midnight(self):
        on_off_intervals = _merge_and_sort_intervals((("23:55:00", timedelta(minutes=10)),))
        assert len(on_off_intervals) == 1
        assert on_off_intervals[0] == _to_time_interval("23:55:00", "00:05:00")

    def test_calculate_on_off_intervals_never_off(self):
        with pytest.raises(ValueError):
            _merge_and_sort_intervals(
                (
                    ("00:01:00", timedelta(minutes=180)),
                    ("23:00:00", timedelta(hours=5)),
                    ("01:00:00", timedelta(hours=23)),
                )
            )

    def test_calculate_on_off_intervals_never_off_regression_1(self):
        with pytest.raises(ValueError):
            _merge_and_sort_intervals(
                (
                    ("00:00:00", timedelta(hours=23)),
                    ("23:00:00", timedelta(hours=1)),
                )
            )

    def test_calculate_on_off_intervals_never_off_regression_2(self):
        with pytest.raises(ValueError):
            _merge_and_sort_intervals(
                (
                    ("23:00:00", timedelta(hours=23)),
                    ("22:00:00", timedelta(hours=1)),
                )
            )

    def test_calculate_on_off_intervals_never_off_regression_3(self):
        with pytest.raises(ValueError):
            _merge_and_sort_intervals(
                (
                    ("01:00:00", timedelta(hours=22)),
                    ("22:00:00", timedelta(hours=3)),
                )
            )

    def test_calculate_on_off_intervals_never_off_regression_4(self):
        with pytest.raises(ValueError):
            _merge_and_sort_intervals(
                (
                    ("11:30:00", timedelta(hours=23)),
                    ("10:00:00", timedelta(hours=4)),
                )
            )

    def test_calculate_on_off_intervals_never_off_regression_5(self):
        with pytest.raises(ValueError):
            _merge_and_sort_intervals(
                (
                    ("23:30:00", timedelta(hours=23)),
                    ("22:00:00", timedelta(hours=4)),
                )
            )

    def test_calculate_on_off_intervals_multiple_no_overlaps(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("00:00:00", timedelta(minutes=10)),
                ("02:00:00", timedelta(minutes=30)),
                ("01:00:00", timedelta(minutes=20)),
            )
        )
        assert len(on_off_intervals) == 3
        assert on_off_intervals[0] == _to_time_interval("00:00:00", "00:10:00")
        assert on_off_intervals[1] == _to_time_interval("01:00:00", "01:20:00")
        assert on_off_intervals[2] == _to_time_interval("02:00:00", "02:30:00")

    def test_calculate_on_off_intervals_repeat(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("00:00:00", timedelta(minutes=10)),
                ("00:00:00", timedelta(minutes=10)),
                ("00:00:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_intervals) == 1
        assert on_off_intervals[0] == _to_time_interval("00:00:00", "00:10:00")

    def test_calculate_on_off_intervals_all_overlaps(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("00:00:00", timedelta(minutes=10)),
                ("00:05:00", timedelta(minutes=10)),
                ("00:10:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_intervals) == 1
        assert on_off_intervals[0] == _to_time_interval("00:00:00", "00:20:00")

    def test_calculate_on_off_intervals_two_separate_overlaps(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("00:00:00", timedelta(minutes=10)),
                ("00:05:00", timedelta(minutes=15)),
                ("01:00:00", timedelta(minutes=10)),
                ("02:00:00", timedelta(minutes=30)),
                ("02:05:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_intervals) == 3
        assert on_off_intervals[0] == _to_time_interval("00:00:00", "00:20:00")
        assert on_off_intervals[1] == _to_time_interval("01:00:00", "01:10:00")
        assert on_off_intervals[2] == _to_time_interval("02:00:00", "02:30:00")

    def test_calculate_on_off_intervals_with_merge_over_midnight(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("23:50:00", timedelta(minutes=10)),
                ("01:00:00", timedelta(hours=1)),
                ("23:55:00", timedelta(minutes=10)),
                ("00:05:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_intervals) == 2
        assert on_off_intervals[0] == _to_time_interval("01:00:00", "02:00:00")
        assert on_off_intervals[1] == _to_time_interval("23:50:00", "00:15:00")

    def test_calculate_on_off_intervals_with_merge_over_midnight_many(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("00:05:00", timedelta(minutes=10)),
                ("23:00:00", timedelta(hours=23)),
                ("01:00:00", timedelta(hours=1)),
                ("23:55:00", timedelta(minutes=10)),
            )
        )
        assert len(on_off_intervals) == 1
        assert on_off_intervals[0] == _to_time_interval("23:00:00", "22:00:00")

    def test_calculate_on_off_intervals_merge_regression_1(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("00:01:00", timedelta(minutes=180)),
                ("02:00:00", timedelta(hours=5)),
                ("01:00:00", timedelta(hours=23)),
            )
        )
        assert len(on_off_intervals) == 1
        assert on_off_intervals[0] == _to_time_interval("00:01:00", "00:00:00")

    def test_calculate_on_off_intervals_merge_regression_2(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("00:01:00", timedelta(minutes=180)),
                ("23:00:00", timedelta(hours=5)),
                ("01:00:00", timedelta(hours=2)),
            )
        )
        assert len(on_off_intervals) == 1
        assert on_off_intervals[0] == _to_time_interval("23:00:00", "04:00:00")

    def test_calculate_on_off_intervals_merge_regression_3(self):
        on_off_intervals = _merge_and_sort_intervals(
            (
                ("00:01:00", timedelta(minutes=180)),
                ("23:00:00", timedelta(hours=5)),
            )
        )
        assert len(on_off_intervals) == 1
        assert on_off_intervals[0] == _to_time_interval("23:00:00", "04:00:00")
