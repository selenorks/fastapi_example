import pytest

from app.forecast import filter_day_temp_forecast, DayTempForecast
from datetime import datetime


@pytest.mark.parametrize(
    "day_temp_forecast, expected",
    (
        # before Summer time in Serbia
        ("2025-10-25T12:00:00+00:00", True),
        ("2025-10-25T11:00:00-01:00", True),
        ("2025-10-25T11:00:00-01:00", True),
        ("2025-10-25T13:00:00+00:00", False),
        ("2025-10-25T13:00:00+00:00", False),
        # # Winter time in Serbia
        ("2025-10-26T12:00:00+00:00", False),
        ("2025-10-26T13:00:00+00:00", True),
        ("2025-10-26T14:00:00+00:00", False),
    ),
)
def test_filter_by_time(day_temp_forecast, expected):
    temp = DayTempForecast(timestamp=datetime.fromisoformat(day_temp_forecast), temp=18)
    assert filter_day_temp_forecast(temp) is expected
