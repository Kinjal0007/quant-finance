import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from app.main import _to_unix, _candles_to_rows, app


def test_to_unix():
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    unix_ts = _to_unix(dt)
    assert unix_ts == 1704110400


def test_candles_to_rows():
    symbol = "AAPL"
    data = {
        "t": [1704110400, 1704196800],  # Jan 1, Jan 2
        "o": [100.0, 101.0],
        "h": [102.0, 103.0],
        "l": [99.0, 100.0],
        "c": [101.0, 102.0],
        "v": [1000000, 1100000],
    }
    
    rows = _candles_to_rows(symbol, data)
    
    assert len(rows) == 2
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["open"] == 100.0
    assert rows[0]["close"] == 101.0
    assert rows[0]["volume"] == 1000000.0
    assert rows[0]["source"] == "finnhub"
    assert "ingest_time" in rows[0]


@pytest.mark.asyncio
async def test_health_endpoint():
    with app.test_client() as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "ingestor_finnhub"


@pytest.mark.asyncio
async def test_ingest_endpoint_missing_symbol():
    with app.test_client() as client:
        response = client.get("/v1/ingest/finnhub/candles")
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_ingest_endpoint_invalid_days():
    with app.test_client() as client:
        response = client.get("/v1/ingest/finnhub/candles?symbol=AAPL&days=0")
        assert response.status_code == 422  # Validation error
        
        response = client.get("/v1/ingest/finnhub/candles?symbol=AAPL&days=400")
        assert response.status_code == 422  # Validation error
