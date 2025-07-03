"""
Tests for the services modules.
"""

import pytest

from whoismcp.config import Config
from whoismcp.services import CacheService, RDAPService, WhoisService


class TestCacheService:
    """Test suite for CacheService."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(cache_ttl=3600, cache_max_size=100)

    @pytest.fixture
    async def cache_service(self, config):
        """Create test cache service."""
        service = CacheService(config)
        await service.start()
        return service

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_service):
        """Test setting and getting cache values."""
        key = "test_key"
        value = {"data": "test_value"}

        await cache_service.set(key, value)
        result = await cache_service.get(key)

        assert result == value

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache_service):
        """Test getting non-existent cache value."""
        result = await cache_service.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache_service):
        """Test deleting cache value."""
        key = "test_key"
        value = {"data": "test_value"}

        await cache_service.set(key, value)
        await cache_service.delete(key)

        result = await cache_service.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self, cache_service):
        """Test clearing all cache values."""
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")

        await cache_service.clear()

        assert await cache_service.get("key1") is None
        assert await cache_service.get("key2") is None


class TestWhoisService:
    """Test suite for WhoisService."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(whois_timeout=30)

    @pytest.fixture
    def whois_service(self, config):
        """Create test whois service."""
        return WhoisService(config)

    def test_get_domain_whois_server(self, whois_service):
        """Test getting whois server for domain."""
        server = whois_service._get_domain_whois_server("example.com")
        assert server == "whois.verisign-grs.com"

        server = whois_service._get_domain_whois_server("example.org")
        assert server == "whois.pir.org"

    def test_get_ip_whois_server(self, whois_service):
        """Test getting whois server for IP."""
        # Test ARIN range
        server = whois_service._get_ip_whois_server("8.8.8.8")
        assert server in [
            "whois.arin.net",
            "whois.ripe.net",
            "whois.apnic.net",
            "whois.lacnic.net",
            "whois.afrinic.net",
        ]

    @pytest.mark.asyncio
    async def test_lookup_domain_invalid(self, whois_service):
        """Test domain lookup with invalid domain."""
        with pytest.raises(ValueError, match="Invalid domain name"):
            await whois_service.lookup_domain("invalid..domain")


class TestRDAPService:
    """Test suite for RDAPService."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(rdap_timeout=30)

    @pytest.fixture
    def rdap_service(self, config):
        """Create test RDAP service."""
        return RDAPService(config)

    @pytest.mark.asyncio
    async def test_get_domain_servers(self, rdap_service):
        """Test getting RDAP servers for domain."""
        servers = await rdap_service._get_domain_rdap_servers("example.com")
        assert len(servers) > 0

        servers = await rdap_service._get_domain_rdap_servers("example.org")
        assert len(servers) > 0

    @pytest.mark.asyncio
    async def test_lookup_domain_invalid(self, rdap_service):
        """Test domain lookup with invalid domain."""
        with pytest.raises(ValueError, match="Invalid domain name"):
            await rdap_service.lookup_domain("invalid..domain")
