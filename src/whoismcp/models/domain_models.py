"""
Data models for domain and IP lookup results.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WhoisResult(BaseModel):
    """Result model for Whois lookups."""

    target: str = Field(..., description="Domain name or IP address queried")
    target_type: str = Field(..., description="Type of target: 'domain' or 'ip'")
    whois_server: str = Field(..., description="Whois server used for the query")
    raw_response: str = Field(..., description="Raw Whois response text")
    parsed_data: dict[str, Any] = Field(
        default_factory=dict, description="Parsed Whois data"
    )
    success: bool = Field(..., description="Whether the lookup was successful")
    error: str | None = Field(None, description="Error message if lookup failed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the lookup"
    )

    model_config = ConfigDict()


class RDAPResult(BaseModel):
    """Result model for RDAP lookups."""

    target: str = Field(..., description="Domain name or IP address queried")
    target_type: str = Field(..., description="Type of target: 'domain' or 'ip'")
    rdap_server: str = Field(..., description="RDAP server used for the query")
    response_data: dict[str, Any] = Field(
        default_factory=dict, description="RDAP response data"
    )
    success: bool = Field(..., description="Whether the lookup was successful")
    error: str | None = Field(None, description="Error message if lookup failed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the lookup"
    )

    model_config = ConfigDict()


class DomainInfo(BaseModel):
    """Parsed domain information from Whois/RDAP data."""

    domain_name: str | None = None
    registrar: str | None = None
    registrant_name: str | None = None
    registrant_organization: str | None = None
    registrant_email: str | None = None
    admin_contact: str | None = None
    tech_contact: str | None = None
    name_servers: list[str] = Field(default_factory=list)
    creation_date: datetime | None = None
    expiration_date: datetime | None = None
    updated_date: datetime | None = None
    status: list[str] = Field(default_factory=list)
    dnssec: str | None = None

    model_config = ConfigDict()


class IPInfo(BaseModel):
    """Parsed IP information from Whois/RDAP data."""

    ip_address: str | None = None
    network_range: str | None = None
    network_name: str | None = None
    organization: str | None = None
    country: str | None = None
    admin_contact: str | None = None
    tech_contact: str | None = None
    abuse_contact: str | None = None
    registration_date: datetime | None = None
    updated_date: datetime | None = None

    model_config = ConfigDict()
