# Deployment Configuration Guide

## Required Port Configuration

For successful deployment, the following port configuration is needed in `.replit`:

```toml
[[ports]]
localPort = 5000
externalPort = 80
```

This maps the internal web server port (5000) to the external deployment port (80).

## Health Check Endpoints

The application now provides the following endpoints for deployment health checks:

- `GET /` - Main web interface (returns 200 OK)
- `GET /health` - Health check endpoint (returns JSON status)

Both endpoints respond with HTTP 200 status codes when the service is healthy.

## Deployment Checklist

- [x] Web server binds to `0.0.0.0:5000` for external access
- [x] Health check endpoint at `/health` implemented
- [x] Root endpoint at `/` serves proper HTTP responses
- [ ] Port forwarding configured to map port 5000 to port 80 (requires .replit modification)

## Service Status

- MCP Server: Running on port 5001 (internal)
- Web Interface: Running on port 5000 (exposed for deployment)
- Health Check: Available at `/health`
- Protocol: JSON-RPC 2.0 over TCP

## Current Configuration

The startup process:
1. MCP server starts on port 5001
2. Web interface starts on port 5000
3. Both services run in parallel
4. Web interface can communicate with MCP server for functionality tests