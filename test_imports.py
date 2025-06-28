#!/usr/bin/env python3
"""Test imports for debugging."""

try:
    print("Testing imports...")
    
    print("Importing config...")
    from config import Config
    
    print("Importing models...")
    from models.domain_models import WhoisResult, RDAPResult
    from models.mcp_models import MCPRequest, MCPResponse
    
    print("Importing utils...")
    from utils.validators import is_valid_domain, is_valid_ip
    from utils.rate_limiter import RateLimiter
    from utils.parsers import WhoisParser
    
    print("Importing services...")
    from services.whois_service import WhoisService
    from services.rdap_service import RDAPService
    from services.cache_service import CacheService
    
    print("Importing main MCP server...")
    from mcp_server import MCPServer
    
    print("All imports successful!")
    
    # Test basic config
    config = Config()
    print(f"Config created: bind_host={config.bind_host}, bind_port={config.bind_port}")
    
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()