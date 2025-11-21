"""Sniper Search API integration"""
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class SniperSearchService:
    """Service for Sniper Search API integration"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.base_url = settings.SNIPER_SEARCH_BASE_URL
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_suppliers(
        self,
        product_name: str,
        quantity: Optional[int] = 1,
        uom: Optional[str] = "шт"
    ) -> Dict[str, Any]:
        """
        Search for suppliers using Sniper Search API
        
        Args:
            product_name: Product name to search
            quantity: Product quantity
            uom: Unit of measurement
            
        Returns:
            Dictionary with task_id and status
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        payload = {
            "name": f"Поиск: {product_name}",
            "search_engine": {
                "yandex": True,
                "google": True,
                "bing": True,
                "baidu": False
            },
            "geo_targets": [225],  # Russia
            "languages": [1],  # Russian
            "parse_ads": True,
            "supplier_types": {
                "manufacturing": True,
                "wholesale": True,
                "trading": True,
                "service": True
            },
            "query_list": [
                {
                    "search_query": f"{product_name} купить оптом",
                    "pages_count": 3
                }
            ],
            "search_goods": [
                {
                    "name": product_name,
                    "quantity": quantity,
                    "uom": uom
                }
            ],
            "dry_run": False
        }
        
        try:
            # Устанавливаем таймаут для запроса (10 секунд)
            timeout = aiohttp.ClientTimeout(total=10)
            async with self.session.post(
                f"{self.base_url}/api/v0/requests/wizard",
                json=payload,
                timeout=timeout
            ) as response:
                if response.status == 202:
                    result = await response.json()
                    logger.info(f"Sniper Search task created: {result.get('task_id')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Sniper Search API error: {response.status} - {error_text}")
                    # Формируем более информативное сообщение об ошибке
                    if response.status == 401:
                        raise Exception(f"API error: 401 Unauthorized - Проверьте SNIPER_SEARCH_API_TOKEN в .env")
                    elif response.status == 403:
                        raise Exception(f"API error: 403 Forbidden - Недостаточно прав доступа или превышен лимит")
                    elif response.status == 404:
                        raise Exception(f"API error: 404 Not Found - Проверьте SNIPER_SEARCH_BASE_URL в .env")
                    else:
                        raise Exception(f"API error: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Sniper Search request failed: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of search task"""
        if not self.session:
            raise RuntimeError("Session not initialized.")
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with self.session.get(
                f"{self.base_url}/api/v0/requests",
                params={"query": task_id},
                timeout=timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get task status: {response.status}")
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            raise
    
    async def get_replies(self, task_id: str, offset: int = 0, entry: int = 20) -> Dict[str, Any]:
        """Get supplier replies for a task"""
        if not self.session:
            raise RuntimeError("Session not initialized.")
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with self.session.get(
                f"{self.base_url}/api/v0/mailbox/replies",
                params={
                    "task_id": task_id,
                    "offset": offset,
                    "entry": entry,
                    "ai_price": True
                },
                timeout=timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get replies: {response.status}")
        except Exception as e:
            logger.error(f"Failed to get replies: {e}")
            raise
