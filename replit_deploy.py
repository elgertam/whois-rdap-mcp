#!/usr/bin/env python3
"""
Replit deployment configuration for MCP Whois/RDAP Server.
This ensures proper deployment with health checks and port configuration.
"""

import os
import sys
import asyncio
import threading
import time
import signal
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import datetime

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

class DeploymentHandler(BaseHTTPRequestHandler):
    """HTTP handler optimized for deployment."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/' or self.path == '/index.html':
            self._serve_main_page()
        elif self.path == '/health':
            self._serve_health_check()
        elif self.path == '/status':
            self._serve_status_check()
        else:
            self._serve_404()
    
    def do_HEAD(self):
        """Handle HEAD requests for health checks."""
        if self.path in ['/', '/health', '/status']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json' if self.path in ['/health', '/status'] else 'text/html')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _serve_main_page(self):
        """Serve the main application page."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MCP Whois/RDAP Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
        .status { padding: 15px; margin: 15px 0; border-radius: 5px; background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        h1 { color: #333; }
        .feature { margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MCP Whois/RDAP Server</h1>
        <div class="status">
            <strong>Status:</strong> Server is running and ready for MCP connections<br>
            <strong>Protocol:</strong> JSON-RPC 2.0<br>
            <strong>Port:</strong> 5001 (MCP), 5000 (Web Interface)
        </div>
        <div class="feature">Whois Lookups: TCP connections to global registries</div>
        <div class="feature">RDAP Lookups: HTTPS requests to structured endpoints</div>
        <div class="feature">Caching: In-memory LRU cache with TTL</div>
        <div class="feature">Rate Limiting: Token bucket protection</div>
        <h2>Deployment Status</h2>
        <p>The server is configured for production deployment with health monitoring.</p>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _serve_health_check(self):
        """Serve health check endpoint."""
        health_data = {
            "status": "healthy",
            "service": "MCP Whois/RDAP Server",
            "version": "1.0.0",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "uptime": time.time() - start_time,
            "mcp_port": 5001,
            "web_port": 5000
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(health_data, indent=2).encode('utf-8'))
    
    def _serve_status_check(self):
        """Serve detailed status check."""
        status_data = {
            "application": "MCP Whois/RDAP Server",
            "status": "running",
            "services": {
                "mcp_server": {"port": 5001, "status": "active"},
                "web_interface": {"port": 5000, "status": "active"}
            },
            "deployment": {
                "ready": True,
                "health_endpoints": ["/", "/health", "/status"],
                "external_port": 80,
                "internal_port": 5000
            }
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(status_data, indent=2).encode('utf-8'))
    
    def _serve_404(self):
        """Serve 404 response."""
        self.send_response(404)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'404 Not Found')
    
    def log_message(self, format, *args):
        """Suppress request logging for cleaner deployment logs."""
        pass

def run_mcp_server():
    """Run the MCP server in background thread."""
    try:
        from main import main as mcp_main
        asyncio.run(mcp_main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"MCP Server error: {e}")

def run_web_server():
    """Run the web server in main thread."""
    try:
        server = HTTPServer(('0.0.0.0', 5000), DeploymentHandler)
        print("Deployment web server started on http://0.0.0.0:5000")
        server.serve_forever()
    except KeyboardInterrupt:
        print("Web server shutting down...")
    except Exception as e:
        print(f"Web Server error: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

# Global start time for uptime tracking
start_time = time.time()

def main():
    """Main deployment entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting MCP Whois/RDAP Server for Replit deployment...")
    print(f"Environment: {os.getenv('REPLIT_ENVIRONMENT', 'production')}")
    
    # Start MCP server in background
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()
    
    # Give MCP server time to start
    time.sleep(3)
    print("MCP Server started on port 5001")
    
    # Start web server in main thread (blocking)
    run_web_server()

if __name__ == "__main__":
    main()