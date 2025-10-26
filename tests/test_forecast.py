from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from httpcore import URL
from httpx import patch

from app.forecast import (
    filter_day_temp_forecast,
    DayTempForecast,
    Coordinates,
    get_forecast,
)
from datetime import datetime, timezone


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


POSITIVE_RESPONSE = {
    "geometry": {"coordinates": [20.46, 1, 353], "type": "Point"},
    "properties": {
        "meta": {
            "units": {
                "air_pressure_at_sea_level": "hPa",
                "air_temperature": "celsius",
                "cloud_area_fraction": "%",
                "precipitation_amount": "mm",
                "relative_humidity": "%",
                "wind_from_direction": "degrees",
                "wind_speed": "m/s",
            },
            "updated_at": "2025-10-25T08:17:45Z",
        },
        "timeseries": [
            {
                "data": {
                    "instant": {
                        "details": {
                            "air_pressure_at_sea_level": 1013.4,
                            "air_temperature": 28.4,
                            "cloud_area_fraction": 19.5,
                            "relative_humidity": 66.5,
                            "wind_from_direction": 231.0,
                            "wind_speed": 0.7,
                        }
                    },
                    "next_1_hours": {
                        "details": {"precipitation_amount": 0.0},
                        "summary": {"symbol_code": "fair_day"},
                    },
                    "next_12_hours": {
                        "details": {},
                        "summary": {"symbol_code": "lightrainshowers_day"},
                    },
                    "next_6_hours": {
                        "details": {"precipitation_amount": 0.8},
                        "summary": {"symbol_code": "lightrainshowers_day"},
                    },
                },
                "time": "2025-10-25T12:00:00Z",
            },
            {
                "data": {
                    "instant": {
                        "details": {
                            "air_pressure_at_sea_level": 1012.9,
                            "air_temperature": 29.7,
                            "cloud_area_fraction": 23.4,
                            "relative_humidity": 59.7,
                            "wind_from_direction": 230.4,
                            "wind_speed": 1.1,
                        }
                    },
                    "next_1_hours": {
                        "details": {"precipitation_amount": 0.2},
                        "summary": {"symbol_code": "lightrainshowers_day"},
                    },
                    "next_12_hours": {
                        "details": {},
                        "summary": {"symbol_code": "lightrainshowers_day"},
                    },
                    "next_6_hours": {
                        "details": {"precipitation_amount": 0.8},
                        "summary": {"symbol_code": "lightrainshowers_day"},
                    },
                },
                "time": "2025-10-26T09:00:00Z",
            },
            {
                "data": {
                    "instant": {
                        "details": {
                            "air_pressure_at_sea_level": 1012.1,
                            "air_temperature": 30.4,
                            "cloud_area_fraction": 21.9,
                            "relative_humidity": 59.4,
                            "wind_from_direction": 220.6,
                            "wind_speed": 1.7,
                        }
                    },
                    "next_1_hours": {
                        "details": {"precipitation_amount": 0.0},
                        "summary": {"symbol_code": "fair_day"},
                    },
                    "next_12_hours": {
                        "details": {},
                        "summary": {"symbol_code": "lightrainshowers_day"},
                    },
                    "next_6_hours": {
                        "details": {"precipitation_amount": 1.0},
                        "summary": {"symbol_code": "rainshowers_day"},
                    },
                },
                "time": "2025-10-26T10:00:00Z",
            },
            {
                "data": {
                    "instant": {
                        "details": {
                            "air_pressure_at_sea_level": 1010.9,
                            "air_temperature": 30.9,
                            "cloud_area_fraction": 32.0,
                            "relative_humidity": 59.1,
                            "wind_from_direction": 241.8,
                            "wind_speed": 2.0,
                        }
                    },
                    "next_1_hours": {
                        "details": {"precipitation_amount": 0.0},
                        "summary": {"symbol_code": "fair_day"},
                    },
                    "next_12_hours": {
                        "details": {},
                        "summary": {"symbol_code": "lightrainshowers_day"},
                    },
                    "next_6_hours": {
                        "details": {"precipitation_amount": 0.9},
                        "summary": {"symbol_code": "lightrainshowers_day"},
                    },
                },
                "time": "2025-10-26T11:00:00Z",
            },
        ],
    },
    "type": "Feature",
}


class ResponseMock:
    def __init__(self, json_data: dict|None, raise_exception=None):
        self.json_data = json_data
        self.raise_exception = raise_exception

    def raise_for_status(self):
        if self.raise_exception:
            raise self.raise_exception

    def json(self):
        return self.json_data


class HttpClientMock:
    def __init__(self, get_data: dict, raise_exception=None):
        self.get_data = get_data
        self.raise_exception = raise_exception

    async def get(self, url: URL | str):
        return ResponseMock(self.get_data)


@pytest.mark.asyncio
async def test_get_forecast_positive():
    client = HttpClientMock(POSITIVE_RESPONSE)
    pos = Coordinates(lat=1, lon=20.46)
    result = await get_forecast(pos, client)
    assert result == [
        DayTempForecast(
            timestamp=datetime(2025, 10, 25, 12, 0, tzinfo=timezone.utc),
            temp=28.4,
        )
    ]


@pytest.mark.asyncio
async def test_get_forecast_incorrect_format():
    client = HttpClientMock(
        {"geometry": {"coordinates": [20.46, 1, 353], "type": "Point"}}
    )
    pos = Coordinates(lat=1, lon=20.46)
    result = await get_forecast(pos, client)
    assert result == []


@pytest.mark.asyncio
async def test_get_forecast_fail_to_get_response_from_api():
    client = HttpClientMock(
        {"geometry": {"coordinates": [20.46, 1, 353], "type": "Point"}},
        Exception("general error"),
    )
    pos = Coordinates(lat=1, lon=20.46)
    result = await get_forecast(pos, client)
    assert result == []
