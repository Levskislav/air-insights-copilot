"""
tests/test_retry.py
===================
Unit tests for agent/retry.py - HTTP retry with exponential backoff.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from agent.retry import (
    request_with_retry,
    get_json,
    post_json,
    RETRY_STATUS_CODES,
    RETRY_DELAYS,
)


class TestRetryStatusCodes:
    """Tests for retry status code configuration."""
    
    def test_retryable_status_codes(self):
        """Verify the correct status codes trigger retry."""
        expected = {429, 500, 502, 503, 504}
        assert RETRY_STATUS_CODES == expected
    
    def test_retry_delays_exponential(self):
        """Verify retry delays are configured."""
        assert len(RETRY_DELAYS) == 3
        assert RETRY_DELAYS[0] < RETRY_DELAYS[1] < RETRY_DELAYS[2]


class TestRequestWithRetry:
    """Tests for request_with_retry function."""
    
    @pytest.mark.asyncio
    @patch("agent.retry.get_client")
    async def test_successful_request(self, mock_get_client):
        """Successful request returns JSON data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = await request_with_retry("GET", "https://api.example.com/data")
        
        assert result == {"result": "success"}
        mock_client.request.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("agent.retry.get_client")
    @patch("agent.retry.asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_on_500(self, mock_sleep, mock_get_client):
        """Request retries on 500 status code."""
        # First call returns 500, second returns 200
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"result": "success"}
        mock_response_200.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.request.side_effect = [mock_response_500, mock_response_200]
        mock_get_client.return_value = mock_client
        
        result = await request_with_retry("GET", "https://api.example.com/data")
        
        assert result == {"result": "success"}
        assert mock_client.request.call_count == 2
        mock_sleep.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("agent.retry.get_client")
    @patch("agent.retry.asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_on_429_rate_limit(self, mock_sleep, mock_get_client):
        """Request retries on 429 rate limit."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": "ok"}
        mock_response_200.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.request.side_effect = [mock_response_429, mock_response_200]
        mock_get_client.return_value = mock_client
        
        result = await request_with_retry("GET", "https://api.example.com/data")
        
        assert result == {"data": "ok"}
        assert mock_client.request.call_count == 2
    
    @pytest.mark.asyncio
    @patch("agent.retry.get_client")
    async def test_no_retry_on_400(self, mock_get_client):
        """400 Bad Request does NOT trigger retry."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )
        
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        with pytest.raises(httpx.HTTPStatusError):
            await request_with_retry("GET", "https://api.example.com/data")
        
        # Should only be called once (no retry)
        assert mock_client.request.call_count == 1
    
    @pytest.mark.asyncio
    @patch("agent.retry.get_client")
    @patch("agent.retry.asyncio.sleep", new_callable=AsyncMock)
    async def test_max_retries_exceeded(self, mock_sleep, mock_get_client):
        """Raises error after all retries exhausted."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        
        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        with pytest.raises(RuntimeError, match="Retryable HTTP status"):
            await request_with_retry("GET", "https://api.example.com/data")
        
        # 1 initial + 3 retries = 4 total attempts
        assert mock_client.request.call_count == 4
        assert mock_sleep.call_count == 3
    
    @pytest.mark.asyncio
    @patch("agent.retry.get_client")
    @patch("agent.retry.asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_on_connection_error(self, mock_sleep, mock_get_client):
        """Request retries on connection errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.request.side_effect = [
            httpx.ConnectError("Connection refused"),
            mock_response
        ]
        mock_get_client.return_value = mock_client
        
        result = await request_with_retry("GET", "https://api.example.com/data")
        
        assert result == {"result": "success"}
        assert mock_client.request.call_count == 2


class TestConvenienceFunctions:
    """Tests for get_json and post_json convenience functions."""
    
    @pytest.mark.asyncio
    @patch("agent.retry.request_with_retry", new_callable=AsyncMock)
    async def test_get_json(self, mock_request):
        """get_json calls request_with_retry with GET method."""
        mock_request.return_value = {"data": "test"}
        
        result = await get_json("https://api.example.com/data", params={"key": "value"})
        
        assert result == {"data": "test"}
        mock_request.assert_called_once_with(
            "GET", "https://api.example.com/data",
            params={"key": "value"},
            timeout=pytest.approx(10.0, abs=1)
        )
    
    @pytest.mark.asyncio
    @patch("agent.retry.request_with_retry", new_callable=AsyncMock)
    async def test_post_json(self, mock_request):
        """post_json calls request_with_retry with POST method."""
        mock_request.return_value = {"result": "created"}
        
        result = await post_json(
            "https://api.example.com/data",
            json={"name": "test"},
            headers={"Authorization": "Bearer token"}
        )
        
        assert result == {"result": "created"}
        mock_request.assert_called_once()
