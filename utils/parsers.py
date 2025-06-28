"""
Parsing utilities for Whois and RDAP responses.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import structlog

from models.domain_models import DomainInfo, IPInfo

logger = structlog.get_logger(__name__)


class WhoisParser:
    """Parser for Whois response data."""
    
    # Common Whois field patterns
    DOMAIN_PATTERNS = {
        'domain_name': [
            r'domain name:\s*(.+)',
            r'domain:\s*(.+)',
            r'domain-name:\s*(.+)',
        ],
        'registrar': [
            r'registrar:\s*(.+)',
            r'registrar name:\s*(.+)',
            r'registrar organization:\s*(.+)',
        ],
        'registrant_name': [
            r'registrant name:\s*(.+)',
            r'registrant:\s*(.+)',
            r'owner name:\s*(.+)',
        ],
        'registrant_organization': [
            r'registrant organization:\s*(.+)',
            r'registrant org:\s*(.+)',
            r'owner organization:\s*(.+)',
        ],
        'registrant_email': [
            r'registrant email:\s*(.+)',
            r'owner email:\s*(.+)',
            r'registrant e-mail:\s*(.+)',
        ],
        'admin_contact': [
            r'admin contact:\s*(.+)',
            r'administrative contact:\s*(.+)',
            r'admin name:\s*(.+)',
        ],
        'tech_contact': [
            r'tech contact:\s*(.+)',
            r'technical contact:\s*(.+)',
            r'tech name:\s*(.+)',
        ],
        'creation_date': [
            r'creation date:\s*(.+)',
            r'created:\s*(.+)',
            r'registered:\s*(.+)',
            r'registration date:\s*(.+)',
        ],
        'expiration_date': [
            r'expiration date:\s*(.+)',
            r'expires:\s*(.+)',
            r'expire:\s*(.+)',
            r'registry expiry date:\s*(.+)',
        ],
        'updated_date': [
            r'updated date:\s*(.+)',
            r'last updated:\s*(.+)',
            r'modified:\s*(.+)',
            r'changed:\s*(.+)',
        ],
        'name_servers': [
            r'name server:\s*(.+)',
            r'nserver:\s*(.+)',
            r'nameserver:\s*(.+)',
            r'dns:\s*(.+)',
        ],
        'status': [
            r'status:\s*(.+)',
            r'domain status:\s*(.+)',
            r'state:\s*(.+)',
        ],
        'dnssec': [
            r'dnssec:\s*(.+)',
            r'dnssec status:\s*(.+)',
        ]
    }
    
    IP_PATTERNS = {
        'network_range': [
            r'netrange:\s*(.+)',
            r'inetnum:\s*(.+)',
            r'network:\s*(.+)',
        ],
        'network_name': [
            r'netname:\s*(.+)',
            r'network name:\s*(.+)',
            r'descr:\s*(.+)',
        ],
        'organization': [
            r'organization:\s*(.+)',
            r'org:\s*(.+)',
            r'orgname:\s*(.+)',
            r'owner:\s*(.+)',
        ],
        'country': [
            r'country:\s*(.+)',
            r'country code:\s*(.+)',
        ],
        'admin_contact': [
            r'admin-c:\s*(.+)',
            r'admincontact:\s*(.+)',
        ],
        'tech_contact': [
            r'tech-c:\s*(.+)',
            r'techcontact:\s*(.+)',
        ],
        'abuse_contact': [
            r'abuse-c:\s*(.+)',
            r'abuse contact:\s*(.+)',
        ],
        'registration_date': [
            r'regdate:\s*(.+)',
            r'registration date:\s*(.+)',
            r'created:\s*(.+)',
        ],
        'updated_date': [
            r'updated:\s*(.+)',
            r'last updated:\s*(.+)',
            r'changed:\s*(.+)',
        ]
    }
    
    # Date format patterns
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
        '%d-%b-%Y',
        '%d.%m.%Y',
        '%Y/%m/%d',
        '%m/%d/%Y',
        '%d-%m-%Y',
        '%Y%m%d',
    ]
    
    def parse_domain_whois(self, whois_text: str) -> Dict[str, Any]:
        """Parse domain Whois response."""
        try:
            # Normalize text
            normalized_text = self._normalize_whois_text(whois_text)
            
            # Extract basic fields
            parsed_data = {}
            
            for field, patterns in self.DOMAIN_PATTERNS.items():
                value = self._extract_field(normalized_text, patterns)
                if value:
                    if field in ['creation_date', 'expiration_date', 'updated_date']:
                        parsed_data[field] = self._parse_date(value)
                    elif field == 'name_servers':
                        # Handle multiple name servers
                        if field not in parsed_data:
                            parsed_data[field] = []
                        parsed_data[field].append(value.strip())
                    elif field == 'status':
                        # Handle multiple status values
                        if field not in parsed_data:
                            parsed_data[field] = []
                        parsed_data[field].append(value.strip())
                    else:
                        parsed_data[field] = value.strip()
            
            # Extract all name servers
            ns_list = self._extract_all_matches(normalized_text, self.DOMAIN_PATTERNS['name_servers'])
            if ns_list:
                parsed_data['name_servers'] = [ns.strip() for ns in ns_list]
            
            # Extract all status values
            status_list = self._extract_all_matches(normalized_text, self.DOMAIN_PATTERNS['status'])
            if status_list:
                parsed_data['status'] = [status.strip() for status in status_list]
            
            logger.debug("Domain whois parsing completed", 
                        fields_extracted=len(parsed_data))
            
            return parsed_data
            
        except Exception as e:
            logger.warning("Failed to parse domain whois", error=str(e))
            return {}
    
    def parse_ip_whois(self, whois_text: str) -> Dict[str, Any]:
        """Parse IP Whois response."""
        try:
            # Normalize text
            normalized_text = self._normalize_whois_text(whois_text)
            
            # Extract basic fields
            parsed_data = {}
            
            for field, patterns in self.IP_PATTERNS.items():
                value = self._extract_field(normalized_text, patterns)
                if value:
                    if field in ['registration_date', 'updated_date']:
                        parsed_data[field] = self._parse_date(value)
                    else:
                        parsed_data[field] = value.strip()
            
            logger.debug("IP whois parsing completed", 
                        fields_extracted=len(parsed_data))
            
            return parsed_data
            
        except Exception as e:
            logger.warning("Failed to parse IP whois", error=str(e))
            return {}
    
    def _normalize_whois_text(self, text: str) -> str:
        """Normalize Whois text for parsing."""
        # Convert to lowercase for case-insensitive matching
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Split into lines for line-by-line processing
        lines = text.split('\n')
        
        # Remove comment lines and empty lines
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('%') and not line.startswith('#'):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def _extract_field(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract field value using multiple patterns."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                if value and value not in ['', '-', 'n/a', 'not available']:
                    return value
        return None
    
    def _extract_all_matches(self, text: str, patterns: List[str]) -> List[str]:
        """Extract all matching values for patterns."""
        matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in found:
                value = match.strip()
                if value and value not in ['', '-', 'n/a', 'not available']:
                    matches.append(value)
        return matches
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string into ISO format."""
        if not date_str:
            return None
        
        # Clean up date string
        date_str = date_str.strip()
        
        # Remove timezone info for now (complex to handle all variants)
        date_str = re.sub(r'\s*\([^)]+\)\s*$', '', date_str)
        date_str = re.sub(r'\s*[A-Z]{3,4}\s*$', '', date_str)
        
        # Try different date formats
        for fmt in self.DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # If no format matches, return as-is
        logger.warning("Could not parse date", date_string=date_str)
        return date_str


class RDAPParser:
    """Parser for RDAP response data."""
    
    @staticmethod
    def parse_domain_rdap(rdap_data: Dict[str, Any]) -> DomainInfo:
        """Parse RDAP domain response into DomainInfo."""
        try:
            domain_info = DomainInfo()
            
            # Basic domain information
            if 'ldhName' in rdap_data:
                domain_info.domain_name = rdap_data['ldhName']
            elif 'unicodeName' in rdap_data:
                domain_info.domain_name = rdap_data['unicodeName']
            
            # Status
            if 'status' in rdap_data:
                domain_info.status = rdap_data['status']
            
            # Name servers
            if 'nameservers' in rdap_data:
                ns_list = []
                for ns in rdap_data['nameservers']:
                    if 'ldhName' in ns:
                        ns_list.append(ns['ldhName'])
                domain_info.name_servers = ns_list
            
            # Entities (contacts, registrar)
            if 'entities' in rdap_data:
                RDAPParser._parse_entities(rdap_data['entities'], domain_info)
            
            # Events (dates)
            if 'events' in rdap_data:
                RDAPParser._parse_events(rdap_data['events'], domain_info)
            
            # Secure DNS
            if 'secureDNS' in rdap_data:
                secure_dns = rdap_data['secureDNS']
                if 'delegationSigned' in secure_dns:
                    domain_info.dnssec = 'signed' if secure_dns['delegationSigned'] else 'unsigned'
            
            return domain_info
            
        except Exception as e:
            logger.warning("Failed to parse RDAP domain data", error=str(e))
            return DomainInfo()
    
    @staticmethod
    def parse_ip_rdap(rdap_data: Dict[str, Any]) -> IPInfo:
        """Parse RDAP IP response into IPInfo."""
        try:
            ip_info = IPInfo()
            
            # Network information
            if 'startAddress' in rdap_data and 'endAddress' in rdap_data:
                start = rdap_data['startAddress']
                end = rdap_data['endAddress']
                ip_info.network_range = f"{start} - {end}"
            
            if 'cidr0_cidrs' in rdap_data:
                cidrs = rdap_data['cidr0_cidrs']
                if cidrs:
                    ip_info.network_range = ', '.join([f"{c['v4prefix']}/{c['length']}" for c in cidrs])
            
            if 'name' in rdap_data:
                ip_info.network_name = rdap_data['name']
            
            if 'country' in rdap_data:
                ip_info.country = rdap_data['country']
            
            # Entities (organization, contacts)
            if 'entities' in rdap_data:
                RDAPParser._parse_ip_entities(rdap_data['entities'], ip_info)
            
            # Events (dates)
            if 'events' in rdap_data:
                RDAPParser._parse_ip_events(rdap_data['events'], ip_info)
            
            return ip_info
            
        except Exception as e:
            logger.warning("Failed to parse RDAP IP data", error=str(e))
            return IPInfo()
    
    @staticmethod
    def _parse_entities(entities: List[Dict[str, Any]], domain_info: DomainInfo):
        """Parse RDAP entities for domain information."""
        for entity in entities:
            roles = entity.get('roles', [])
            
            # Extract contact information
            vcard = entity.get('vcardArray')
            if vcard and len(vcard) > 1:
                contact_info = RDAPParser._parse_vcard(vcard[1])
                
                if 'registrar' in roles:
                    domain_info.registrar = contact_info.get('fn', contact_info.get('org'))
                elif 'registrant' in roles:
                    domain_info.registrant_name = contact_info.get('fn')
                    domain_info.registrant_organization = contact_info.get('org')
                    domain_info.registrant_email = contact_info.get('email')
                elif 'administrative' in roles:
                    domain_info.admin_contact = contact_info.get('fn', contact_info.get('email'))
                elif 'technical' in roles:
                    domain_info.tech_contact = contact_info.get('fn', contact_info.get('email'))
    
    @staticmethod
    def _parse_ip_entities(entities: List[Dict[str, Any]], ip_info: IPInfo):
        """Parse RDAP entities for IP information."""
        for entity in entities:
            roles = entity.get('roles', [])
            
            # Extract contact information
            vcard = entity.get('vcardArray')
            if vcard and len(vcard) > 1:
                contact_info = RDAPParser._parse_vcard(vcard[1])
                
                if 'registrant' in roles:
                    ip_info.organization = contact_info.get('fn', contact_info.get('org'))
                elif 'administrative' in roles:
                    ip_info.admin_contact = contact_info.get('fn', contact_info.get('email'))
                elif 'technical' in roles:
                    ip_info.tech_contact = contact_info.get('fn', contact_info.get('email'))
                elif 'abuse' in roles:
                    ip_info.abuse_contact = contact_info.get('email')
    
    @staticmethod
    def _parse_vcard(vcard_data: List[List]) -> Dict[str, str]:
        """Parse vCard data from RDAP response."""
        contact_info = {}
        
        for field in vcard_data:
            if len(field) >= 4:
                field_name = field[0].lower()
                field_value = field[3]
                
                if field_name == 'fn':  # Full name
                    contact_info['fn'] = field_value
                elif field_name == 'org':  # Organization
                    contact_info['org'] = field_value
                elif field_name == 'email':  # Email
                    contact_info['email'] = field_value
        
        return contact_info
    
    @staticmethod
    def _parse_events(events: List[Dict[str, Any]], domain_info: DomainInfo):
        """Parse RDAP events for domain dates."""
        for event in events:
            action = event.get('eventAction')
            date_str = event.get('eventDate')
            
            if action and date_str:
                try:
                    # Parse ISO format date
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    
                    if action == 'registration':
                        domain_info.creation_date = dt
                    elif action == 'expiration':
                        domain_info.expiration_date = dt
                    elif action == 'last changed':
                        domain_info.updated_date = dt
                        
                except ValueError:
                    logger.warning("Failed to parse event date", date=date_str)
    
    @staticmethod
    def _parse_ip_events(events: List[Dict[str, Any]], ip_info: IPInfo):
        """Parse RDAP events for IP dates."""
        for event in events:
            action = event.get('eventAction')
            date_str = event.get('eventDate')
            
            if action and date_str:
                try:
                    # Parse ISO format date
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    
                    if action == 'registration':
                        ip_info.registration_date = dt
                    elif action == 'last changed':
                        ip_info.updated_date = dt
                        
                except ValueError:
                    logger.warning("Failed to parse event date", date=date_str)
