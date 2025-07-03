"""
Data models for domain and IP lookup results.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class WhoisResult(BaseModel):
    """Result model for Whois lookups."""

    target: str = Field(..., description="Domain name or IP address queried")
    target_type: str = Field(..., description="Type of target: 'domain' or 'ip'")
    whois_server: str = Field(..., description="Whois server used for the query")
    raw_response: str = Field(..., description="Raw Whois response text")
    parsed_data: Dict[str, Any] = Field(
        default_factory=dict, description="Parsed Whois data"
    )
    success: bool = Field(..., description="Whether the lookup was successful")
    error: Optional[str] = Field(None, description="Error message if lookup failed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the lookup"
    )

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class RDAPResult(BaseModel):
    """Result model for RDAP lookups."""

    target: str = Field(..., description="Domain name or IP address queried")
    target_type: str = Field(..., description="Type of target: 'domain' or 'ip'")
    rdap_server: str = Field(..., description="RDAP server used for the query")
    response_data: Dict[str, Any] = Field(
        default_factory=dict, description="RDAP response data"
    )
    success: bool = Field(..., description="Whether the lookup was successful")
    error: Optional[str] = Field(None, description="Error message if lookup failed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the lookup"
    )

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class DomainInfo(BaseModel):
    """Parsed domain information from Whois/RDAP data."""

    domain_name: Optional[str] = None
    registrar: Optional[str] = None
    registrant_name: Optional[str] = None
    registrant_organization: Optional[str] = None
    registrant_email: Optional[str] = None
    admin_contact: Optional[str] = None
    tech_contact: Optional[str] = None
    name_servers: List[str] = Field(default_factory=list)
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    status: List[str] = Field(default_factory=list)
    dnssec: Optional[str] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )


class IPInfo(BaseModel):
    """Parsed IP information from Whois/RDAP data."""

    ip_address: Optional[str] = None
    network_range: Optional[str] = None
    network_name: Optional[str] = None
    organization: Optional[str] = None
    country: Optional[str] = None
    admin_contact: Optional[str] = None
    tech_contact: Optional[str] = None
    abuse_contact: Optional[str] = None
    registration_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat() if v else None}
    )
