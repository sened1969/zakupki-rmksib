from __future__ import annotations
from email.message import EmailMessage
from typing import Iterable
from loguru import logger
import aiosmtplib
from config.settings import settings


async def send_email(subject: str, body_html: str, recipients: Iterable[str]) -> bool:
	"""Send HTML email to recipients. Returns True on success.
	If SMTP is not configured, logs a warning and returns False.
	"""
	recipients = [r for r in recipients if r]
	if not recipients:
		logger.warning("send_email: no recipients provided")
		return False

	if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASS or not settings.COMPANY_EMAIL:
		logger.warning("SMTP not configured; cannot send email")
		return False

	message = EmailMessage()
	message["From"] = settings.COMPANY_EMAIL
	message["To"] = ", ".join(recipients)
	message["Subject"] = subject
	message.set_content("This message requires an HTML-capable mail client.")
	message.add_alternative(body_html, subtype="html")

	try:
		client = aiosmtplib.SMTP(hostname=settings.SMTP_HOST, port=587, start_tls=True)
		await client.connect()
		await client.starttls()
		await client.login(settings.SMTP_USER, settings.SMTP_PASS)
		await client.send_message(message)
		await client.quit()
		logger.info(f"Email sent to: {recipients}")
		return True
	except Exception as exc:
		logger.exception(f"Failed to send email: {exc}")
		return False






















