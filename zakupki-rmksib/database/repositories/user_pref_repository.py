from __future__ import annotations
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import UserPreference


class UserPreferenceRepository:
	def __init__(self, session: AsyncSession):
		self.session = session

	async def get_by_user_id(self, user_id: int) -> Optional[UserPreference]:
		res = await self.session.execute(select(UserPreference).where(UserPreference.user_id == user_id))
		return res.scalar_one_or_none()

	async def get_or_create(self, user_id: int) -> UserPreference:
		pref = await self.get_by_user_id(user_id)
		if pref is None:
			pref = UserPreference(user_id=user_id, notify_enabled=True, customers=None, nomenclature=None)
			self.session.add(pref)
			await self.session.commit()
			await self.session.refresh(pref)
		return pref

	async def update_lists(self, pref: UserPreference, customers: Optional[List[str]] = None, nomenclature: Optional[List[str]] = None) -> UserPreference:
		if customers is not None:
			pref.customers = customers
		if nomenclature is not None:
			pref.nomenclature = nomenclature
		self.session.add(pref)
		await self.session.commit()
		await self.session.refresh(pref)
		return pref

	async def set_notify(self, pref: UserPreference, enabled: bool) -> UserPreference:
		pref.notify_enabled = enabled
		self.session.add(pref)
		await self.session.commit()
		await self.session.refresh(pref)
		return pref
	
	async def update_email_settings(
		self,
		pref: UserPreference,
		email_password: Optional[str] = None,
		smtp_provider: Optional[str] = None
	) -> UserPreference:
		"""Обновить настройки email"""
		if email_password is not None:
			pref.email_password = email_password
		if smtp_provider is not None:
			pref.smtp_provider = smtp_provider
		self.session.add(pref)
		await self.session.commit()
		await self.session.refresh(pref)
		return pref
	
	async def update_budget(
		self,
		pref: UserPreference,
		budget_min: Optional[int] = None,
		budget_max: Optional[int] = None
	) -> UserPreference:
		"""Обновить настройки бюджета"""
		if budget_min is not None:
			pref.budget_min = budget_min
		if budget_max is not None:
			pref.budget_max = budget_max
		self.session.add(pref)
		await self.session.commit()
		await self.session.refresh(pref)
		return pref







