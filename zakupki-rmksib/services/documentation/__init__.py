"""Модуль для работы с конкурсной документацией"""
from .processor import (
	save_documentation_file,
	extract_text_from_file,
	is_supported_format,
	download_documentation_from_url,
	SUPPORTED_EXTENSIONS
)

__all__ = [
	'save_documentation_file',
	'extract_text_from_file',
	'is_supported_format',
	'download_documentation_from_url',
	'SUPPORTED_EXTENSIONS'
]



