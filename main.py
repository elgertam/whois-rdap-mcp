#!/usr/bin/env python3
"""
Main entry point for deployment.
This provides a web interface demonstrating the WhoisMCP functionality.
"""

import os
import sys
import signal
from pathlib import Path

# Add the src directory to Python path for the whoismcp package
sys.path.insert(0, str(Path(__file__).parent / "src"))


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

    print("Starting WhoisMCP Web Interface...")
    print(f"Environment: {os.getenv('REPLIT_ENVIRONMENT', 'production')}")
    print()
    print("Note: This is a web interface for demonstration purposes.")
    print("To use the actual MCP server, run: ./mcp_server_new")
    print("Or use the uv command: uv run whoismcp-server")
    print("The MCP server communicates via stdin/stdout as per MCP specification.")
    print()

    # Start web server in main thread (blocking)
    print("Web Interface starting on port 5000...")
    run_web_server()


if __name__ == "__main__":
    main()
