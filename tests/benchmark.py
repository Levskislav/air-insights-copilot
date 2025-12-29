"""
tests/benchmark.py
==================
Performance benchmark for OutdoorMate API.

Tests:
1. Cold request (no cache) latency
2. Cached request latency
3. Concurrent requests throughput

Target: Cached p95 latency < 2 seconds

Usage:
    python tests/benchmark.py
    
    Or with pytest:
    pytest tests/benchmark.py -v -s
"""

import asyncio
import statistics
import time
from typing import NamedTuple

import httpx


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://localhost:8000"
ANALYZE_ENDPOINT = f"{BASE_URL}/analyze"

# Test payload
TEST_PAYLOAD = {
    "latitude": 42.6977,
    "longitude": 23.3219,
    "hours": 6
}

# Number of requests for each test
WARM_UP_REQUESTS = 2
BENCHMARK_REQUESTS = 20
CONCURRENT_REQUESTS = 10


# =============================================================================
# RESULT TYPES
# =============================================================================

class BenchmarkResult(NamedTuple):
    """Result of a benchmark run."""
    name: str
    requests: int
    min_ms: float
    max_ms: float
    avg_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    success_rate: float


# =============================================================================
# BENCHMARK FUNCTIONS
# =============================================================================

async def single_request(client: httpx.AsyncClient) -> tuple[bool, float]:
    """
    Make a single request and return success status and latency.
    
    Returns:
        Tuple of (success: bool, latency_ms: float)
    """
    start = time.perf_counter()
    try:
        response = await client.post(
            ANALYZE_ENDPOINT,
            json=TEST_PAYLOAD,
            timeout=30.0
        )
        latency = (time.perf_counter() - start) * 1000
        return response.status_code == 200, latency
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        print(f"  Request failed: {e}")
        return False, latency


def calculate_percentile(data: list[float], percentile: float) -> float:
    """Calculate percentile value from sorted data."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = int(len(sorted_data) * percentile / 100)
    return sorted_data[min(index, len(sorted_data) - 1)]


def analyze_results(name: str, latencies: list[float], successes: list[bool]) -> BenchmarkResult:
    """Analyze benchmark results and return statistics."""
    successful_latencies = [l for l, s in zip(latencies, successes) if s]
    
    if not successful_latencies:
        return BenchmarkResult(
            name=name,
            requests=len(latencies),
            min_ms=0, max_ms=0, avg_ms=0,
            p50_ms=0, p95_ms=0, p99_ms=0,
            success_rate=0.0
        )
    
    return BenchmarkResult(
        name=name,
        requests=len(latencies),
        min_ms=min(successful_latencies),
        max_ms=max(successful_latencies),
        avg_ms=statistics.mean(successful_latencies),
        p50_ms=calculate_percentile(successful_latencies, 50),
        p95_ms=calculate_percentile(successful_latencies, 95),
        p99_ms=calculate_percentile(successful_latencies, 99),
        success_rate=sum(successes) / len(successes) * 100
    )


# =============================================================================
# BENCHMARK TESTS
# =============================================================================

async def benchmark_sequential(client: httpx.AsyncClient, n: int, name: str) -> BenchmarkResult:
    """Run N sequential requests."""
    latencies = []
    successes = []
    
    for i in range(n):
        success, latency = await single_request(client)
        latencies.append(latency)
        successes.append(success)
        print(f"  Request {i+1}/{n}: {latency:.1f}ms {'✓' if success else '✗'}")
    
    return analyze_results(name, latencies, successes)


async def benchmark_concurrent(client: httpx.AsyncClient, n: int) -> BenchmarkResult:
    """Run N concurrent requests."""
    tasks = [single_request(client) for _ in range(n)]
    results = await asyncio.gather(*tasks)
    
    latencies = [r[1] for r in results]
    successes = [r[0] for r in results]
    
    return analyze_results("Concurrent", latencies, successes)


# =============================================================================
# MAIN BENCHMARK
# =============================================================================

async def run_benchmark():
    """Run the complete benchmark suite."""
    print("=" * 60)
    print("OutdoorMate API Performance Benchmark")
    print("=" * 60)
    print(f"Target: {ANALYZE_ENDPOINT}")
    print(f"Payload: {TEST_PAYLOAD}")
    print()
    
    async with httpx.AsyncClient() as client:
        # Check if server is running
        try:
            response = await client.get(BASE_URL, timeout=5.0)
            if response.status_code != 200:
                print("❌ Server not responding correctly")
                return
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("   Make sure the server is running:")
            print("   uvicorn service.main:app --port 8000")
            return
        
        print("✓ Server is running")
        print()
        
        results = []
        
        # Test 1: Warm-up (populates cache)
        print(f"1. Warm-up ({WARM_UP_REQUESTS} requests)")
        print("-" * 40)
        await benchmark_sequential(client, WARM_UP_REQUESTS, "Warm-up")
        print()
        
        # Test 2: Cached requests (sequential)
        print(f"2. Cached Requests ({BENCHMARK_REQUESTS} sequential)")
        print("-" * 40)
        cached_result = await benchmark_sequential(client, BENCHMARK_REQUESTS, "Cached")
        results.append(cached_result)
        print()
        
        # Test 3: Concurrent requests
        print(f"3. Concurrent Requests ({CONCURRENT_REQUESTS} parallel)")
        print("-" * 40)
        concurrent_result = await benchmark_concurrent(client, CONCURRENT_REQUESTS)
        results.append(concurrent_result)
        
        for i, (success, latency) in enumerate([(True, concurrent_result.avg_ms)] * CONCURRENT_REQUESTS):
            pass  # Results already printed
        print(f"  All {CONCURRENT_REQUESTS} requests completed")
        print()
        
        # Print summary
        print("=" * 60)
        print("RESULTS SUMMARY")
        print("=" * 60)
        print()
        print(f"{'Test':<15} {'Requests':>8} {'Avg':>8} {'p50':>8} {'p95':>8} {'p99':>8} {'Success':>8}")
        print("-" * 70)
        
        for r in results:
            print(f"{r.name:<15} {r.requests:>8} {r.avg_ms:>7.1f}ms {r.p50_ms:>7.1f}ms {r.p95_ms:>7.1f}ms {r.p99_ms:>7.1f}ms {r.success_rate:>7.1f}%")
        
        print()
        print("=" * 60)
        print("PASS/FAIL CRITERIA")
        print("=" * 60)
        
        # Check p95 target
        p95_target = 2000  # 2 seconds
        cached_p95 = cached_result.p95_ms
        
        if cached_p95 < p95_target:
            print(f"✅ Cached p95 latency: {cached_p95:.1f}ms < {p95_target}ms target")
        else:
            print(f"❌ Cached p95 latency: {cached_p95:.1f}ms > {p95_target}ms target")
        
        # Check success rate
        if cached_result.success_rate >= 99:
            print(f"✅ Success rate: {cached_result.success_rate:.1f}%")
        else:
            print(f"⚠️  Success rate: {cached_result.success_rate:.1f}% (target: 99%+)")
        
        print()


# =============================================================================
# PYTEST INTEGRATION
# =============================================================================

def test_cached_latency_under_2_seconds():
    """Pytest: Verify cached p95 latency is under 2 seconds."""
    import pytest
    
    async def run():
        async with httpx.AsyncClient() as client:
            # Warm-up
            await single_request(client)
            await single_request(client)
            
            # Benchmark
            latencies = []
            successes = []
            for _ in range(10):
                success, latency = await single_request(client)
                latencies.append(latency)
                successes.append(success)
            
            result = analyze_results("test", latencies, successes)
            assert result.p95_ms < 2000, f"p95 latency {result.p95_ms:.1f}ms exceeds 2000ms"
            assert result.success_rate >= 90, f"Success rate {result.success_rate:.1f}% below 90%"
    
    asyncio.run(run())


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    asyncio.run(run_benchmark())

