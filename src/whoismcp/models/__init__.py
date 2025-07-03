"""
Data models for the WhoisMCP package.
"""

from .domain_models import DomainInfo, IPInfo, RDAPResult, WhoisResult

__all__ = ["WhoisResult", "RDAPResult", "DomainInfo", "IPInfo"]
