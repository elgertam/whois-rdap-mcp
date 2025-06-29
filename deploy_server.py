#!/usr/bin/env python3
"""
Deployment-ready server script for MCP Whois/RDAP Server.
This script ensures the web server is properly configured for deployment.
"""

import os
import sys
import asyncio
import threading
import time
import signal
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def run_mcp_server():
    """Run the MCP server in a separate thread."""
    try:
        from main import main as mcp_main
        asyncio.run(mcp_main())
    except Exception as e:
        print(f"MCP Server error: {e}")

def run_web_server():
    """Run the web server in main thread."""
    try:
        from simple_web_demo import start_demo
        start_demo()
    except Exception as e:
        print(f"Web Server error: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Start servers for deployment."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting MCP Whois/RDAP Server for deployment...")
    print(f"Environment: {os.getenv('NODE_ENV', 'production')}")
    
    # Start MCP server in background thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()
    
    # Give MCP server time to start
    time.sleep(2)
    print("MCP Server started on port 5001")
    
    # Start web server in main thread (for deployment)
    print("Starting web interface on port 5000...")
    print("Ready for deployment health checks at:")
    print("  GET / - Main interface")
    print("  GET /health - Health check endpoint")
    
    # This will block until terminated
    run_web_server()

if __name__ == "__main__":
    main()