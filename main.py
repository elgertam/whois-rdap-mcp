#!/usr/bin/env python3
"""
Main entry point for MCP Whois/RDAP Server deployment.
This file serves as the default entry point for Replit deployments.
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
    """Run the MCP server in background thread."""
    try:
        from mcp_main import main as mcp_main
        asyncio.run(mcp_main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"MCP Server error: {e}")

def run_web_server():
    """Run the web server in main thread."""
    try:
        from simple_web_demo import start_demo
        start_demo()
    except KeyboardInterrupt:
        print("Web server shutting down...")
    except Exception as e:
        print(f"Web Server error: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Main deployment entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting MCP Whois/RDAP Server...")
    print(f"Environment: {os.getenv('REPLIT_ENVIRONMENT', 'production')}")
    
    # Start MCP server in background
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()
    
    # Give MCP server time to start
    time.sleep(3)
    print("MCP Server started on port 5001")
    
    # Start web server in main thread (blocking)
    print("Web Interface starting on port 5000...")
    run_web_server()

if __name__ == "__main__":
    main()