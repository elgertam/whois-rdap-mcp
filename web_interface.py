#!/usr/bin/env python3
"""
Simple web interface to demonstrate MCP server functionality.
"""

import asyncio
import json
from typing import Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import anyio

class MCPWebInterface(BaseHTTPRequestHandler):
    """HTTP handler to provide web interface for MCP server."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self._serve_main_page()
        elif parsed_path.path == '/api/whois':
            self._handle_whois_lookup(parsed_path.query)
        elif parsed_path.path == '/api/rdap':
            self._handle_rdap_lookup(parsed_path.query)
        elif parsed_path.path == '/api/status':
            self._handle_status_check()
        else:
            self._serve_404()
    
    def do_POST(self):
        """Handle POST requests for tool calls."""
        if self.path == '/api/lookup':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                result = asyncio.run(self._call_mcp_tool(data))
                self._send_json_response(result)
            except Exception as e:
                self._send_error_response(str(e))
        else:
            self._serve_404()
    
    def _serve_main_page(self):
        """Serve the main demo page."""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>MCP Whois/RDAP Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-group { margin: 20px 0; }
        input, select, button { padding: 10px; margin: 5px; }
        .result { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .success { border-left: 4px solid #4CAF50; }
        .error { border-left: 4px solid #f44336; }
        pre { overflow-x: auto; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MCP Whois/RDAP Server</h1>
        <p>Model Context Protocol server for domain and IP address lookups</p>
        
        <div class="form-group">
            <label>Target (domain or IP):</label>
            <input type="text" id="target" placeholder="example.com or 8.8.8.8" value="example.com" style="width: 200px;">
        </div>
        
        <div class="form-group">
            <label>Lookup method:</label>
            <select id="method">
                <option value="whois">Whois Lookup</option>
                <option value="rdap">RDAP Lookup</option>
            </select>
        </div>
        
        <div class="form-group">
            <button onclick="performLookup()">Perform Lookup</button>
            <button onclick="checkStatus()">Check Server Status</button>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        async function performLookup() {
            const target = document.getElementById('target').value;
            const method = document.getElementById('method').value;
            const resultDiv = document.getElementById('result');
            
            if (!target) {
                resultDiv.innerHTML = '<div class="result error">Please enter a target domain or IP address.</div>';
                return;
            }
            
            resultDiv.innerHTML = '<div class="result">Performing lookup...</div>';
            
            try {
                const response = await fetch('/api/lookup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        method: method,
                        target: target
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <h3>Lookup Successful</h3>
                            <p><strong>Target:</strong> ${data.result.target}</p>
                            <p><strong>Method:</strong> ${method.toUpperCase()}</p>
                            <p><strong>Server:</strong> ${data.result.whois_server || data.result.rdap_server}</p>
                            <details>
                                <summary>View Full Response</summary>
                                <pre>${JSON.stringify(data.result, null, 2)}</pre>
                            </details>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <h3>Lookup Failed</h3>
                            <p>${data.error}</p>
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="result error">
                        <h3>Request Failed</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        async function checkStatus() {
            const resultDiv = document.getElementById('result');
            
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                resultDiv.innerHTML = `
                    <div class="result success">
                        <h3>Server Status</h3>
                        <p><strong>MCP Server:</strong> ${data.mcp_server_running ? 'Running' : 'Not responding'}</p>
                        <p><strong>Available Tools:</strong> ${data.tools.join(', ')}</p>
                        <p><strong>Server Info:</strong> ${data.server_info.name} v${data.server_info.version}</p>
                    </div>
                `;
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="result error">
                        <h3>Status Check Failed</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    async def _call_mcp_tool(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP server tool via JSON-RPC."""
        try:
            # Connect to MCP server
            stream = await anyio.connect_tcp("localhost", 5000)
            
            async with stream:
                # Initialize connection
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "web-interface", "version": "1.0"}
                    }
                }
                
                await stream.send((json.dumps(init_request) + '\n').encode())
                await stream.receive(4096)  # Read init response
                
                # Call tool
                tool_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": f"{data['method']}_lookup",
                        "arguments": {
                            "target": data['target'],
                            "use_cache": True
                        }
                    }
                }
                
                await stream.send((json.dumps(tool_request) + '\n').encode())
                response = await stream.receive(8192)
                
                try:
                    mcp_response = json.loads(response.decode())
                    
                    if 'result' in mcp_response:
                        result_text = mcp_response['result']['content'][0]['text']
                        result_data = json.loads(result_text)
                        return {"success": True, "result": result_data}
                    else:
                        return {"success": False, "error": "MCP server returned error"}
                except json.JSONDecodeError:
                    # Handle the JSON parsing issue by reading in chunks
                    buffer = response
                    while True:
                        try:
                            mcp_response = json.loads(buffer.decode())
                            break
                        except json.JSONDecodeError:
                            additional = await stream.receive(1024)
                            if not additional:
                                break
                            buffer += additional
                    
                    if 'result' in mcp_response:
                        result_text = mcp_response['result']['content'][0]['text']
                        result_data = json.loads(result_text)
                        return {"success": True, "result": result_data}
                    else:
                        return {"success": False, "error": "Failed to parse MCP response"}
                        
        except Exception as e:
            return {"success": False, "error": f"MCP connection failed: {str(e)}"}
    
    async def _check_mcp_status(self) -> Dict[str, Any]:
        """Check MCP server status."""
        try:
            stream = await anyio.connect_tcp("localhost", 5000)
            
            async with stream:
                # Initialize
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "status-check", "version": "1.0"}
                    }
                }
                
                await stream.send((json.dumps(init_request) + '\n').encode())
                response = await stream.receive(4096)
                init_response = json.loads(response.decode())
                
                # List tools
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list"
                }
                
                await stream.send((json.dumps(tools_request) + '\n').encode())
                response = await stream.receive(4096)
                tools_response = json.loads(response.decode())
                
                return {
                    "mcp_server_running": True,
                    "server_info": init_response['result']['serverInfo'],
                    "tools": [tool['name'] for tool in tools_response['result']['tools']]
                }
                
        except Exception as e:
            return {
                "mcp_server_running": False,
                "error": str(e),
                "tools": [],
                "server_info": {}
            }
    
    def _handle_status_check(self):
        """Handle status check request."""
        try:
            status = asyncio.run(self._check_mcp_status())
            self._send_json_response(status)
        except Exception as e:
            self._send_error_response(str(e))
    
    def _send_json_response(self, data: Dict[str, Any]):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_error_response(self, error: str):
        """Send error response."""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": error}).encode())
    
    def _serve_404(self):
        """Serve 404 page."""
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>404 Not Found</h1>')
    
    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        pass

def start_web_server():
    """Start the web server."""
    server = HTTPServer(('0.0.0.0', 5000), MCPWebInterface)
    print("Web interface started on http://0.0.0.0:5000")
    server.serve_forever()

if __name__ == '__main__':
    start_web_server()