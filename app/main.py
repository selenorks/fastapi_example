from contextlib import asynccontextmanager
from typing import Annotated

import httpx
import uvicorn
from fastapi import FastAPI, Query, Request
from pydantic import AfterValidator

from app.forecast import (
    ORJSONIndentedResponse,
    get_forecast_cached,
    BelgradeCoordinates,
    Coordinates,
)


def check_longitude(pos: float):
    if -180 <= pos <= 180:
        return pos
    raise ValueError("should be in range -180 to 180")


def check_latitude(pos: float):
    if -90 <= pos <= 90:
        return pos
    raise ValueError("should be in range -90 to 90")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the Client on startup and add it to the state
    async with httpx.AsyncClient() as client:
        yield {"http_client": client}
        # The Client closes on shutdown


app = FastAPI(lifespan=lifespan)


@app.get(
    "/get_forecast",
    responses={
        200: {
            "description": "Forecast for next days for requested coordinates",
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
async def app_get_forecast(
    request: Request,
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
):
    """
    Return a forecast for requested location for available days corresponds to 14 hour Serbian time.
    """

    coordinates = Coordinates(lat=lat, lon=lon)
    http_client = request.state.http_client
    return await get_forecast_cached(coordinates, http_client)


@app.get(
    "/get_forecast_belgrade",
    responses={
        200: {
            "description": "Forecast for next days for Belgrade",
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
async def app_get_forecast_belgrade(request: Request):
    """
    Return a forecast for Belgrade for available days corresponds to 14 hour Serbian time.
    """
    http_client = request.state.http_client
    coordinates = BelgradeCoordinates
    return await get_forecast_cached(coordinates, http_client)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
