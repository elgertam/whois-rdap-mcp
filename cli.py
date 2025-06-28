#!/usr/bin/env python3
"""
Command-line interface for testing the MCP Whois/RDAP server.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import click
import structlog
from services.whois_service import WhoisService
from services.rdap_service import RDAPService
from config import Config

# Configure basic logging for CLI
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """MCP Whois/RDAP server CLI tool."""
    if verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )


@cli.command()
@click.argument('target')
@click.option('--output', '-o', type=click.Choice(['json', 'text']), default='json',
              help='Output format')
@click.option('--raw', is_flag=True, help='Show raw Whois response')
def whois(target, output, raw):
    """Perform Whois lookup for domain or IP address."""
    async def run_whois():
        config = Config()
        service = WhoisService(config)
        
        try:
            from utils.validators import is_valid_ip, is_valid_domain
            
            if is_valid_ip(target):
                result = await service.lookup_ip(target)
            elif is_valid_domain(target):
                result = await service.lookup_domain(target)
            else:
                click.echo(f"Error: Invalid domain name or IP address: {target}", err=True)
                return
            
            if output == 'json':
                click.echo(json.dumps(result, indent=2))
            else:
                # Text output
                click.echo(f"Target: {result['target']}")
                click.echo(f"Type: {result['target_type']}")
                click.echo(f"Server: {result['whois_server']}")
                click.echo(f"Success: {result['success']}")
                
                if result['success']:
                    if raw:
                        click.echo("\nRaw Response:")
                        click.echo("-" * 50)
                        click.echo(result['raw_response'])
                    else:
                        click.echo("\nParsed Data:")
                        click.echo("-" * 50)
                        for key, value in result['parsed_data'].items():
                            if isinstance(value, list):
                                click.echo(f"{key}: {', '.join(value)}")
                            else:
                                click.echo(f"{key}: {value}")
                else:
                    click.echo(f"Error: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            if output == 'json':
                error_result = {
                    'target': target,
                    'success': False,
                    'error': str(e)
                }
                click.echo(json.dumps(error_result, indent=2))
    
    asyncio.run(run_whois())


@cli.command()
@click.argument('target')
@click.option('--output', '-o', type=click.Choice(['json', 'text']), default='json',
              help='Output format')
def rdap(target, output):
    """Perform RDAP lookup for domain or IP address."""
    async def run_rdap():
        config = Config()
        service = RDAPService(config)
        
        try:
            from utils.validators import is_valid_ip, is_valid_domain
            
            if is_valid_ip(target):
                result = await service.lookup_ip(target)
            elif is_valid_domain(target):
                result = await service.lookup_domain(target)
            else:
                click.echo(f"Error: Invalid domain name or IP address: {target}", err=True)
                return
            
            if output == 'json':
                click.echo(json.dumps(result, indent=2))
            else:
                # Text output
                click.echo(f"Target: {result['target']}")
                click.echo(f"Type: {result['target_type']}")
                click.echo(f"Server: {result['rdap_server']}")
                click.echo(f"Success: {result['success']}")
                
                if result['success']:
                    click.echo("\nRDAP Response:")
                    click.echo("-" * 50)
                    click.echo(json.dumps(result['response_data'], indent=2))
                else:
                    click.echo(f"Error: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            if output == 'json':
                error_result = {
                    'target': target,
                    'success': False,
                    'error': str(e)
                }
                click.echo(json.dumps(error_result, indent=2))
        finally:
            await service.close()
    
    asyncio.run(run_rdap())


@cli.command()
@click.option('--host', default='localhost', help='MCP server host')
@click.option('--port', default=8000, help='MCP server port')
def test_server(host, port):
    """Test MCP server connectivity."""
    async def run_test():
        import anyio
        
        try:
            # Test basic connectivity
            click.echo(f"Connecting to MCP server at {host}:{port}...")
            
            stream = await anyio.connect_tcp(host, port)
            
            async with stream:
                # Send initialize request
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "mcp-whois-test-client",
                            "version": "1.0.0"
                        }
                    }
                }
                
                message = json.dumps(init_request) + '\n'
                await stream.send(message.encode('utf-8'))
                
                # Read response
                response_data = await stream.receive(4096)
                response = json.loads(response_data.decode('utf-8'))
                
                click.echo("✓ Server responded successfully")
                click.echo(f"Server info: {response.get('result', {}).get('serverInfo', {})}")
                
                # Test tools/list
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                message = json.dumps(tools_request) + '\n'
                await stream.send(message.encode('utf-8'))
                
                response_data = await stream.receive(4096)
                response = json.loads(response_data.decode('utf-8'))
                
                tools = response.get('result', {}).get('tools', [])
                click.echo(f"✓ Available tools: {len(tools)}")
                for tool in tools:
                    click.echo(f"  - {tool['name']}: {tool['description']}")
                
        except Exception as e:
            click.echo(f"✗ Connection failed: {e}", err=True)
    
    asyncio.run(run_test())


@cli.command()
@click.option('--target', required=True, help='Domain or IP to lookup')
@click.option('--method', type=click.Choice(['whois', 'rdap']), required=True,
              help='Lookup method')
@click.option('--host', default='localhost', help='MCP server host')
@click.option('--port', default=8000, help='MCP server port')
def test_lookup(target, method, host, port):
    """Test lookup via MCP server."""
    async def run_lookup():
        import anyio
        
        try:
            click.echo(f"Testing {method} lookup for {target} via MCP server...")
            
            stream = await anyio.connect_tcp(host, port)
            
            async with stream:
                # Initialize connection
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "mcp-whois-test-client",
                            "version": "1.0.0"
                        }
                    }
                }
                
                message = json.dumps(init_request) + '\n'
                await stream.send(message.encode('utf-8'))
                await stream.receive(4096)  # Read init response
                
                # Call tool
                tool_name = f"{method}_lookup"
                lookup_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": {
                            "target": target,
                            "use_cache": False
                        }
                    }
                }
                
                message = json.dumps(lookup_request) + '\n'
                await stream.send(message.encode('utf-8'))
                
                response_data = await stream.receive(8192)
                response = json.loads(response_data.decode('utf-8'))
                
                if 'result' in response:
                    click.echo("✓ Lookup successful")
                    content = response['result']['content'][0]['text']
                    result = json.loads(content)
                    click.echo(json.dumps(result, indent=2))
                else:
                    click.echo("✗ Lookup failed")
                    click.echo(json.dumps(response, indent=2))
                
        except Exception as e:
            click.echo(f"✗ Lookup failed: {e}", err=True)
    
    asyncio.run(run_lookup())


@cli.command()
def config_show():
    """Show current configuration."""
    config = Config()
    click.echo("Current Configuration:")
    click.echo("=" * 50)
    
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        click.echo(f"{key}: {value}")


if __name__ == '__main__':
    cli()
