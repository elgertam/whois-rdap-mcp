#!/usr/bin/env python3
"""Test RDAP lookup functionality."""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_rdap_lookup():
    try:
        print("Testing RDAP lookup...")
        
        from services.rdap_service import RDAPService
        from config import Config
        
        config = Config()
        service = RDAPService(config)
        
        # Test domain lookup
        result = await service.lookup_domain("google.com")
        print(f"RDAP lookup successful: {result['success']}")
        print(f"Target: {result['target']}")
        print(f"Server: {result['rdap_server']}")
        
        if result['success']:
            print("Response data keys:", list(result['response_data'].keys()))
            # Show some key RDAP data
            if 'ldhName' in result['response_data']:
                print(f"  Domain: {result['response_data']['ldhName']}")
            if 'status' in result['response_data']:
                print(f"  Status: {result['response_data']['status']}")
        else:
            print(f"Error: {result.get('error')}")
        
        await service.close()
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rdap_lookup())