#!/usr/bin/env python3
"""Test server startup for debugging."""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

async def test_server():
    try:
        print("Creating config...")
        from config import Config
        config = Config()
        print(f"Config: host={config.bind_host}, port={config.bind_port}")
        
        print("Creating MCP server...")
        from mcp_server import MCPServer
        server = MCPServer(config)
        print("MCP server created successfully")
        
        print("Starting server...")
        # Test if we can bind to the port
        import anyio
        
        try:
            listener = await anyio.create_tcp_listener(
                local_host=config.bind_host,
                local_port=config.bind_port
            )
            
            print(f"Successfully bound to {config.bind_host}:{config.bind_port}")
            await listener.aclose()
            print("Server test completed successfully!")
            
        except Exception as e:
            print(f"Failed to bind to port: {e}")
            
    except Exception as e:
        print(f"Server test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server())