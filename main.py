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
    
    print("Starting MCP Whois/RDAP Server Web Interface...")
    print(f"Environment: {os.getenv('REPLIT_ENVIRONMENT', 'production')}")
    print()
    print("Note: This is a web interface for demonstration purposes.")
    print("To use the actual MCP server, run: ./mcp_server")
    print("The MCP server communicates via stdin/stdout as per MCP specification.")
    print()
    
    # Start web server in main thread (blocking)
    print("Web Interface starting on port 5000...")
    run_web_server()

if __name__ == "__main__":
    main()