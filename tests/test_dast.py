"""
tests/test_dast.py
==================
Dynamic Application Security Testing (DAST)

Tests the running API for common security vulnerabilities:
- SQL/NoSQL injection
- Cross-Site Scripting (XSS)
- Input validation bypass
- Rate limiting
- Error information disclosure
- Authentication bypass attempts

Run: pytest tests/test_dast.py -v
"""

import pytest
from fastapi.testclient import TestClient
from service.main import app
from service.routes import limiter


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter storage before each test to prevent rate limit interference."""
    # Clear the limiter's internal storage
    if hasattr(limiter, '_storage') and hasattr(limiter._storage, 'storage'):
        limiter._storage.storage.clear()
    yield
    # Also clear after test
    if hasattr(limiter, '_storage') and hasattr(limiter._storage, 'storage'):
        limiter._storage.storage.clear()


class TestInputValidation:
    """Test input validation and injection prevention."""
    
    def test_sql_injection_in_place_name(self):
        """Test that SQL injection attempts are safely handled."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1; SELECT * FROM passwords",
            "' UNION SELECT * FROM users --",
        ]
        
        for payload in malicious_inputs:
            response = client.post("/analyze", json={
                "place_name": payload,
                "hours": 6
            })
            # Should return 400 (not found) or handle safely, not 500
            assert response.status_code != 500, f"SQL injection may have caused error: {payload}"
    
    def test_xss_in_place_name(self):
        """Test that XSS attempts are safely handled."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ]
        
        for payload in xss_payloads:
            response = client.post("/analyze", json={
                "place_name": payload,
                "hours": 6
            })
            # Should handle safely
            assert response.status_code != 500, f"XSS payload caused error: {payload}"
            
            # If successful, response should not contain raw script
            if response.status_code == 200:
                assert "<script>" not in response.text.lower()
    
    def test_command_injection_attempts(self):
        """Test that command injection attempts are safely handled."""
        cmd_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "$(whoami)",
            "`id`",
            "&& rm -rf /",
        ]
        
        for payload in cmd_payloads:
            response = client.post("/analyze", json={
                "place_name": f"Sofia{payload}",
                "hours": 6
            })
            assert response.status_code != 500, f"Command injection may have caused error: {payload}"


class TestBoundaryValidation:
    """Test boundary conditions and validation."""
    
    def test_latitude_bounds(self):
        """Test latitude validation."""
        # Valid boundaries
        assert client.post("/analyze", json={"latitude": 90, "longitude": 0, "hours": 1}).status_code in [200, 400]
        assert client.post("/analyze", json={"latitude": -90, "longitude": 0, "hours": 1}).status_code in [200, 400]
        
        # Invalid - should be rejected
        response = client.post("/analyze", json={"latitude": 91, "longitude": 0, "hours": 1})
        assert response.status_code == 422  # Validation error
        
        response = client.post("/analyze", json={"latitude": -91, "longitude": 0, "hours": 1})
        assert response.status_code == 422
    
    def test_longitude_bounds(self):
        """Test longitude validation."""
        # Invalid - should be rejected
        response = client.post("/analyze", json={"latitude": 0, "longitude": 181, "hours": 1})
        assert response.status_code == 422
        
        response = client.post("/analyze", json={"latitude": 0, "longitude": -181, "hours": 1})
        assert response.status_code == 422
    
    def test_hours_bounds(self):
        """Test hours parameter validation."""
        # Invalid - should be rejected
        response = client.post("/analyze", json={"latitude": 0, "longitude": 0, "hours": 0})
        assert response.status_code == 422
        
        response = client.post("/analyze", json={"latitude": 0, "longitude": 0, "hours": -1})
        assert response.status_code == 422
        
        # Very large hours - API returns 200 with error message (graceful handling)
        response = client.post("/analyze", json={"latitude": 0, "longitude": 0, "hours": 1000})
        assert response.status_code in [200, 422]  # Either validation error or graceful message
    
    def test_extremely_long_input(self):
        """Test handling of extremely long input strings."""
        long_string = "A" * 10000
        
        response = client.post("/analyze", json={
            "place_name": long_string,
            "hours": 6
        })
        # Should reject or handle gracefully, not crash
        assert response.status_code in [400, 422], "Should reject extremely long input"


class TestErrorHandling:
    """Test error handling doesn't leak sensitive information."""
    
    def test_error_no_stack_trace(self):
        """Ensure errors don't expose stack traces."""
        response = client.post("/analyze", json={
            "latitude": "invalid",
            "longitude": "invalid",
            "hours": "invalid"
        })
        
        # Should return validation error
        assert response.status_code == 422
        
        # Should not contain stack trace indicators
        response_text = response.text.lower()
        assert "traceback" not in response_text
        assert "file \"" not in response_text
        assert "line " not in response_text or "location" in response_text
    
    def test_error_no_internal_paths(self):
        """Ensure errors don't expose internal file paths."""
        response = client.post("/analyze", json={
            "latitude": "invalid"
        })
        
        response_text = response.text
        # Should not contain system paths
        assert "/home/" not in response_text
        assert "C:\\" not in response_text
        assert "/usr/" not in response_text


class TestAuthenticationBypass:
    """Test authentication and authorization."""
    
    def test_no_auth_header_manipulation(self):
        """Test that auth header manipulation doesn't grant access."""
        suspicious_headers = [
            {"Authorization": "Bearer admin"},
            {"X-Forwarded-For": "127.0.0.1"},
            {"X-Real-IP": "localhost"},
            {"X-Admin": "true"},
        ]
        
        for headers in suspicious_headers:
            response = client.get("/health", headers=headers)
            # Should work normally (public endpoint)
            assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting is in place."""
    
    def test_rate_limit_exists(self):
        """Verify rate limiting is configured."""
        # Make multiple rapid requests
        responses = []
        for _ in range(35):  # Limit is 30/minute
            response = client.post("/analyze", json={
                "place_name": "Sofia",
                "hours": 1
            })
            responses.append(response.status_code)
        
        # Should eventually get rate limited (429)
        assert 429 in responses, "Rate limiting should trigger after 30 requests"
