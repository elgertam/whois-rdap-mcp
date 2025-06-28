#!/usr/bin/env python3
"""Test MCP protocol functionality."""

import asyncio
import json
import anyio

async def test_mcp_protocol():
    try:
        print("Connecting to MCP server...")
        
        stream = await anyio.connect_tcp("localhost", 5000)
        
        async with stream:
            # 1. Initialize connection
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            await stream.send((json.dumps(init_request) + '\n').encode())
            response = await stream.receive(4096)
            init_response = json.loads(response.decode())
            print("✓ Initialize successful")
            print(f"  Server: {init_response['result']['serverInfo']['name']} v{init_response['result']['serverInfo']['version']}")
            
            # 2. List tools
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            await stream.send((json.dumps(tools_request) + '\n').encode())
            response = await stream.receive(4096)
            tools_response = json.loads(response.decode())
            tools = tools_response['result']['tools']
            print(f"✓ Tools listed: {len(tools)} available")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
            
            # 3. Test Whois lookup
            whois_request = {
                "jsonrpc": "2.0", 
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "whois_lookup",
                    "arguments": {
                        "target": "example.com",
                        "use_cache": False
                    }
                }
            }
            
            await stream.send((json.dumps(whois_request) + '\n').encode())
            response = await stream.receive(8192)
            whois_response = json.loads(response.decode())
            
            if 'result' in whois_response:
                print("✓ Whois lookup successful")
                result_data = json.loads(whois_response['result']['content'][0]['text'])
                print(f"  Target: {result_data['target']}")
                print(f"  Success: {result_data['success']}")
                print(f"  Server: {result_data['whois_server']}")
            else:
                print("✗ Whois lookup failed")
                print(whois_response)
            
            print("\n✓ MCP protocol test completed successfully!")
            
    except Exception as e:
        print(f"✗ MCP protocol test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_protocol())