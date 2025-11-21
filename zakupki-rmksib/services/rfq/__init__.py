"""RFQ (Request for Quotation) services"""
from services.rfq.generator import (
    generate_rfq_text,
    parse_supplier_info_from_report,
    extract_emails_from_text
)
from services.rfq.web_parser import (
    extract_emails_from_website,
    extract_emails_from_multiple_websites,
    extract_website_urls_from_text,
    extract_emails_from_html
)

__all__ = [
    "generate_rfq_text",
    "parse_supplier_info_from_report",
    "extract_emails_from_text",
    "extract_emails_from_website",
    "extract_emails_from_multiple_websites",
    "extract_website_urls_from_text",
    "extract_emails_from_html"
]

