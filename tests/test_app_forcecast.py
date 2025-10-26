from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.test_forecast import ResponseMock, POSITIVE_RESPONSE
from app.forecast import get_forecast_cached

GET_RESPONSE = [{"timestamp": "2025-10-25T12:00:00Z", "temp": 28.4}]


@pytest.fixture(scope="function")
def get_forecast_cached_clear():
    yield 1
    get_forecast_cached.cache_clear()


@pytest.mark.parametrize("data, exception_obj, expected",
                         (
                                 (POSITIVE_RESPONSE, None, GET_RESPONSE),
                                 (None, Exception("no data"), []),
                         )
                         )
def test_get_forecast_belgrade(data, exception_obj, expected, get_forecast_cached_clear):
    with patch('app.forecast.AsyncClient.get', new_callable=AsyncMock) as http_get:
        http_get.return_value = ResponseMock(data, exception_obj)
        with TestClient(app) as client:
            response = client.get("/get_forecast_belgrade")
            assert response.status_code == 200
            assert response.json() == expected


def test_get_forecast(get_forecast_cached_clear):
    with patch('app.forecast.AsyncClient.get', new_callable=AsyncMock) as http_get:
        http_get.return_value = ResponseMock(POSITIVE_RESPONSE)
        with TestClient(app) as client:
            response = client.get("/get_forecast", params={"lat": 50, "lon": 20})
            assert response.status_code == 200
            assert response.json() == GET_RESPONSE
