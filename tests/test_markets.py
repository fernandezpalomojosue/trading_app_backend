from unittest.mock import AsyncMock, patch
import pytest


# =========================
# BASIC / PUBLIC ENDPOINTS
# =========================

def test_list_markets(client):
    """
    GET /api/v1/markets
    No usa servicios externos.
    """
    res = client.get("/api/v1/markets")

    assert res.status_code == 200
    data = res.json()

    assert isinstance(data, list)
    assert any(m["id"] == "stocks" for m in data)


def test_market_overview_invalid_market(client):
    """
    Solo 'stocks' está soportado.
    """
    res = client.get("/api/v1/markets/crypto/overview")

    assert res.status_code == 400
    assert "stocks" in res.json()["detail"].lower()


def test_list_assets_invalid_market(client):
    res = client.get("/api/v1/markets/forex/assets")

    assert res.status_code == 400
    assert "stocks" in res.json()["detail"].lower()


# =========================
# MOCKED SERVICE TESTS
# =========================

@patch("app.api.v1.endpoints.markets.MassiveClient")
def test_market_overview_success(mock_client, client):
    """
    GET /markets/stocks/overview
    Con MassiveClient mockeado
    """
    mock_instance = AsyncMock()
    mock_client.return_value.__aenter__.return_value = mock_instance

    mock_instance.get_daily_market_summary.return_value = {
        "results": [
            {
                "symbol": "AAPL",
                "close": 150.0,
                "change": 2.0,
                "change_percent": 1.35,
                "volume": 1000000,
            }
        ]
    }

    res = client.get("/api/v1/markets/stocks/overview")

    assert res.status_code == 200
    body = res.json()

    assert body["market"] == "stocks"
    assert body["total_assets"] == 1
    assert body["status"] == "closed"
    assert len(body["top_gainers"]) == 1


@patch("app.api.v1.endpoints.markets.MassiveClient")
def test_list_assets_success(mock_client, client):
    """
    GET /markets/stocks/assets
    """
    mock_instance = AsyncMock()
    mock_client.return_value.__aenter__.return_value = mock_instance

    mock_instance.get_daily_market_summary.return_value = {
        "results": [
            {
                "symbol": "MSFT",
                "close": 300.0,
                "change": -1.2,
                "change_percent": -0.4,
                "volume": 2000000,
            }
        ]
    }

    res = client.get("/api/v1/markets/stocks/assets?limit=10")

    assert res.status_code == 200
    data = res.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["symbol"] == "MSFT"
    assert data[0]["market"] == "stocks"


@patch("app.api.v1.endpoints.markets.MassiveClient")
def test_get_asset_success(mock_client, client):
    """
    GET /markets/assets/{symbol}
    """
    mock_instance = AsyncMock()
    mock_client.return_value.__aenter__.return_value = mock_instance

    mock_instance.get_ticker_details.return_value = {
        "id": "AAPL",
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "market": "stocks",
        "currency": "USD",
        "active": True,
    }

    res = client.get("/api/v1/markets/assets/AAPL")

    assert res.status_code == 200
    body = res.json()

    assert body["symbol"] == "AAPL"
    assert body["active"] is True


@patch("app.api.v1.endpoints.markets.MassiveClient")
def test_get_candles_success(mock_client, client):
    """
    GET /markets/{symbol}/candles
    """
    mock_instance = AsyncMock()
    mock_client.return_value.__aenter__.return_value = mock_instance

    mock_instance.get_ohlc_data.return_value = {
        "results": [
            {"o": 150, "h": 155, "l": 149, "c": 154, "v": 100000}
        ]
    }

    res = client.get("/api/v1/markets/AAPL/candles")

    assert res.status_code == 200
    data = res.json()

    assert "results" in data
    assert isinstance(data["results"], list)
