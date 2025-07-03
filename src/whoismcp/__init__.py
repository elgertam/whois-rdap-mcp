"""
WhoisMCP - Model Context Protocol Server for Whois and RDAP lookups.

A high-performance MCP server providing domain and IP address lookup services
using both traditional Whois and modern RDAP protocols.
"""

__version__ = "1.0.0"
__author__ = "Whois MCP Server"
__email__ = "server@example.com"

from .config import Config
from .services import WhoisService, RDAPService, CacheService
from .models import WhoisResult, RDAPResult, DomainInfo, IPInfo

__all__ = [
    "Config",
    "WhoisService",
    "RDAPService",
    "CacheService",
    "WhoisResult",
    "RDAPResult",
    "DomainInfo",
    "IPInfo",
]
