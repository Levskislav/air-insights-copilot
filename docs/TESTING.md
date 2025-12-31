# Testing Documentation

## Overview

OutdoorMate has **89 tests** covering validation, computation, caching, retry logic, integration, and security.

```bash
pytest tests/ -v
```

---

## Test Summary

| Category | Tests | Description |
|----------|-------|-------------|
| **Validation** | 18 | Input validation and data quality |
| **Computation** | 10 | Statistical functions |
| **Cache** | 12 | Thread-safe caching |
| **Retry** | 10 | HTTP retry with circuit breaker |
| **Integration** | 7 | API endpoint tests |
| **Security (DAST)** | 12 | Dynamic security testing |
| **Security (SAST)** | 4 | Static code analysis |

---

## Detailed Test Descriptions

### test_validate.py (18 tests)

| Test | Description |
|------|-------------|
| `test_valid_coordinates` | Validates correct lat/lon coordinates (Sofia, Sydney) |
| `test_boundary_values` | Validates edge cases (90, -90, 180, -180) |
| `test_invalid_latitude_high` | Rejects latitude > 90 |
| `test_invalid_latitude_low` | Rejects latitude < -90 |
| `test_invalid_longitude_high` | Rejects longitude > 180 |
| `test_invalid_longitude_low` | Rejects longitude < -180 |
| `test_valid_hours` | Accepts hours 1-72 |
| `test_invalid_hours_low` | Rejects hours < 1 |
| `test_invalid_hours_high` | Rejects hours > 72 |
| `test_invalid_hours_negative` | Rejects negative hours |
| `test_full_data` | Identifies non-sparse data |
| `test_empty_list` | Identifies empty data as sparse |
| `test_all_none_values` | Identifies all-null data as sparse |
| `test_valid_payload` | Extracts data from Open-Meteo response |
| `test_missing_key` | Handles missing fields gracefully |
| `test_complete_data` | Validates complete API response |
| `test_slicing_to_hours` | Correctly slices data to requested hours |
| `test_no_air_data` | Sets quality flags when air data missing |

### test_compute.py (10 tests)

| Test | Description |
|------|-------------|
| `test_basic_average` | Computes average of numbers |
| `test_single_value` | Returns single value unchanged |
| `test_with_none_values` | Ignores None when computing average |
| `test_all_none` | Returns None for all-null input |
| `test_empty_list` | Returns None for empty list |
| `test_none_input` | Returns None for None input |
| `test_basic_min` | Finds minimum value |
| `test_basic_max` | Finds maximum value |
| `test_basic_rounding` | Rounds to specified decimals |
| `test_default_decimals` | Uses 2 decimals by default |

### test_cache.py (12 tests)

| Test | Description |
|------|-------------|
| `test_basic_key_generation` | Generates cache key "lat:lon:hours" |
| `test_key_rounds_coordinates` | Rounds coordinates to 4 decimals |
| `test_key_negative_coordinates` | Handles negative coordinates |
| `test_key_zero_coordinates` | Handles zero coordinates |
| `test_set_and_get` | Stores and retrieves values |
| `test_get_missing_key` | Returns None for missing key |
| `test_clear_removes_all` | Clears all cached values |
| `test_overwrite_existing_key` | Overwrites existing entries |
| `test_empty_cache_stats` | Returns stats for empty cache |
| `test_stats_after_adding_items` | Updates stats after adding items |
| `test_concurrent_writes` | Thread-safe concurrent writes |
| `test_concurrent_reads_and_writes` | Thread-safe mixed operations |

### test_retry.py (10 tests)

| Test | Description |
|------|-------------|
| `test_retryable_status_codes` | Verifies 429, 500, 502, 503, 504 trigger retry |
| `test_retry_delays_exponential` | Verifies exponential backoff delays |
| `test_successful_request` | Returns JSON on success |
| `test_retry_on_500` | Retries on 500 Internal Server Error |
| `test_retry_on_429_rate_limit` | Retries on 429 Rate Limit |
| `test_no_retry_on_400` | Does NOT retry on 400 Bad Request |
| `test_max_retries_exceeded` | Fails after 4 attempts |
| `test_retry_on_connection_error` | Retries on connection errors |
| `test_get_json` | Convenience function for GET |
| `test_post_json` | Convenience function for POST |

### test_integration_analyze.py (7 tests)

| Test | Description |
|------|-------------|
| `test_analyze_with_coordinates` | Full flow with lat/lon |
| `test_analyze_with_place_name` | Full flow with place name |
| `test_analyze_missing_location` | Rejects missing location |
| `test_analyze_invalid_coordinates` | Rejects invalid coordinates |
| `test_health_check` | Health endpoint returns 200 |
| `test_geocode_valid_place` | Geocodes valid place name |
| `test_geocode_empty_place` | Rejects empty place name |

### test_dast.py (12 tests) — Dynamic Security

| Test | Description |
|------|-------------|
| `test_sql_injection_in_place_name` | Blocks SQL injection attempts |
| `test_xss_in_place_name` | Blocks XSS attempts |
| `test_command_injection_attempts` | Blocks command injection |
| `test_latitude_bounds` | Validates coordinate boundaries |
| `test_longitude_bounds` | Validates longitude boundaries |
| `test_hours_bounds` | Validates hours parameter |
| `test_extremely_long_input` | Rejects extremely long input |
| `test_error_no_stack_trace` | Errors don't expose stack traces |
| `test_error_no_internal_paths` | Errors don't expose file paths |
| `test_no_auth_header_manipulation` | Blocks auth header manipulation |
| `test_rate_limit_exists` | Verifies rate limiting (30/min) |

### test_sast.py (4 tests) — Static Security

| Test | Description |
|------|-------------|
| `test_bandit_agent_module` | Scans agent/ for vulnerabilities |
| `test_bandit_service_module` | Scans service/ for vulnerabilities |
| `test_no_hardcoded_secrets` | No hardcoded API keys/passwords |
| `test_no_dangerous_functions` | No eval(), exec(), shell=True |

---

## Running Specific Tests

```bash
# All tests
pytest tests/ -v

# Only validation tests
pytest tests/test_validate.py -v

# Only security tests
pytest tests/test_dast.py tests/test_sast.py -v

# With coverage
pytest tests/ --cov=agent --cov=service
```
