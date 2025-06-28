"""
Data models for MCP server and domain lookup services.
"""

from .domain_models import WhoisResult, RDAPResult
from .mcp_models import (
    MCPRequest, MCPResponse, MCPError, 
    ResourceDefinition, ToolDefinition,
    WhoisRequest, RDAPRequest
)

__all__ = [
    'WhoisResult', 'RDAPResult',
    'MCPRequest', 'MCPResponse', 'MCPError',
    'ResourceDefinition', 'ToolDefinition', 
    'WhoisRequest', 'RDAPRequest'
]
