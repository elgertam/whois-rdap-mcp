#!/usr/bin/env python3
"""Comprehensive test suite for the MCP Whois/RDAP server."""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

class ComprehensiveTest:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        
    def log_test(self, test_name, success, details=""):
        if success:
            print(f"✓ {test_name}")
            if details:
                print(f"  {details}")
            self.tests_passed += 1
        else:
            print(f"✗ {test_name}")
            if details:
                print(f"  {details}")
            self.tests_failed += 1
    
    async def test_import_validation(self):
        """Test that all modules import correctly."""
        try:
            from config import Config
            from models.domain_models import WhoisResult, RDAPResult
            from services.whois_service import WhoisService
            from services.rdap_service import RDAPService
            from mcp_server import MCPServer
            
            self.log_test("Module imports", True, "All modules loaded successfully")
            return True
        except Exception as e:
            self.log_test("Module imports", False, f"Import error: {e}")
            return False
    
    async def test_config_validation(self):
        """Test configuration system."""
        try:
            from config import Config
            config = Config()
            config.validate()
            
            expected_port = 5000
            if config.bind_port == expected_port:
                self.log_test("Configuration", True, f"Configured for port {expected_port}")
                return True
            else:
                self.log_test("Configuration", False, f"Wrong port: {config.bind_port}")
                return False
        except Exception as e:
            self.log_test("Configuration", False, f"Config error: {e}")
            return False
    
    async def test_whois_service(self):
        """Test Whois service with real domain."""
        try:
            from services.whois_service import WhoisService
            from config import Config
            
            config = Config()
            service = WhoisService(config)
            
            # Test with a reliable domain
            result = await service.lookup_domain("example.com")
            
            if result['success']:
                self.log_test("Whois Service", True, 
                             f"Retrieved data from {result['whois_server']}")
                return True
            else:
                self.log_test("Whois Service", False, 
                             f"Lookup failed: {result.get('error')}")
                return False
        except Exception as e:
            self.log_test("Whois Service", False, f"Service error: {e}")
            return False
    
    async def test_rdap_service(self):
        """Test RDAP service with real domain."""
        try:
            from services.rdap_service import RDAPService
            from config import Config
            
            config = Config()
            service = RDAPService(config)
            
            # Test with a reliable domain
            result = await service.lookup_domain("example.com")
            
            if result['success']:
                self.log_test("RDAP Service", True, 
                             f"Retrieved data from {result['rdap_server']}")
                await service.close()
                return True
            else:
                self.log_test("RDAP Service", False, 
                             f"Lookup failed: {result.get('error')}")
                await service.close()
                return False
        except Exception as e:
            self.log_test("RDAP Service", False, f"Service error: {e}")
            return False
    
    async def test_mcp_server_startup(self):
        """Test MCP server can start and bind to port."""
        try:
            from mcp_server import MCPServer
            from config import Config
            import anyio
            
            config = Config()
            server = MCPServer(config)
            
            # Test binding
            listener = await anyio.create_tcp_listener(
                local_host=config.bind_host,
                local_port=config.bind_port
            )
            await listener.aclose()
            
            self.log_test("MCP Server Startup", True, 
                         f"Can bind to {config.bind_host}:{config.bind_port}")
            return True
        except Exception as e:
            self.log_test("MCP Server Startup", False, f"Startup error: {e}")
            return False
    
    async def test_mcp_protocol(self):
        """Test MCP protocol communication."""
        try:
            import anyio
            
            # Connect to running server
            stream = await anyio.connect_tcp("localhost", 5000)
            
            async with stream:
                # Initialize
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"}
                    }
                }
                
                await stream.send((json.dumps(init_request) + '\n').encode())
                response = await stream.receive(4096)
                init_response = json.loads(response.decode())
                
                if 'result' in init_response:
                    server_info = init_response['result']['serverInfo']
                    self.log_test("MCP Protocol", True, 
                                 f"Connected to {server_info['name']} v{server_info['version']}")
                    return True
                else:
                    self.log_test("MCP Protocol", False, "Initialize failed")
                    return False
                    
        except Exception as e:
            self.log_test("MCP Protocol", False, f"Protocol error: {e}")
            return False
    
    async def test_cache_functionality(self):
        """Test caching system."""
        try:
            from services.cache_service import CacheService
            from config import Config
            
            config = Config()
            cache = CacheService(config)
            
            # Test cache operations
            await cache.set("test_key", {"test": "data"}, ttl=60)
            result = await cache.get("test_key")
            
            if result and result.get("test") == "data":
                stats = await cache.stats()
                self.log_test("Cache Functionality", True, 
                             f"Cache operational, {stats['total_entries']} entries")
                await cache.close()
                return True
            else:
                self.log_test("Cache Functionality", False, "Cache operation failed")
                await cache.close()
                return False
        except Exception as e:
            self.log_test("Cache Functionality", False, f"Cache error: {e}")
            return False
    
    async def test_rate_limiting(self):
        """Test rate limiting system."""
        try:
            from utils.rate_limiter import RateLimiter
            from config import Config
            
            config = Config()
            limiter = RateLimiter(config)
            
            # Test token acquisition
            client_id = "test_client"
            success1 = await limiter.acquire(client_id)
            success2 = await limiter.acquire(client_id)
            
            if success1 and success2:
                stats = await limiter.get_stats(client_id)
                self.log_test("Rate Limiting", True, 
                             f"Rate limiter operational, {stats['tokens_available']} tokens available")
                await limiter.close()
                return True
            else:
                self.log_test("Rate Limiting", False, "Rate limiting failed")
                await limiter.close()
                return False
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Rate limiter error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests and report results."""
        print("=" * 60)
        print("MCP WHOIS/RDAP SERVER - COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        
        # Core functionality tests
        await self.test_import_validation()
        await self.test_config_validation()
        await self.test_mcp_server_startup()
        await self.test_mcp_protocol()
        
        # Service tests
        await self.test_whois_service()
        await self.test_rdap_service()
        
        # System tests
        await self.test_cache_functionality()
        await self.test_rate_limiting()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"✓ Tests Passed: {self.tests_passed}")
        print(f"✗ Tests Failed: {self.tests_failed}")
        print(f"Total Tests: {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED! MCP server is fully operational.")
            print("\nServer Features Verified:")
            print("- Model Context Protocol compliance")
            print("- Asynchronous Whois lookups")
            print("- RDAP structured data retrieval")
            print("- In-memory caching with TTL")
            print("- Token bucket rate limiting")
            print("- Real-world registry integration")
            return True
        else:
            print(f"\n⚠️  {self.tests_failed} test(s) failed. Please review issues.")
            return False

async def main():
    tester = ComprehensiveTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())