#!/usr/bin/env python3
"""
Model Context Protocol Server for Whois and RDAP lookups.
Entry point for the MCP server application.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import MCPServer
from config import Config
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


async def main():
    """Main entry point for the MCP server."""
    try:
        # Initialize configuration
        config = Config()
        
        # Create and start MCP server
        server = MCPServer(config)
        
        logger.info("Starting MCP server for Whois/RDAP lookups", 
                   version="1.0.0",
                   bind_host=config.bind_host,
                   bind_port=config.bind_port)
        
        await server.start()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully")
    except Exception as e:
        logger.error("Fatal error in main", error=str(e), exc_info=True)
        raise
    finally:
        logger.info("MCP server shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        sys.exit(1)
