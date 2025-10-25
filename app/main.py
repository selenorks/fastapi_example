from typing import Annotated

from fastapi import FastAPI, Query
from pydantic import AfterValidator

from app.forecast import (
    ORJSONIndentedResponse,
    get_forecasts,
    BelgradeCoordinates,
    Coordinates,
)

app = FastAPI()


def check_longitude(pos: float):
    if -180 <= pos <= 180:
        return pos
    raise ValueError("should be in range -90 to 90")


def check_latitude(pos: float):
    if -90 <= pos <= 90:
        return pos
    raise ValueError("should be in range -90 to 90")


@app.get("/get_forecast", response_class=ORJSONIndentedResponse)
async def get_forecast(
    lat: Annotated[
        float,
        AfterValidator(check_latitude),
        Query(description="Latitude of the location"),
    ],
    lon: Annotated[
        float,
        AfterValidator(check_longitude),
        Query(description="Longitude of the location"),
    ],
    # ,
    # Annotated[Union[str, None], AfterValidator(check_valid_id)]
    # lon: float = Query(float, description="Longitude of the location"),
):
    """
    Return a forecast for requested location for available days corresponds to 14 hour Serbian time.
    """

    coordinates = Coordinates(lat=lat, lon=lon)
    return await get_forecasts(coordinates)


@app.get(
    "/get_forecast_belgrade",
    responses={
        200: {
            "description": "Item successfully created",
            "content": {
                "application/json": {
                    "example": [
                        {"timestamp": "2025-11-12T12:00:00Z", "temp": 5.2},
                        {"timestamp": "2025-11-13T13:00:00Z", "temp": 6.7},
                    ]
                }
            },
        },
    },
    response_class=ORJSONIndentedResponse,
)
async def get_forecast_belgrade():
    """
    Return a forecast for Belgrade for available days corresponds to 14 hour Serbian time.
    :return:
    """
    coordinates = BelgradeCoordinates
    return await get_forecasts(coordinates)
