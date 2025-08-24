import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from app.main import _parse_intraday_response, _parse_fx_response, _parse_crypto_response, app


def test_parse_intraday_response():
    """Test parsing intraday price data from Twelve Data API."""
    raw_data = {
        "values": [
            {
                "datetime": "2024-01-15 09:30:00",
                "open": "100.00",
                "high": "101.50",
                "low": "99.80",
                "close": "101.20",
                "volume": "1000000"
            },
            {
                "datetime": "2024-01-15 09:31:00",
                "open": "101.20",
                "high": "101.80",
                "low": "101.00",
                "close": "101.60",
                "volume": "800000"
            }
        ]
    }
    
    prices = _parse_intraday_response(raw_data)
    
    assert len(prices) == 2
    assert prices[0].datetime == "2024-01-15 09:30:00"
    assert prices[0].open == 100.00
    assert prices[0].close == 101.20
    assert prices[0].volume == 1000000


def test_parse_fx_response():
    """Test parsing FX rate data from Twelve Data API."""
    raw_data = {
        "values": [
            {
                "datetime": "2024-01-15 10:00:00",
                "open": "1.0850",
                "high": "1.0870",
                "low": "1.0840",
                "close": "1.0860"
            }
        ]
    }
    
    rates = _parse_fx_response(raw_data)
    
    assert len(rates) == 1
    assert rates[0].datetime == "2024-01-15 10:00:00"
    assert rates[0].open == 1.0850
    assert rates[0].close == 1.0860


def test_parse_crypto_response():
    """Test parsing crypto price data from Twelve Data API."""
    raw_data = {
        "values": [
            {
                "datetime": "2024-01-15 11:00:00",
                "open": "42000.00",
                "high": "42500.00",
                "low": "41800.00",
                "close": "42200.00",
                "volume": "1500.5"
            }
        ]
    }
    
    prices = _parse_crypto_response(raw_data)
    
    assert len(prices) == 1
    assert prices[0].datetime == "2024-01-15 11:00:00"
    assert prices[0].open == 42000.00
    assert prices[0].close == 42200.00
    assert prices[0].volume == 1500.5


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    with app.test_client() as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "ingestor_twelve"


@pytest.mark.asyncio
async def test_intraday_endpoint_missing_symbol():
    """Test intraday endpoint validation."""
    with app.test_client() as client:
        response = client.get("/v1/ingest/twelve/intraday")
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_fx_endpoint_missing_symbol():
    """Test FX endpoint validation."""
    with app.test_client() as client:
        response = client.get("/v1/ingest/twelve/fx")
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_crypto_endpoint_missing_symbol():
    """Test crypto endpoint validation."""
    with app.test_client() as client:
        response = client.get("/v1/ingest/twelve/crypto")
        assert response.status_code == 422  # Validation error


def test_malformed_data_handling():
    """Test handling of malformed API responses."""
    raw_data = {
        "values": [
            {
                "datetime": "2024-01-15 09:30:00",
                "open": "invalid",  # Invalid number
                "high": "101.50",
                "low": "99.80",
                "close": "101.20",
                "volume": "1000000"
            },
            {
                "datetime": "2024-01-15 09:31:00",
                "open": "101.20",
                "high": "101.80",
                "low": "101.00",
                "close": "101.60",
                "volume": "800000"
            }
        ]
    }
    
    # Should skip malformed data and continue processing
    prices = _parse_intraday_response(raw_data)
    
    assert len(prices) == 1  # Only the valid record
    assert prices[0].datetime == "2024-01-15 09:31:00"
