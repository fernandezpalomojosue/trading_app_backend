# tests/unit/application/services/test_evaluation_target_service_simple.py
"""
Simple unit tests for EvaluationTargetService without full app imports.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.application.services.evaluation_target_service import EvaluationTargetService
from app.domain.entities.evaluation_target import EvaluationTarget


class TestEvaluationTargetServiceSimple:
    """Test EvaluationTargetService behavior with minimal dependencies."""
    
    @pytest.mark.asyncio
    async def test_get_targets_with_favorites(self):
        """Should return single target with favorite stocks."""
        # Arrange
        mock_favorites = Mock()
        mock_favorites.symbols = ["AAPL", "MSFT", "GOOGL"]
        
        mock_favorite_repo = AsyncMock()
        mock_favorite_repo.get_all_favorites.return_value = mock_favorites
        
        mock_settings = Mock()
        
        service = EvaluationTargetService(
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 1
        target = targets[0]
        assert isinstance(target, EvaluationTarget)
        assert target.stocks == ["AAPL", "MSFT", "GOOGL"]
        assert target.stock_count == 3
        
        # Verify dependencies were called
        mock_favorite_repo.get_all_favorites.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_targets_no_favorites_with_defaults(self):
        """Should return single target with default stocks when no favorites."""
        # Arrange
        mock_favorites = Mock()
        mock_favorites.symbols = []  # Empty favorites
        
        mock_favorite_repo = AsyncMock()
        mock_favorite_repo.get_all_favorites.return_value = mock_favorites
        
        mock_settings = Mock()
        mock_settings.DEFAULT_SIGNAL_STOCKS = "AAPL,TSLA,NVDA"
        
        service = EvaluationTargetService(
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 1
        target = targets[0]
        assert target.stocks == ["AAPL", "TSLA", "NVDA"]
        assert target.stock_count == 3
    
    @pytest.mark.asyncio
    async def test_get_targets_no_favorites_no_defaults(self):
        """Should return empty list when no favorites and no defaults."""
        # Arrange
        mock_favorites = Mock()
        mock_favorites.symbols = None  # No favorites
        
        mock_favorite_repo = AsyncMock()
        mock_favorite_repo.get_all_favorites.return_value = mock_favorites
        
        mock_settings = Mock()
        mock_settings.DEFAULT_SIGNAL_STOCKS = None
        
        service = EvaluationTargetService(
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 0
    
    @pytest.mark.asyncio
    async def test_get_targets_normalizes_symbols(self):
        """Should normalize stock symbols to uppercase."""
        # Arrange
        mock_favorites = Mock()
        mock_favorites.symbols = ["aapl", "msft", "googl"]  # lowercase
        
        mock_favorite_repo = AsyncMock()
        mock_favorite_repo.get_all_favorites.return_value = mock_favorites
        
        mock_settings = Mock()
        
        service = EvaluationTargetService(
            favorite_repository=mock_favorite_repo,
            settings=mock_settings
        )
        
        # Act
        targets = await service.get_targets()
        
        # Assert
        assert len(targets) == 1
        target = targets[0]
        assert target.stocks == ["AAPL", "MSFT", "GOOGL"]  # Uppercase
