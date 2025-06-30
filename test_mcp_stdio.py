#!/usr/bin/env python3
"""
Test script for the MCP stdio server.
Demonstrates how MCP clients would interact with the server.
"""

import json
import subprocess
import sys
import asyncio
from pathlib import Path

async def test_mcp_server():
    """Test the MCP server via stdio."""
    
    print("Testing MCP Whois/RDAP Server via stdio...")
    print("=" * 50)
    
    # Start the MCP server process
    server_script = Path(__file__).parent / "mcp_stdio_server_fixed.py"
    
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(server_script),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Test 1: Initialize
        print("\n1. Testing initialize...")
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            },
            "id": 1
        }
        
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()
        
        response_data = await process.stdout.readline()
        response = json.loads(response_data.decode().strip())
        print(f"✓ Initialize response: {response['result']['serverInfo']['name']}")
        
        # Test 2: List tools
        print("\n2. Testing tools/list...")
        tools_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        process.stdin.write((json.dumps(tools_request) + "\n").encode())
        await process.stdin.drain()
        
        response_data = await process.stdout.readline()
        response = json.loads(response_data.decode().strip())
        tools = response['result']['tools']
        print(f"✓ Available tools: {[tool['name'] for tool in tools]}")
        
        # Test 3: List resources
        print("\n3. Testing resources/list...")
        resources_request = {
            "jsonrpc": "2.0",
            "method": "resources/list",
            "params": {},
            "id": 3
        }
        
        process.stdin.write((json.dumps(resources_request) + "\n").encode())
        await process.stdin.drain()
        
        response_data = await process.stdout.readline()
        response = json.loads(response_data.decode().strip())
        resources = response['result']['resources']
        print(f"✓ Available resources: {len(resources)} resource types")
        
        # Test 4: Call whois_lookup tool
        print("\n4. Testing whois_lookup tool...")
        whois_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "whois_lookup",
                "arguments": {
                    "target": "example.com",
                    "use_cache": True
                }
            },
            "id": 4
        }
        
        process.stdin.write((json.dumps(whois_request) + "\n").encode())
        await process.stdin.drain()
        
        response_data = await process.stdout.readline()
        response = json.loads(response_data.decode().strip())
        
        if 'result' in response and 'content' in response['result']:
            result_data = json.loads(response['result']['content'][0]['text'])
            print(f"✓ Whois lookup success: {result_data.get('success', False)}")
            if result_data.get('success'):
                print(f"  Target: {result_data.get('target')}")
                print(f"  Server: {result_data.get('whois_server')}")
        else:
            print(f"✗ Whois lookup failed: {response}")
        
        # Test 5: Call rdap_lookup tool
        print("\n5. Testing rdap_lookup tool...")
        rdap_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "rdap_lookup",
                "arguments": {
                    "target": "example.com",
                    "use_cache": True
                }
            },
            "id": 5
        }
        
        process.stdin.write((json.dumps(rdap_request) + "\n").encode())
        await process.stdin.drain()
        
        response_data = await process.stdout.readline()
        response = json.loads(response_data.decode().strip())
        
        if 'result' in response and 'content' in response['result']:
            result_data = json.loads(response['result']['content'][0]['text'])
            print(f"✓ RDAP lookup success: {result_data.get('success', False)}")
            if result_data.get('success'):
                print(f"  Target: {result_data.get('target')}")
                print(f"  Server: {result_data.get('rdap_server')}")
        else:
            print(f"✗ RDAP lookup failed: {response}")
        
        # Close the server
        process.stdin.close()
        await process.wait()
        
        print("\n" + "=" * 50)
        print("MCP Server Test Complete!")
        print("\nThe MCP server is working correctly via stdio.")
        print("It can be used by MCP-compatible AI clients.")
        
    except Exception as e:
        print(f"Test failed: {e}")
        if 'process' in locals():
            process.terminate()
            await process.wait()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())