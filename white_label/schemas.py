from ninja import Schema
from typing import Optional, List


class WhiteLabelUpdateSchema(Schema):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    website_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    custom_css: Optional[str] = None
    email_header: Optional[str] = None
    email_footer: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    features: Optional[dict] = None


class AddDomainSchema(Schema):
    domain: str
    is_primary: bool = False


class WhiteLabelDomainOutSchema(Schema):
    id: str
    domain: str
    is_primary: bool
    status: str
    verified_at: Optional[str] = None
    created_at: str


class WhiteLabelOutSchema(Schema):
    id: str
    company_name: str
    logo_url: str
    favicon_url: str
    support_email: str
    support_phone: str
    website_url: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    custom_css: str
    email_header: str
    email_footer: str
    email_from_name: str
    email_from_address: str
    features: dict
    status: str
    organization_id: str
    domains: List[WhiteLabelDomainOutSchema] = []
    created_at: str
    updated_at: str


class MessageResponseSchema(Schema):
    message: str
    success: bool = True