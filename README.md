# MCP Whois/RDAP Server

A Model Context Protocol (MCP) server that provides domain and IP address lookup services using Whois and RDAP protocols.

## What is MCP?

The Model Context Protocol (MCP) is a specification for connecting AI models with external data sources and tools. MCP servers run locally and communicate with AI clients via stdin/stdout.

## Usage

### Running the MCP Server

The MCP server is designed to be used by MCP-compatible AI clients. To start the server:

```bash
./mcp_server
```

The server will:
- Read JSON-RPC requests from stdin
- Process whois/RDAP lookups
- Write JSON-RPC responses to stdout

### Available Tools

- **whois_lookup**: Perform Whois lookup for domain or IP address
- **rdap_lookup**: Perform RDAP lookup for domain or IP address

### Available Resources

- `whois://domain/{domain}` - Domain Whois information
- `whois://ip/{ip}` - IP Whois information  
- `rdap://domain/{domain}` - Domain RDAP information
- `rdap://ip/{ip}` - IP RDAP information

### Example MCP Client Configuration

```json
{
  "mcpServers": {
    "whois-rdap": {
      "command": "./mcp_server",
      "cwd": "/path/to/whois-rdap-server"
    }
  }
}
```

## Web Interface (Demo)

A web interface is available for demonstration purposes at port 5000. This is NOT the MCP server - it's just a demo showing the functionality.

To start the web interface:

```bash
python main.py
```

## Features

- **Asynchronous Operations**: High-performance async processing
- **Rate Limiting**: Protects external registry servers
- **Caching**: In-memory cache with TTL for performance
- **Multiple Protocols**: Both Whois (TCP) and RDAP (HTTPS)
- **Comprehensive Coverage**: Supports major TLDs and RIRs
- **Error Handling**: Robust error handling and structured logging

## Services

- **WhoisService**: TCP-based lookups to traditional Whois servers
- **RDAPService**: HTTPS-based lookups to modern RDAP endpoints
- **CacheService**: In-memory LRU cache with TTL
- **RateLimiter**: Token bucket rate limiting per client and globally

## Configuration

Configure via environment variables:

- `BIND_HOST`: Host for internal services (default: 0.0.0.0)
- `BIND_PORT`: Port for internal services (default: 5001)
- `WHOIS_TIMEOUT`: Whois query timeout in seconds (default: 30)
- `RDAP_TIMEOUT`: RDAP query timeout in seconds (default: 30)
- `CACHE_TTL`: Cache TTL in seconds (default: 3600)
- `CACHE_MAX_SIZE`: Maximum cache entries (default: 1000)
- `GLOBAL_RATE_LIMIT_PER_SECOND`: Global rate limit (default: 10.0)
- `CLIENT_RATE_LIMIT_PER_SECOND`: Per-client rate limit (default: 2.0)
- `LOG_LEVEL`: Logging level (default: INFO)

## Dependencies

- Python 3.11+
- anyio (async I/O)
- httpx (HTTP client)
- pydantic (data validation)
- structlog (structured logging)
- click (CLI)

## Architecture

The server follows MCP specification:
- JSON-RPC 2.0 protocol over stdio
- Standard MCP methods (initialize, tools/list, tools/call, etc.)
- Proper error handling and response formatting
- Resource-based access patterns