"""
Data models for Model Context Protocol communication.
"""

from typing import Any

from pydantic import BaseModel, Field


class MCPRequest(BaseModel):
    """Model Context Protocol request."""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: str | int = Field(..., description="Request ID")
    method: str = Field(..., description="MCP method name")
    params: dict[str, Any] | None = Field(None, description="Request parameters")


class MCPResponse(BaseModel):
    """Model Context Protocol response."""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: str | int = Field(..., description="Request ID")
    result: dict[str, Any] | None = Field(None, description="Response result")


class MCPError(BaseModel):
    """Model Context Protocol error response."""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: str | int | None = Field(None, description="Request ID")
    error: dict[str, Any] = Field(..., description="Error details")

    def __init__(
        self,
        id: str | int | None = None,
        error_code: int = -32603,
        message: str = "Internal error",
        data: Any | None = None,
        **kwargs,
    ):
        error_dict = {"code": error_code, "message": message}
        if data is not None:
            error_dict["data"] = data

        super().__init__(id=id, error=error_dict, **kwargs)


class ResourceDefinition(BaseModel):
    """MCP resource definition."""

    uri: str = Field(..., description="Resource URI template")
    name: str = Field(..., description="Human-readable resource name")
    description: str = Field(..., description="Resource description")
    mimeType: str = Field(..., description="MIME type of resource content")


class ToolDefinition(BaseModel):
    """MCP tool definition."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: dict[str, Any] = Field(..., description="JSON schema for tool input")


class WhoisRequest(BaseModel):
    """Whois lookup request parameters."""

    target: str = Field(..., description="Domain name or IP address to lookup")
    use_cache: bool = Field(default=True, description="Whether to use cached results")


class RDAPRequest(BaseModel):
    """RDAP lookup request parameters."""

    target: str = Field(..., description="Domain name or IP address to lookup")
    use_cache: bool = Field(default=True, description="Whether to use cached results")
