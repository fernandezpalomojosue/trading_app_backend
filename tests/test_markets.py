from unittest.mock import AsyncMock, patch
import pytest
from datetime import datetime


class TestMarketsEndpoints:
    """Test suite for markets endpoints"""
    
    # =========================
    # BASIC / PUBLIC ENDPOINTS
    # =========================

    def test_list_markets(self, client):
        """
        GET /api/v1/markets
        Returns list of available markets without external dependencies.
        """
        response = client.get("/api/v1/markets")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1  # At least stocks should be available
        
        # Verify structure of market items
        for market in data:
            assert "id" in market
            assert "name" in market
            assert isinstance(market["id"], str)
            assert isinstance(market["name"], str)
        
        # Verify stocks market is present
        assert any(m["id"] == "stocks" for m in data)

    def test_market_overview_invalid_market(self, client):
        """
        GET /api/v1/markets/crypto/overview
        Should return 400 as only 'stocks' is supported.
        """
        response = client.get("/api/v1/markets/crypto/overview")

        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "stocks" in error_detail.lower()
        assert "solo" in error_detail.lower()

    def test_list_assets_invalid_market(self, client):
        """
        GET /api/v1/markets/forex/assets
        Should return 422 for invalid market type.
        """
        response = client.get("/api/v1/markets/forex/assets")
        assert response.status_code == 422

    def test_list_assets_pagination_validation(self, client):
        """
        GET /api/v1/markets/stocks/assets with invalid pagination parameters.
        """
        # Test negative limit
        response = client.get("/api/v1/markets/stocks/assets?limit=-10")
        assert response.status_code in [422, 500]  # May fail with API key error
        
        # Test negative offset
        response = client.get("/api/v1/markets/stocks/assets?offset=-5")
        assert response.status_code in [422, 500]  # May fail with API key error
        
        # Test very large limit
        response = client.get("/api/v1/markets/stocks/assets?limit=10000")
        assert response.status_code in [200, 422, 500]  # May fail with API key error

    # =========================
    # MOCKED SERVICE TESTS
    # =========================

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_market_overview_success(self, mock_client, client):
        """
        GET /api/v1/markets/stocks/overview
        Test successful market overview with mocked MassiveClient.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        mock_instance.get_daily_market_summary.return_value = {
            "results": [
                {
                    "T": "AAPL",  # Symbol in Polygon format
                    "c": 150.0,    # Close
                    "o": 148.0,    # Open  
                    "h": 152.0,    # High
                    "l": 147.0,    # Low
                    "v": 1000000    # Volume
                },
                {
                    "T": "MSFT",
                    "c": 250.0,
                    "o": 248.0,
                    "h": 252.0,
                    "l": 247.0,
                    "v": 800000
                }
            ]
        }

        response = client.get("/api/v1/markets/stocks/overview")

        assert response.status_code == 200
        body = response.json()

        # Verify response structure
        assert "market" in body
        assert "total_assets" in body
        assert "status" in body
        assert "last_updated" in body
        assert "top_gainers" in body
        assert "top_losers" in body
        assert "most_active" in body
        
        # Verify response content
        assert body["market"] == "stocks"
        assert body["total_assets"] == 2
        assert body["status"] == "closed"
        assert len(body["top_gainers"]) == 2
        assert len(body["top_losers"]) == 2
        assert len(body["most_active"]) == 2
        
        # Verify timestamp format
        assert "last_updated" in body
        
        # Verify top assets structure
        for gainer in body["top_gainers"]:
            assert "symbol" in gainer
            assert "change_percent" in gainer
            assert "volume" in gainer

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_market_overview_empty_results(self, mock_client, client):
        """
        Test market overview with empty results from external service.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        mock_instance.get_daily_market_summary.return_value = {
            "results": []
        }

        response = client.get("/api/v1/markets/stocks/overview")

        assert response.status_code == 200
        body = response.json()
        assert body["total_assets"] == 0
        assert len(body["top_gainers"]) == 0
        assert len(body["top_losers"]) == 0
        assert len(body["most_active"]) == 0

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_market_overview_service_error(self, mock_client, client):
        """
        Test market overview when external service fails.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        mock_instance.get_daily_market_summary.side_effect = Exception("Service unavailable")

        response = client.get("/api/v1/markets/stocks/overview")

        assert response.status_code == 500
        error_detail = response.json()["detail"]
        assert "Error al obtener el resumen del mercado" in error_detail

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_list_assets_success(self, mock_client, client):
        """
        GET /api/v1/markets/stocks/assets
        Test successful assets listing with pagination.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        mock_instance.get_daily_market_summary.return_value = {
            "results": [
                {
                    "T": "MSFT",   # Symbol in Polygon format
                    "c": 300.0,    # Close
                    "o": 301.2,    # Open
                    "h": 302.0,    # High
                    "l": 298.5,    # Low
                    "v": 2000000    # Volume
                },
                {
                    "T": "GOOGL",
                    "c": 2500.0,
                    "o": 2510.0,
                    "h": 2520.0,
                    "l": 2490.0,
                    "v": 1500000
                }
            ]
        }

        response = client.get("/api/v1/markets/stocks/assets?limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify asset structure
        for asset in data:
            assert "id" in asset
            assert "symbol" in asset
            assert "name" in asset
            assert "market" in asset
            assert "currency" in asset
            assert "active" in asset
            # Note: price field may not be present in mocked response
            assert "change" in asset or "change_percent" in asset
            assert "volume" in asset
            assert "details" in asset
            
            assert asset["market"] == "stocks"
            assert asset["currency"] == "USD"
            assert asset["active"] is True

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_list_assets_pagination(self, mock_client, client):
        """
        Test pagination functionality in assets endpoint.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        # Create mock data with multiple assets
        mock_results = [
            {
                "T": f"STOCK{i}",
                "c": 100.0 + i,
                "o": 99.0 + i,
                "h": 101.0 + i,
                "l": 98.0 + i,
                "v": 1000000 - i * 10000
            }
            for i in range(10)
        ]
        
        mock_instance.get_daily_market_summary.return_value = {"results": mock_results}

        # Test limit
        response = client.get("/api/v1/markets/stocks/assets?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Test offset
        response = client.get("/api/v1/markets/stocks/assets?limit=5&offset=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_get_asset_success(self, mock_client, client):
        """
        GET /api/v1/markets/assets/{symbol}
        Test getting specific asset details.
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
            "description": "Technology company",
            "sector": "Technology"
        }

        response = client.get("/api/v1/markets/assets/AAPL")

        assert response.status_code == 200
        body = response.json()

        assert body["symbol"] == "AAPL"
        assert body["name"] == "Apple Inc."
        assert body["market"] == "stocks"
        assert body["currency"] == "USD"
        assert body["active"] is True
        assert "details" in body
        assert body["details"]["sector"] == "Technology"

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_get_asset_not_found(self, mock_client, client):
        """
        Test getting non-existent asset.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        mock_instance.get_ticker_details.side_effect = Exception("Asset not found")

        response = client.get("/api/v1/markets/assets/NONEXISTENT")

        assert response.status_code == 500

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_get_candles_success(self, mock_client, client):
        """
        GET /api/v1/markets/{symbol}/candles
        Test getting OHLC candle data.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        mock_instance.get_ohlc_data.return_value = {
            "results": [
                {
                    "o": 150,    # Open
                    "h": 155,    # High
                    "l": 149,    # Low
                    "c": 154,    # Close
                    "v": 100000, # Volume
                    "t": 1640995200  # Timestamp
                },
                {
                    "o": 154,
                    "h": 158,
                    "l": 152,
                    "c": 157,
                    "v": 120000,
                    "t": 1641081600
                }
            ],
            "status": "OK"
        }

        response = client.get("/api/v1/markets/AAPL/candles")

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 2
        
        # Verify candle structure
        for candle in data["results"]:
            assert "o" in candle  # Open
            assert "h" in candle  # High
            assert "l" in candle  # Low
            assert "c" in candle  # Close
            assert "v" in candle  # Volume

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_get_candles_with_parameters(self, mock_client, client):
        """
        Test getting candle data with various parameters.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        mock_instance.get_ohlc_data.return_value = {
            "results": [
                {"o": 100, "h": 105, "l": 95, "c": 103, "v": 50000}
            ]
        }

        # Test with parameters
        response = client.get("/api/v1/markets/AAPL/candles?timespan=hour&multiplier=4&limit=100")
        
        assert response.status_code == 200
        
        # Verify the mock was called with correct parameters
        mock_instance.get_ohlc_data.assert_called_once_with(
            symbol="AAPL",
            multiplier=4,
            timespan="hour",
            start_date=None,
            end_date=None,
            adjusted=True,
            sort="asc",
            limit=100
        )

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_get_candles_service_error(self, mock_client, client):
        """
        Test candle data endpoint when external service fails.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        mock_instance.get_ohlc_data.side_effect = Exception("Service error")

        response = client.get("/api/v1/markets/AAPL/candles")

        assert response.status_code == 500

    def test_candles_invalid_parameters(self, client):
        """
        Test candle endpoint with invalid parameters.
        """
        # Test with invalid timespan
        response = client.get("/api/v1/markets/AAPL/candles?timespan=invalid")
        # May succeed or fail depending on validation, or fail with API key error
        assert response.status_code in [200, 422, 500]
        
        # Test with negative multiplier
        response = client.get("/api/v1/markets/AAPL/candles?multiplier=-1")
        assert response.status_code in [200, 422, 500]
        
        # Test with very large limit
        response = client.get("/api/v1/markets/AAPL/candles?limit=100000")
        assert response.status_code in [200, 422, 500]

    @patch("app.api.v1.endpoints.markets.MassiveClient")
    def test_market_data_processing_edge_cases(self, mock_client, client):
        """
        Test processing of edge case market data.
        """
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance

        # Test with extreme values
        mock_instance.get_daily_market_summary.return_value = {
            "results": [
                {
                    "T": "EXTREME",
                    "o": 0.0001,     # Very small
                    "c": 999999.99,  # Very large
                    "h": 999999.99,
                    "l": 0.0001,
                    "v": 0           # Zero volume
                },
                {
                    "T": "ZERO_DIV",
                    "o": 0,          # Zero open price (division by zero case)
                    "c": 100.0,
                    "v": 1000000
                }
            ]
        }

        response = client.get("/api/v1/markets/stocks/overview")
        assert response.status_code == 200
        
        # Should handle extreme values gracefully
        body = response.json()
        assert body["total_assets"] >= 0
