"""
Whois service implementation for domain and IP lookups.
Handles asynchronous TCP connections to Whois servers.
"""

import asyncio
import socket
from typing import Dict, Any, Optional
import anyio
import structlog

from models.domain_models import WhoisResult
from utils.validators import is_valid_domain, is_valid_ip
from utils.parsers import WhoisParser
from config import Config

logger = structlog.get_logger(__name__)


class WhoisService:
    """Asynchronous Whois service for domain and IP lookups."""
    
    # Default Whois servers for various TLDs and registries
    WHOIS_SERVERS = {
        # Generic TLDs
        'com': 'whois.verisign-grs.com',
        'net': 'whois.verisign-grs.com', 
        'org': 'whois.pir.org',
        'info': 'whois.afilias.net',
        'biz': 'whois.neulevel.biz',
        'name': 'whois.nic.name',
        'mobi': 'whois.dotmobiregistry.net',
        'asia': 'whois.nic.asia',
        'tel': 'whois.nic.tel',
        'travel': 'whois.nic.travel',
        'pro': 'whois.registrypro.pro',
        'museum': 'whois.museum',
        'coop': 'whois.nic.coop',
        'aero': 'whois.information.aero',
        'cat': 'whois.cat',
        'jobs': 'jobswhois.verisign-grs.com',
        
        # Country code TLDs (selection)
        'uk': 'whois.nic.uk',
        'de': 'whois.denic.de',
        'fr': 'whois.nic.fr',
        'it': 'whois.nic.it',
        'nl': 'whois.domain-registry.nl',
        'be': 'whois.dns.be',
        'au': 'whois.auda.org.au',
        'ca': 'whois.cira.ca',
        'jp': 'whois.jprs.jp',
        'kr': 'whois.kr',
        'cn': 'whois.cnnic.net.cn',
        
        # Regional Internet Registries for IP lookups
        'arin': 'whois.arin.net',
        'ripe': 'whois.ripe.net', 
        'apnic': 'whois.apnic.net',
        'lacnic': 'whois.lacnic.net',
        'afrinic': 'whois.afrinic.net'
    }
    
    # IP range to RIR mapping (simplified)
    IP_REGISTRIES = {
        # ARIN (North America)
        ('3.0.0.0', '3.255.255.255'): 'arin',
        ('4.0.0.0', '4.255.255.255'): 'arin',
        ('8.0.0.0', '8.255.255.255'): 'arin',
        ('54.0.0.0', '54.255.255.255'): 'arin',
        
        # RIPE (Europe, Middle East, Central Asia)
        ('2.0.0.0', '2.255.255.255'): 'ripe',
        ('5.0.0.0', '5.255.255.255'): 'ripe',
        ('31.0.0.0', '31.255.255.255'): 'ripe',
        
        # APNIC (Asia Pacific)
        ('1.0.0.0', '1.255.255.255'): 'apnic',
        ('14.0.0.0', '14.255.255.255'): 'apnic',
        ('27.0.0.0', '27.255.255.255'): 'apnic',
        
        # Default fallback
        'default': 'arin'
    }
    
    def __init__(self, config: Config):
        self.config = config
        self.parser = WhoisParser()
        
    async def lookup_domain(self, domain: str) -> Dict[str, Any]:
        """Perform Whois lookup for a domain name."""
        if not is_valid_domain(domain):
            raise ValueError(f"Invalid domain name: {domain}")
        
        logger.info("Starting domain whois lookup", domain=domain)
        
        whois_server = "unknown"
        try:
            # Get appropriate Whois server
            whois_server = self._get_domain_whois_server(domain)
            
            # Perform Whois query
            raw_response = await self._query_whois_server(whois_server, domain)
            
            # Parse response
            parsed_result = self.parser.parse_domain_whois(raw_response)
            
            result = WhoisResult(
                target=domain,
                target_type="domain",
                whois_server=whois_server,
                raw_response=raw_response,
                parsed_data=parsed_result,
                success=True,
                error=None
            )
            
            logger.info("Domain whois lookup completed successfully", 
                       domain=domain, server=whois_server)
            
            return result.model_dump(mode='json')
            
        except Exception as e:
            logger.error("Domain whois lookup failed", 
                        domain=domain, error=str(e))
            
            return WhoisResult(
                target=domain,
                target_type="domain", 
                whois_server=whois_server,
                raw_response="",
                parsed_data={},
                success=False,
                error=str(e)
            ).model_dump(mode='json')
    
    async def lookup_ip(self, ip_address: str) -> Dict[str, Any]:
        """Perform Whois lookup for an IP address."""
        if not is_valid_ip(ip_address):
            raise ValueError(f"Invalid IP address: {ip_address}")
        
        logger.info("Starting IP whois lookup", ip=ip_address)
        
        whois_server = "unknown"
        try:
            # Get appropriate Whois server for IP
            whois_server = self._get_ip_whois_server(ip_address)
            
            # Perform Whois query
            raw_response = await self._query_whois_server(whois_server, ip_address)
            
            # Parse response
            parsed_result = self.parser.parse_ip_whois(raw_response)
            
            result = WhoisResult(
                target=ip_address,
                target_type="ip",
                whois_server=whois_server,
                raw_response=raw_response,
                parsed_data=parsed_result,
                success=True,
                error=None
            )
            
            logger.info("IP whois lookup completed successfully", 
                       ip=ip_address, server=whois_server)
            
            return result.model_dump(mode='json')
            
        except Exception as e:
            logger.error("IP whois lookup failed", 
                        ip=ip_address, error=str(e))
            
            return WhoisResult(
                target=ip_address,
                target_type="ip",
                whois_server=whois_server,
                raw_response="",
                parsed_data={},
                success=False,
                error=str(e)
            ).model_dump(mode='json')
    
    def _get_domain_whois_server(self, domain: str) -> str:
        """Get the appropriate Whois server for a domain."""
        # Extract TLD
        parts = domain.lower().split('.')
        if len(parts) < 2:
            raise ValueError("Invalid domain format")
        
        tld = parts[-1]
        
        # Handle special cases for UK domains
        if tld == 'uk' and len(parts) >= 3:
            second_level = parts[-2]
            if second_level in ['co', 'org', 'me', 'ltd', 'plc']:
                return self.WHOIS_SERVERS.get('uk', 'whois.nic.uk')
        
        # Get server for TLD
        server = self.WHOIS_SERVERS.get(tld)
        if not server:
            # Try to query IANA for unknown TLDs
            server = f"whois.nic.{tld}"
        
        return server
    
    def _get_ip_whois_server(self, ip_address: str) -> str:
        """Get the appropriate Whois server for an IP address."""
        # Convert IP to integer for range checking
        try:
            ip_int = self._ip_to_int(ip_address)
            
            # Check which registry range the IP falls into
            for (start_ip, end_ip), registry in self.IP_REGISTRIES.items():
                if isinstance(start_ip, str):  # IP range
                    start_int = self._ip_to_int(start_ip)
                    end_int = self._ip_to_int(end_ip)
                    
                    if start_int <= ip_int <= end_int:
                        return self.WHOIS_SERVERS[registry]
            
            # Default fallback
            return self.WHOIS_SERVERS[self.IP_REGISTRIES['default']]
            
        except Exception:
            # If IP parsing fails, use ARIN as default
            return self.WHOIS_SERVERS['arin']
    
    def _ip_to_int(self, ip_address: str) -> int:
        """Convert IP address string to integer."""
        parts = ip_address.split('.')
        if len(parts) != 4:
            raise ValueError("Invalid IPv4 address")
        
        return (int(parts[0]) << 24) + (int(parts[1]) << 16) + \
               (int(parts[2]) << 8) + int(parts[3])
    
    async def _query_whois_server(self, server: str, query: str) -> str:
        """Query a Whois server and return the response."""
        try:
            # Create TCP connection with timeout
            with anyio.move_on_after(self.config.whois_timeout) as cancel_scope:
                stream = await anyio.connect_tcp(server, 43)
                
                async with stream:
                    # Send query
                    query_bytes = f"{query}\r\n".encode('utf-8')
                    await stream.send(query_bytes)
                    
                    # Read response
                    response_parts = []
                    while True:
                        try:
                            data = await stream.receive(4096)
                            if not data:
                                break
                            response_parts.append(data.decode('utf-8', errors='ignore'))
                        except anyio.EndOfStream:
                            break
                    
                    response = ''.join(response_parts)
                    
                    if not response.strip():
                        raise ValueError("Empty response from Whois server")
                    
                    return response
            
            if cancel_scope.cancelled_caught:
                raise TimeoutError(f"Whois query timeout for {server}")
            
            # This should not be reached, but return empty if no response
            return ""
                    
        except OSError as e:
            raise ConnectionError(f"Failed to connect to {server}: {e}")
        except Exception as e:
            raise RuntimeError(f"Whois query failed for {server}: {e}")
