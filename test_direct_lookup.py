#!/usr/bin/env python3
"""Test direct lookup functionality."""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_direct_lookup():
    try:
        print("Testing direct Whois lookup...")
        
        from services.whois_service import WhoisService
        from config import Config
        
        config = Config()
        service = WhoisService(config)
        
        # Test domain lookup
        result = await service.lookup_domain("google.com")
        print(f"Whois lookup successful: {result['success']}")
        print(f"Target: {result['target']}")
        print(f"Server: {result['whois_server']}")
        
        if result['success']:
            print("Parsed data keys:", list(result['parsed_data'].keys()))
            # Show some parsed data
            for key, value in list(result['parsed_data'].items())[:3]:
                print(f"  {key}: {value}")
        else:
            print(f"Error: {result.get('error')}")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_lookup())