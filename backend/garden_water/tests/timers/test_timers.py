from datetime import timedelta

import pytest

from garden_water.timers.intervals import TimeInterval
from garden_water.timers.timers import DayTime


class TestDayTime:
    def test_init_invalid_second(self):
        with pytest.raises(ValueError):
            DayTime(0, 0, 60)

    def test_init_invalid_minute(self):
        with pytest.raises(ValueError):
            DayTime(0, 60, 0)

    def test_init_invalid_hour(self):
        with pytest.raises(ValueError):
            DayTime(24, 0, 0)

    def test_eq(self):
        assert DayTime(1, 2, 3) == DayTime(1, 2, 3)

    def test_neq(self):
        assert DayTime(1, 2, 3) != DayTime(1, 2, 4)

    def test_lt(self):
        assert DayTime(1, 2, 3) < DayTime(1, 2, 4)

    def test_lte(self):
        assert DayTime(1, 2, 3) <= DayTime(1, 2, 4)
        assert DayTime(1, 2, 3) <= DayTime(1, 2, 3)

    def test_gt(self):
        assert DayTime(1, 2, 4) > DayTime(1, 2, 3)

    def test_gte(self):
        assert DayTime(1, 2, 4) >= DayTime(1, 2, 3)
        assert DayTime(1, 2, 4) >= DayTime(1, 2, 4)

    def test_comparison_regression(self):
        assert DayTime(1, 20, 0) < DayTime(2, 0, 0)

    def test_add_non_timedelta(self):
        with pytest.raises(TypeError):
            DayTime(1, 2, 3) + 5

    def test_add_timedelta(self):
        assert DayTime(1, 2, 3) + timedelta(hours=1, minutes=2, seconds=3) == DayTime(2, 4, 6)

    def test_add_timedelta_overflow_seconds(self):
        assert DayTime(0, 0, 59) + timedelta(hours=1, minutes=2, seconds=3) == DayTime(1, 3, 2)

    def test_add_timedelta_overflow_minutes(self):
        assert DayTime(0, 59, 0) + timedelta(hours=1, minutes=2, seconds=3) == DayTime(2, 1, 3)

    def test_add_timedelta_overflow_seconds_and_minutes(self):
        assert DayTime(0, 59, 59) + timedelta(hours=1, minutes=0, seconds=1) == DayTime(2, 0, 0)

    def test_add_timedelta_overflow_hours(self):
        assert DayTime(23, 0, 0) + timedelta(hours=1, minutes=2, seconds=3) == DayTime(0, 2, 3)

    def test_add_timedelta_overflow_hours_with_minutes(self):
        assert DayTime(23, 59, 0) + timedelta(hours=0, minutes=1, seconds=0) == DayTime(0, 0, 0)

    def test_add_timedelta_overflow_hours_with_seconds(self):
        assert DayTime(23, 59, 1) + timedelta(seconds=59) == DayTime(0, 0, 0)


class TestTimeInterval:
    def test_zero_time_invalid(self):
        with pytest.raises(ValueError):
            TimeInterval(DayTime(0, 0, 0), DayTime(0, 0, 0))

    def test_duration(self):
        assert TimeInterval(DayTime(0, 0, 0), DayTime(0, 0, 1)).duration == timedelta(seconds=1)
        assert TimeInterval(DayTime(0, 0, 0), DayTime(0, 1, 0)).duration == timedelta(minutes=1)
        assert TimeInterval(DayTime(0, 0, 0), DayTime(1, 0, 0)).duration == timedelta(hours=1)

    def test_duration_spanning_midnight(self):
        assert TimeInterval(DayTime(23, 59, 59), DayTime(0, 0, 1)).duration == timedelta(seconds=2)
        assert TimeInterval(DayTime(23, 59, 0), DayTime(0, 1, 0)).duration == timedelta(minutes=2)
        assert TimeInterval(DayTime(23, 0, 0), DayTime(1, 0, 0)).duration == timedelta(hours=2)

    def test_spans_midnight(self):
        assert TimeInterval(DayTime(23, 0, 0), DayTime(2, 0, 0)).spans_midnight()

    def test_spans_midnight_when_does_not(self):
        assert not TimeInterval(DayTime(1, 0, 0), DayTime(2, 0, 0)).spans_midnight()

    def test_intersects_none(self):
        assert not TimeInterval(DayTime(0, 0, 0), DayTime(1, 0, 0)).intersects(
            TimeInterval(DayTime(2, 0, 0), DayTime(3, 0, 0))
        )

    def test_intersects_start(self):
        assert TimeInterval(DayTime(0, 0, 0), DayTime(1, 0, 0)).intersects(
            TimeInterval(DayTime(0, 30, 0), DayTime(1, 30, 0))
        )

    def test_intersects_start_exactly(self):
        assert TimeInterval(DayTime(0, 30, 0), DayTime(1, 0, 0)).intersects(
            TimeInterval(DayTime(0, 30, 0), DayTime(1, 30, 0))
        )

    def test_intersects_same(self):
        assert TimeInterval(DayTime(0, 0, 0), DayTime(1, 0, 0)).intersects(
            TimeInterval(DayTime(0, 0, 0), DayTime(1, 0, 0))
        )

    def test_intersects_superset(self):
        assert TimeInterval(DayTime(0, 0, 0), DayTime(2, 0, 0)).intersects(
            TimeInterval(DayTime(0, 30, 0), DayTime(1, 30, 0))
        )

    def test_intersects_end(self):
        assert TimeInterval(DayTime(0, 45, 0), DayTime(1, 0, 0)).intersects(
            TimeInterval(DayTime(0, 30, 0), DayTime(1, 30, 0))
        )

    def test_intersects_end_exactly(self):
        assert TimeInterval(DayTime(0, 45, 0), DayTime(1, 30, 0)).intersects(
            TimeInterval(DayTime(0, 30, 0), DayTime(1, 30, 0))
        )

    def test_intersects_regression(self):
        # Test: 23:55:00 - 00:05:00 intersects 22:00:00 - 23:00:00
        assert not TimeInterval(DayTime(23, 55, 0), DayTime(0, 5, 0)).intersects(
            TimeInterval(DayTime(22, 0, 0), DayTime(23, 0, 0))
        )
