#!/usr/bin/env python3
"""
Start both the MCP server and web interface.
"""

import asyncio
import threading
import time
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from main import main as mcp_main
from simple_web_demo import start_demo

def run_mcp_server():
    """Run the MCP server in a separate thread."""
    try:
        asyncio.run(mcp_main())
    except Exception as e:
        print(f"MCP Server error: {e}")

def run_web_server():
    """Run the web server in a separate thread."""
    try:
        start_demo()
    except Exception as e:
        print(f"Web Server error: {e}")

def main():
    """Start both servers."""
    print("Starting MCP Whois/RDAP Server with Web Interface...")
    
    # Start MCP server in background thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()
    
    # Give MCP server time to start
    time.sleep(2)
    
    # Start web server in main thread (so it can handle the HTTP requests)
    print("MCP Server started on port 5000")
    print("Web Interface starting on port 8000...")
    start_demo()

if __name__ == "__main__":
    main()