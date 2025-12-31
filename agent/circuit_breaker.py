"""
agent/circuit_breaker.py
========================
Circuit breaker pattern for external API calls.

The circuit breaker prevents cascade failures by "opening" the circuit
when too many failures occur, causing subsequent calls to fail fast
instead of waiting for timeouts.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failures exceeded threshold, requests fail immediately
- HALF_OPEN: After reset timeout, allow one request to test recovery

Usage:
    breaker = CircuitBreaker("open-meteo")
    
    if not breaker.can_execute():
        raise ServiceUnavailableError()
    
    try:
        result = await call_api()
        breaker.record_success()
    except Exception:
        breaker.record_failure()
        raise
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict

from agent.logging_config import log_warning, log_info


# =============================================================================
# CIRCUIT STATES
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


# =============================================================================
# CIRCUIT BREAKER
# =============================================================================

@dataclass
class CircuitBreaker:
    """
    Circuit breaker for a single service.
    
    Attributes:
        name: Service name (for logging)
        failure_threshold: Number of failures before opening circuit
        reset_timeout: Time to wait before attempting recovery
        failures: Current failure count
        last_failure: Timestamp of last failure
        state: Current circuit state
    """
    name: str
    failure_threshold: int = 5
    reset_timeout: timedelta = field(default_factory=lambda: timedelta(seconds=60))
    
    # State tracking
    failures: int = field(default=0, init=False)
    successes_in_half_open: int = field(default=0, init=False)
    last_failure: datetime | None = field(default=None, init=False)
    state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    
    # Thread safety
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    
    def can_execute(self) -> bool:
        """
        Check if a request can proceed.
        
        Returns:
            True if request should proceed, False if circuit is open
        """
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                # Check if reset timeout has passed
                if self.last_failure and datetime.now() - self.last_failure > self.reset_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.successes_in_half_open = 0
                    log_info(f"Circuit {self.name} entering HALF_OPEN state")
                    return True
                return False
            
            # HALF_OPEN: allow limited requests to test recovery
            return True
    
    def record_success(self) -> None:
        """Record a successful request."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.successes_in_half_open += 1
                # After 2 successes in half-open, close the circuit
                if self.successes_in_half_open >= 2:
                    self.state = CircuitState.CLOSED
                    self.failures = 0
                    log_info(f"Circuit {self.name} CLOSED after recovery")
            else:
                # In closed state, just reset failure count
                self.failures = 0
    
    def record_failure(self) -> None:
        """Record a failed request."""
        with self._lock:
            self.failures += 1
            self.last_failure = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open reopens the circuit
                self.state = CircuitState.OPEN
                log_warning(f"Circuit {self.name} OPEN again after half-open failure")
            elif self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
                log_warning(f"Circuit {self.name} OPEN after {self.failures} failures")
    
    def get_state(self) -> dict:
        """Get current circuit state as dict."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failures": self.failures,
                "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            }
    
    def reset(self) -> None:
        """Reset circuit to closed state (for testing)."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failures = 0
            self.last_failure = None
            self.successes_in_half_open = 0


# =============================================================================
# CIRCUIT BREAKER REGISTRY
# =============================================================================

class CircuitBreakerRegistry:
    """
    Registry of circuit breakers for different services.
    
    Provides a single place to get/create circuit breakers by service name.
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def get(self, name: str) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a service.
        
        Args:
            name: Service name (e.g., "open-meteo", "github-models")
            
        Returns:
            CircuitBreaker instance for this service
        """
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name=name)
            return self._breakers[name]
    
    def get_all_states(self) -> list[dict]:
        """Get state of all circuit breakers."""
        with self._lock:
            return [breaker.get_state() for breaker in self._breakers.values()]
    
    def reset_all(self) -> None:
        """Reset all circuit breakers (for testing)."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()


# Global registry
circuit_breakers = CircuitBreakerRegistry()
