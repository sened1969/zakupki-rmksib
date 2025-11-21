"""Сервисы для работы с поставщиками"""
from services.suppliers.contact_parser import (
	get_supplier_contacts,
	parse_contacts_from_url,
	find_contact_page
)

__all__ = [
	'get_supplier_contacts',
	'parse_contacts_from_url',
	'find_contact_page'
]

