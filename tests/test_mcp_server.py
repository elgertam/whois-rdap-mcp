"""
Tests for the MCP server functionality.
"""

import json
from unittest.mock import patch

import pytest

from whoismcp.mcp_server import MCPServer


class TestMCPServer:
    """Test suite for MCPServer."""

    @pytest.fixture
    async def server(self):
        """Create a test MCP server instance."""
        server = MCPServer()
        await server.cache_service.start()
        return server

    @pytest.mark.asyncio
    async def test_initialize(self, server):
        """Test MCP initialize request."""
        params = {"protocolVersion": "2024-11-05", "capabilities": {}}
        result = await server.handle_initialize(params)

        assert result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in result
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "whoismcp"

    @pytest.mark.asyncio
    async def test_list_tools(self, server):
        """Test tools/list request."""
        result = await server.handle_list_tools()

        assert "tools" in result
        tools = result["tools"]
        assert len(tools) == 2

        tool_names = [tool["name"] for tool in tools]
        assert "whois_lookup" in tool_names
        assert "rdap_lookup" in tool_names

    @pytest.mark.asyncio
    async def test_list_resources(self, server):
        """Test resources/list request."""
        result = await server.handle_list_resources()

        assert "resources" in result
        resources = result["resources"]
        assert len(resources) == 4

        uris = [resource["uri"] for resource in resources]
        assert "whois://domain/{domain}" in uris
        assert "whois://ip/{ip}" in uris
        assert "rdap://domain/{domain}" in uris
        assert "rdap://ip/{ip}" in uris

    @pytest.mark.asyncio
    async def test_whois_lookup_missing_target(self, server):
        """Test whois lookup without target argument."""
        arguments = {}
        result = await server._handle_whois_lookup(arguments)

        assert result["isError"] is True
        assert "Missing required argument: target" in result["content"][0][
            "text"]

    @pytest.mark.asyncio
    async def test_whois_lookup_invalid_target(self, server):
        """Test whois lookup with invalid target."""
        arguments = {"target": "invalid-target-format"}

        with patch.object(server.rate_limiter, 'acquire', return_value=True):
            with patch.object(server.cache_service, 'get', return_value=None):
                result = await server._handle_whois_lookup(arguments)

        assert result["isError"] is True
        assert "Invalid target format" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_rdap_lookup_missing_target(self, server):
        """Test RDAP lookup without target argument."""
        arguments = {}
        result = await server._handle_rdap_lookup(arguments)

        assert result["isError"] is True
        assert "Missing required argument: target" in result["content"][0][
            "text"]

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, server):
        """Test rate limit exceeded scenario."""
        arguments = {"target": "example.com"}

        with patch.object(server.rate_limiter, 'acquire', return_value=False):
            result = await server._handle_whois_lookup(arguments)

        assert result["isError"] is True
        assert "Rate limit exceeded" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_cache_hit(self, server):
        """Test cache hit scenario."""
        cached_data = {"target": "example.com", "success": True}
        arguments = {"target": "example.com", "use_cache": True}

        with patch.object(server.rate_limiter, 'acquire', return_value=True):
            with patch.object(server.cache_service,
                              'get',
                              return_value=cached_data):
                result = await server._handle_whois_lookup(arguments)

        assert "content" in result
        content = json.loads(result["content"][0]["text"])
        assert content["target"] == "example.com"
        assert content["success"] is True

    @pytest.mark.asyncio
    async def test_process_request_unknown_method(self, server):
        """Test processing request with unknown method."""
        request = {"jsonrpc": "2.0", "method": "unknown_method", "id": 1}

        result = await server.process_request(request)

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert "error" in result
        assert result["error"]["code"] == -32601
        assert "Method not found" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_process_request_tools_call(self, server):
        """Test processing tools/call request."""
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {}
            },
            "id": 1
        }

        result = await server.process_request(request)

        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert "result" in result
        assert result["result"]["isError"] is True

    def test_write_message(self, server, capsys):
        """Test writing message to stdout."""
        message = {"test": "data"}
        server.write_message(message)

        captured = capsys.readouterr()
        assert '{"test": "data"}' in captured.out

    def test_read_message_valid_json(self, server, monkeypatch):
        """Test reading valid JSON message from stdin."""
        test_input = '{"jsonrpc": "2.0", "method": "test"}\n'

        import io
        monkeypatch.setattr('sys.stdin', io.StringIO(test_input))

        message = server.read_message()
        assert message is not None
        assert message["jsonrpc"] == "2.0"
        assert message["method"] == "test"

    def test_read_message_invalid_json(self, server, monkeypatch):
        """Test reading invalid JSON message from stdin."""
        test_input = 'invalid json\n'

        import io
        monkeypatch.setattr('sys.stdin', io.StringIO(test_input))

        message = server.read_message()
        assert message is None

    def test_read_message_empty(self, server, monkeypatch):
        """Test reading empty input from stdin."""
        test_input = ''

        import io
        monkeypatch.setattr('sys.stdin', io.StringIO(test_input))

        message = server.read_message()
        assert message is None
