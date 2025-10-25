import logging
from datetime import datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from cachetools import TTLCache
from cachetools_async import cached
from fastapi import Response
import orjson
from httpx import AsyncClient
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DayTempForecast(BaseModel):
    timestamp: datetime
    temp: float


class Coordinates(BaseModel):
    lat: float
    lon: float

    def __hash__(self):
        return hash((self.lat, self.lon))


BelgradeCoordinates = Coordinates(lat=44.81, lon=20.46)


def custom_json_encoder(obj):
    """
    Helper to convert class DayTempForecast to json
    :param obj:
    :return:
    """
    if isinstance(obj, DayTempForecast):
        return {"day": str(obj.timestamp.date()), "temp": f"{obj.temp:.1f}"}
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def filter_day_temp_forecast(forecast: DayTempForecast) -> bool:
    """
    Check that the forecast time stamp corresponds to 14 hour Serbian time.
    """
    tz_serbia = ZoneInfo("Europe/Belgrade")
    target_slice_time = forecast.timestamp.astimezone(tz_serbia)
    return target_slice_time.time().hour == 14


def format_timeseries_to_day_temp_forecast(data: dict) -> Iterable[DayTempForecast]:
    """
    Convert REST API response from api.met.no to Iterable of DayTempForecast
    :param data:
    :return:
    """
    tz_serbia = ZoneInfo("Europe/Belgrade")
    for forecast_slice in data["properties"]["timeseries"]:
        format_string = "%Y-%m-%dT%H:%M:%S%z"
        slice_time = datetime.strptime(forecast_slice["time"], format_string)
        yield DayTempForecast(
            timestamp=slice_time,
            temp=forecast_slice["data"]["instant"]["details"]["air_temperature"],
        )


async def request_external_forecast(
    coordinates: Coordinates, http_client: AsyncClient
) -> dict:
    response = await http_client.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={:.2f}&lon={:.2f}".format(
            coordinates.lat, coordinates.lon
        ),
    )
    response.raise_for_status()
    return response.json()


# Cache for 60 seconds to avoid abusing external service
@cached(
    cache=TTLCache(maxsize=1024, ttl=60),
    key=lambda coordinates, http_client: coordinates,
)
async def get_forecasts(
    coordinates: Coordinates, http_client: AsyncClient
) -> list[DayTempForecast]:
    """
    Get forecast from api.met.no corresponds to 14 hour Serbian time.
    """
    try:
        data = await request_external_forecast(coordinates, http_client)
    except Exception as exc:
        logger.error("Failed to get forecast from external server, error: %s", exc)
        return []

    forecast_per_days = list(
        filter(filter_day_temp_forecast, format_timeseries_to_day_temp_forecast(data))
    )
    return forecast_per_days


class ORJSONIndentedResponse(Response):
    media_type = "application/json"

    def render(self, content: any) -> bytes:
        return orjson.dumps(
            content, option=orjson.OPT_INDENT_2, default=custom_json_encoder
        )
