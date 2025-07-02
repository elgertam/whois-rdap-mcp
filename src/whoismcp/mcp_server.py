#!/usr/bin/env python3
"""
MCP Server for Whois/RDAP lookups using stdio communication.
This implements the Model Context Protocol specification for AI integration.
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
import structlog

from whoismcp.config import Config
from whoismcp.services.whois_service import WhoisService
from whoismcp.services.rdap_service import RDAPService
from whoismcp.services.cache_service import CacheService
from whoismcp.utils.rate_limiter import RateLimiter
from whoismcp.utils.validators import is_valid_domain, is_valid_ip

logger = structlog.get_logger(__name__)


class MCPServer:
    """MCP Server that communicates via stdin/stdout."""
    
    def __init__(self) -> None:
        self.config = Config.from_env()
        self.whois_service = WhoisService(self.config)
        self.rdap_service = RDAPService(self.config)
        self.cache_service = CacheService(self.config)
        self.rate_limiter = RateLimiter(self.config)
        
        # Server info
        self.server_info = {
            "name": "whoismcp",
            "version": "1.0.0"
        }
        
        # Define available tools
        self.tools = [
            {
                "name": "whois_lookup",
                "description": "Perform Whois lookup for domain or IP address",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Domain name or IP address to lookup"
                        },
                        "use_cache": {
                            "type": "boolean",
                            "description": "Whether to use cached results",
                            "default": True
                        }
                    },
                    "required": ["target"]
                }
            },
            {
                "name": "rdap_lookup",
                "description": "Perform RDAP lookup for domain or IP address",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Domain name or IP address to lookup"
                        },
                        "use_cache": {
                            "type": "boolean",
                            "description": "Whether to use cached results",
                            "default": True
                        }
                    },
                    "required": ["target"]
                }
            }
        ]
        
        # Define available resources
        self.resources = [
            {
                "uri": "whois://domain/{domain}",
                "name": "Domain Whois Information",
                "description": "Retrieve Whois information for a domain name",
                "mimeType": "application/json"
            },
            {
                "uri": "whois://ip/{ip}",
                "name": "IP Whois Information", 
                "description": "Retrieve Whois information for an IP address",
                "mimeType": "application/json"
            },
            {
                "uri": "rdap://domain/{domain}",
                "name": "Domain RDAP Information",
                "description": "Retrieve RDAP information for a domain name",
                "mimeType": "application/json"
            },
            {
                "uri": "rdap://ip/{ip}",
                "name": "IP RDAP Information",
                "description": "Retrieve RDAP information for an IP address", 
                "mimeType": "application/json"
            }
        ]

    def write_message(self, message: Dict[str, Any]) -> None:
        """Write a message to stdout."""
        json_str = json.dumps(message)
        print(json_str, flush=True)
        
    def read_message(self) -> Optional[Dict[str, Any]]:
        """Read a message from stdin."""
        try:
            line = sys.stdin.readline()
            if not line:
                return None
            return json.loads(line.strip())
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON", error=str(e))
            return None
        except Exception as e:
            logger.error("Failed to read message", error=str(e))
            return None

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": self.server_info
        }

    async def handle_list_tools(self) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {"tools": self.tools}

    async def handle_list_resources(self) -> Dict[str, Any]:
        """Handle resources/list request."""
        return {"resources": self.resources}

    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "whois_lookup":
                return await self._handle_whois_lookup(arguments)
            elif tool_name == "rdap_lookup":
                return await self._handle_rdap_lookup(arguments)
            else:
                return {
                    "isError": True,
                    "content": [{
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }]
                }
        except Exception as e:
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            return {
                "isError": True,
                "content": [{
                    "type": "text", 
                    "text": f"Tool execution failed: {str(e)}"
                }]
            }

    async def _handle_whois_lookup(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle whois lookup tool call."""
        target = arguments.get("target")
        use_cache = arguments.get("use_cache", True)
        
        if not target:
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": "Missing required argument: target"
                }]
            }
        
        # Check rate limiting
        if not await self.rate_limiter.acquire("mcp_client"):
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": "Rate limit exceeded. Please try again later."
                }]
            }
        
        # Check cache if enabled
        cache_key = f"whois:{target}"
        if use_cache:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(cached_result, indent=2)
                    }]
                }
        
        # Determine if target is domain or IP and call appropriate method
        try:
            if is_valid_domain(target):
                result_dict = await self.whois_service.lookup_domain(target)
            elif is_valid_ip(target):
                result_dict = await self.whois_service.lookup_ip(target)
            else:
                return {
                    "isError": True,
                    "content": [{
                        "type": "text",
                        "text": f"Invalid target format: {target}. Must be a domain name or IP address."
                    }]
                }
            
            # Cache result if successful
            if use_cache and result_dict.get('success'):
                await self.cache_service.set(cache_key, result_dict)
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result_dict, indent=2, default=str)
                }]
            }
            
        except Exception as e:
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"Whois lookup failed: {str(e)}"
                }]
            }

    async def _handle_rdap_lookup(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RDAP lookup tool call."""
        target = arguments.get("target")
        use_cache = arguments.get("use_cache", True)
        
        if not target:
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": "Missing required argument: target"
                }]
            }
        
        # Check rate limiting
        if not await self.rate_limiter.acquire("mcp_client"):
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": "Rate limit exceeded. Please try again later."
                }]
            }
        
        # Check cache if enabled
        cache_key = f"rdap:{target}"
        if use_cache:
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(cached_result, indent=2)
                    }]
                }
        
        # Determine if target is domain or IP and call appropriate method
        try:
            if is_valid_domain(target):
                result_dict = await self.rdap_service.lookup_domain(target)
            elif is_valid_ip(target):
                result_dict = await self.rdap_service.lookup_ip(target)
            else:
                return {
                    "isError": True,
                    "content": [{
                        "type": "text",
                        "text": f"Invalid target format: {target}. Must be a domain name or IP address."
                    }]
                }
            
            # Cache result if successful
            if use_cache and result_dict.get('success'):
                await self.cache_service.set(cache_key, result_dict)
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result_dict, indent=2, default=str)
                }]
            }
            
        except Exception as e:
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"RDAP lookup failed: {str(e)}"
                }]
            }

    async def handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri", "")
        
        try:
            if uri.startswith("whois://domain/"):
                domain = uri.replace("whois://domain/", "")
                result_dict = await self.whois_service.lookup_domain(domain)
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(result_dict, indent=2, default=str)
                    }]
                }
            elif uri.startswith("whois://ip/"):
                ip = uri.replace("whois://ip/", "")
                result_dict = await self.whois_service.lookup_ip(ip)
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(result_dict, indent=2, default=str)
                    }]
                }
            elif uri.startswith("rdap://domain/"):
                domain = uri.replace("rdap://domain/", "")
                result_dict = await self.rdap_service.lookup_domain(domain)
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(result_dict, indent=2, default=str)
                    }]
                }
            elif uri.startswith("rdap://ip/"):
                ip = uri.replace("rdap://ip/", "")
                result_dict = await self.rdap_service.lookup_ip(ip)
                return {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(result_dict, indent=2, default=str)
                    }]
                }
            else:
                return {
                    "isError": True,
                    "contents": [{
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": f"Unsupported resource URI: {uri}"
                    }]
                }
        except Exception as e:
            logger.error("Resource read failed", uri=uri, error=str(e))
            return {
                "isError": True,
                "contents": [{
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": f"Failed to read resource: {str(e)}"
                }]
            }

    async def process_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools()
            elif method == "tools/call":
                result = await self.handle_call_tool(params)
            elif method == "resources/list":
                result = await self.handle_list_resources()
            elif method == "resources/read":
                result = await self.handle_read_resource(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            logger.error("Request processing failed", method=method, error=str(e))
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def run(self) -> None:
        """Main server loop."""
        logger.info("MCP stdio server starting")
        
        # Start cache service
        await self.cache_service.start()
        
        try:
            while True:
                # Read request from stdin
                request = self.read_message()
                if request is None:
                    break
                
                # Process request
                response = await self.process_request(request)
                if response:
                    self.write_message(response)
                    
        except KeyboardInterrupt:
            logger.info("Server shutting down")
        except Exception as e:
            logger.error("Server error", error=str(e))
            raise


def main() -> None:
    """Main entry point."""
    async def run_server():
        server = MCPServer()
        await server.run()
    
    asyncio.run(run_server())


if __name__ == "__main__":
    main()