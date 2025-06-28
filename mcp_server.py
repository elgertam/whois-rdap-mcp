"""
Model Context Protocol Server implementation.
Handles JSON-RPC 2.0 communication and MCP protocol compliance.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
import anyio
from pydantic import ValidationError
import structlog

from models.mcp_models import (
    MCPRequest, MCPResponse, MCPError, ResourceDefinition,
    ToolDefinition, WhoisRequest, RDAPRequest
)
from services.whois_service import WhoisService
from services.rdap_service import RDAPService
from services.cache_service import CacheService
from utils.rate_limiter import RateLimiter
from config import Config

logger = structlog.get_logger(__name__)


class MCPServer:
    """Model Context Protocol server for Whois and RDAP services."""
    
    def __init__(self, config: Config):
        self.config = config
        self.whois_service = WhoisService(config)
        self.rdap_service = RDAPService(config)
        self.cache_service = CacheService(config)
        self.rate_limiter = RateLimiter(config)
        
        # MCP protocol definitions
        self.resources = self._define_resources()
        self.tools = self._define_tools()
        
    def _define_resources(self) -> List[ResourceDefinition]:
        """Define MCP resources for domain and IP information."""
        return [
            ResourceDefinition(
                uri="whois://domain/{domain}",
                name="Domain Whois Information",
                description="Retrieve Whois information for a domain name",
                mimeType="application/json"
            ),
            ResourceDefinition(
                uri="whois://ip/{ip}",
                name="IP Whois Information", 
                description="Retrieve Whois information for an IP address",
                mimeType="application/json"
            ),
            ResourceDefinition(
                uri="rdap://domain/{domain}",
                name="Domain RDAP Information",
                description="Retrieve RDAP information for a domain name",
                mimeType="application/json"
            ),
            ResourceDefinition(
                uri="rdap://ip/{ip}",
                name="IP RDAP Information",
                description="Retrieve RDAP information for an IP address", 
                mimeType="application/json"
            )
        ]
    
    def _define_tools(self) -> List[ToolDefinition]:
        """Define MCP tools for domain and IP lookups."""
        return [
            ToolDefinition(
                name="whois_lookup",
                description="Perform Whois lookup for domain or IP address",
                inputSchema={
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
            ),
            ToolDefinition(
                name="rdap_lookup", 
                description="Perform RDAP lookup for domain or IP address",
                inputSchema={
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
            )
        ]
    
    async def start(self):
        """Start the MCP server."""
        try:
            async with anyio.create_tcp_listener(
                local_host=self.config.bind_host,
                local_port=self.config.bind_port
            ) as listener:
                logger.info("MCP server listening", 
                           host=self.config.bind_host, 
                           port=self.config.bind_port)
                
                await listener.serve(self._handle_client)
                
        except Exception as e:
            logger.error("Failed to start MCP server", error=str(e))
            raise
    
    async def _handle_client(self, stream: anyio.abc.SocketStream):
        """Handle individual client connections."""
        client_id = str(uuid.uuid4())[:8]
        logger.info("New client connected", client_id=client_id)
        
        try:
            async with stream:
                while True:
                    # Read JSON-RPC message
                    data = await self._read_message(stream)
                    if not data:
                        break
                    
                    # Process request and send response
                    response = await self._process_request(data, client_id)
                    if response:
                        await self._send_message(stream, response)
                        
        except anyio.EndOfStream:
            logger.info("Client disconnected", client_id=client_id)
        except Exception as e:
            logger.error("Error handling client", 
                        client_id=client_id, error=str(e))
    
    async def _read_message(self, stream: anyio.abc.SocketStream) -> Optional[Dict[str, Any]]:
        """Read JSON-RPC message from stream."""
        try:
            # Read until newline (simple framing)
            buffer = b""
            while True:
                chunk = await stream.receive(1024)
                if not chunk:
                    return None
                
                buffer += chunk
                if b'\n' in buffer:
                    line = buffer.split(b'\n', 1)[0]
                    return json.loads(line.decode('utf-8'))
                    
        except Exception as e:
            logger.warning("Failed to read message", error=str(e))
            return None
    
    async def _send_message(self, stream: anyio.abc.SocketStream, message: Dict[str, Any]):
        """Send JSON-RPC message to stream."""
        try:
            data = json.dumps(message) + '\n'
            await stream.send(data.encode('utf-8'))
        except Exception as e:
            logger.warning("Failed to send message", error=str(e))
    
    async def _process_request(self, data: Dict[str, Any], client_id: str) -> Optional[Dict[str, Any]]:
        """Process JSON-RPC request and return response."""
        try:
            # Parse MCP request
            request = MCPRequest.model_validate(data)
            logger.info("Processing request", 
                       client_id=client_id,
                       method=request.method,
                       request_id=request.id)
            
            # Handle different MCP methods
            if request.method == "initialize":
                result = await self._handle_initialize(request.params)
            elif request.method == "resources/list":
                result = await self._handle_list_resources()
            elif request.method == "resources/read":
                result = await self._handle_read_resource(request.params)
            elif request.method == "tools/list":
                result = await self._handle_list_tools()
            elif request.method == "tools/call":
                result = await self._handle_call_tool(request.params, client_id)
            else:
                raise ValueError(f"Unknown method: {request.method}")
            
            # Return success response
            return MCPResponse(
                id=request.id,
                result=result
            ).model_dump()
            
        except ValidationError as e:
            logger.warning("Invalid request format", 
                          client_id=client_id, error=str(e))
            return MCPError(
                id=data.get("id"),
                error_code=-32602,
                message="Invalid params",
                data=str(e)
            ).model_dump()
            
        except Exception as e:
            logger.error("Error processing request", 
                        client_id=client_id, error=str(e))
            return MCPError(
                id=data.get("id"),
                error_code=-32603,
                message="Internal error",
                data=str(e)
            ).model_dump()
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "resources": {"subscribe": False, "listChanged": False},
                "tools": {},
                "logging": {}
            },
            "serverInfo": {
                "name": "whois-rdap-server",
                "version": "1.0.0"
            }
        }
    
    async def _handle_list_resources(self) -> Dict[str, Any]:
        """Handle MCP resources/list request."""
        return {
            "resources": [r.model_dump() for r in self.resources]
        }
    
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP resources/read request."""
        uri = params.get("uri", "")
        
        if uri.startswith("whois://"):
            # Extract target from URI
            if "/domain/" in uri:
                target = uri.split("/domain/")[-1]
                result = await self.whois_service.lookup_domain(target)
            elif "/ip/" in uri:
                target = uri.split("/ip/")[-1]
                result = await self.whois_service.lookup_ip(target)
            else:
                raise ValueError("Invalid whois URI format")
                
        elif uri.startswith("rdap://"):
            # Extract target from URI
            if "/domain/" in uri:
                target = uri.split("/domain/")[-1]
                result = await self.rdap_service.lookup_domain(target)
            elif "/ip/" in uri:
                target = uri.split("/ip/")[-1]
                result = await self.rdap_service.lookup_ip(target)
            else:
                raise ValueError("Invalid RDAP URI format")
        else:
            raise ValueError("Unsupported resource URI")
        
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(result, indent=2)
            }]
        }
    
    async def _handle_list_tools(self) -> Dict[str, Any]:
        """Handle MCP tools/list request."""
        return {
            "tools": [t.model_dump() for t in self.tools]
        }
    
    async def _handle_call_tool(self, params: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle MCP tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        # Rate limiting check
        if not await self.rate_limiter.acquire(client_id):
            raise ValueError("Rate limit exceeded")
        
        try:
            if tool_name == "whois_lookup":
                result = await self._handle_whois_lookup(arguments)
            elif tool_name == "rdap_lookup":
                result = await self._handle_rdap_lookup(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }
            
        finally:
            await self.rate_limiter.release(client_id)
    
    async def _handle_whois_lookup(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle whois lookup tool call."""
        target = arguments.get("target")
        use_cache = arguments.get("use_cache", True)
        
        if not target:
            raise ValueError("Target parameter is required")
        
        # Check cache first if enabled
        if use_cache:
            cached_result = await self.cache_service.get(f"whois:{target}")
            if cached_result:
                logger.info("Returning cached whois result", target=target)
                return cached_result
        
        # Determine if target is domain or IP
        from utils.validators import is_valid_ip, is_valid_domain
        
        if is_valid_ip(target):
            result = await self.whois_service.lookup_ip(target)
        elif is_valid_domain(target):
            result = await self.whois_service.lookup_domain(target)
        else:
            raise ValueError("Invalid domain name or IP address")
        
        # Cache result if enabled
        if use_cache:
            await self.cache_service.set(f"whois:{target}", result, 
                                       ttl=self.config.cache_ttl)
        
        return result
    
    async def _handle_rdap_lookup(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle RDAP lookup tool call."""
        target = arguments.get("target")
        use_cache = arguments.get("use_cache", True)
        
        if not target:
            raise ValueError("Target parameter is required")
        
        # Check cache first if enabled
        if use_cache:
            cached_result = await self.cache_service.get(f"rdap:{target}")
            if cached_result:
                logger.info("Returning cached RDAP result", target=target)
                return cached_result
        
        # Determine if target is domain or IP
        from utils.validators import is_valid_ip, is_valid_domain
        
        if is_valid_ip(target):
            result = await self.rdap_service.lookup_ip(target)
        elif is_valid_domain(target):
            result = await self.rdap_service.lookup_domain(target)
        else:
            raise ValueError("Invalid domain name or IP address")
        
        # Cache result if enabled
        if use_cache:
            await self.cache_service.set(f"rdap:{target}", result,
                                       ttl=self.config.cache_ttl)
        
        return result
