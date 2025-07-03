"""
Pytest configuration for WhoisMCP tests.
"""

import asyncio
from unittest.mock import Mock

import pytest

from whoismcp.config import Config


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Create a test configuration with safe defaults."""
    return Config(
        bind_host="127.0.0.1",
        bind_port=5001,
        whois_timeout=5,
        rdap_timeout=5,
        cache_ttl=300,
        cache_max_size=10,
        cache_cleanup_interval=60,
        global_rate_limit_per_second=100.0,
        global_rate_limit_burst=200,
        client_rate_limit_per_second=10.0,
        client_rate_limit_burst=20,
        log_level="DEBUG",
        max_connections=10,
        max_keepalive_connections=5,
        max_retries=1,
        retry_delay=0.1,
    )


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    return {
        "whois_service": Mock(),
        "rdap_service": Mock(),
        "cache_service": Mock(),
        "rate_limiter": Mock(),
    }
