"""
Input validation utilities for domain names and IP addresses.
"""

import re
import ipaddress
from typing import Union, Tuple


def is_valid_domain(domain: str) -> bool:
    """Validate domain name format."""
    if not domain or not isinstance(domain, str):
        return False
    
    # Basic length check
    if len(domain) > 253:
        return False
    
    # Remove trailing dot if present
    if domain.endswith('.'):
        domain = domain[:-1]
    
    # Check each label
    labels = domain.split('.')
    if len(labels) < 2:
        return False
    
    for label in labels:
        if not label or len(label) > 63:
            return False
        
        # Label can contain letters, digits, and hyphens
        # Cannot start or end with hyphen
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', label):
            return False
    
    # TLD should contain at least one letter
    tld = labels[-1]
    if not re.search(r'[a-zA-Z]', tld):
        return False
    
    return True


def is_valid_ip(ip_address: str) -> bool:
    """Validate IP address format (IPv4 or IPv6)."""
    if not ip_address or not isinstance(ip_address, str):
        return False
    
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def is_valid_ipv4(ip_address: str) -> bool:
    """Validate IPv4 address format."""
    if not ip_address or not isinstance(ip_address, str):
        return False
    
    try:
        ipaddress.IPv4Address(ip_address)
        return True
    except ValueError:
        return False


def is_valid_ipv6(ip_address: str) -> bool:
    """Validate IPv6 address format."""
    if not ip_address or not isinstance(ip_address, str):
        return False
    
    try:
        ipaddress.IPv6Address(ip_address)
        return True
    except ValueError:
        return False


def validate_domain(domain: str) -> Tuple[bool, str]:
    """Validate domain and return normalized version."""
    if not is_valid_domain(domain):
        return False, "Invalid domain name format"
    
    # Normalize domain name
    normalized = domain.lower().strip()
    if normalized.endswith('.'):
        normalized = normalized[:-1]
    
    return True, normalized


def validate_ip(ip_address: str) -> Tuple[bool, str]:
    """Validate IP address and return normalized version."""
    if not is_valid_ip(ip_address):
        return False, "Invalid IP address format"
    
    try:
        # Normalize IP address
        ip_obj = ipaddress.ip_address(ip_address)
        return True, str(ip_obj)
    except ValueError as e:
        return False, str(e)


def extract_domain_from_email(email: str) -> str:
    """Extract domain from email address."""
    if '@' in email:
        return email.split('@')[-1].lower()
    return ""


def get_domain_tld(domain: str) -> str:
    """Extract top-level domain from domain name."""
    if not is_valid_domain(domain):
        return ""
    
    parts = domain.lower().split('.')
    return parts[-1] if parts else ""


def get_domain_sld(domain: str) -> str:
    """Extract second-level domain from domain name."""
    if not is_valid_domain(domain):
        return ""
    
    parts = domain.lower().split('.')
    return parts[-2] if len(parts) >= 2 else ""


def is_private_ip(ip_address: str) -> bool:
    """Check if IP address is in private range."""
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        return ip_obj.is_private
    except ValueError:
        return False


def is_reserved_ip(ip_address: str) -> bool:
    """Check if IP address is reserved."""
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        return ip_obj.is_reserved
    except ValueError:
        return False
