"""Парсер закупок АО 'ПАВЛИК'"""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin
from loguru import logger
import httpx
from bs4 import BeautifulSoup
from config.nomenclature import check_nomenclature_match


class PavlikParser:
    """Парсер закупок с сайта АО 'ПАВЛИК'"""
    
    BASE_URL = "https://www.pavlik-gold.ru/suppliers/"
    ARCHIVE_URL = "https://www.pavlik-gold.ru/suppliers/archive.php"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    def __init__(self):
        self.timeout = 30
    
    async def parse_current_lots(self) -> List[Dict]:
        """
        Парсинг текущих закупок с главной страницы
        
        Returns:
            Список словарей с данными о лотах
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                headers = {"User-Agent": self.USER_AGENT}
                response = await client.get(self.BASE_URL, headers=headers)
                response.raise_for_status()
                
                html = await response.aread()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Ищем таблицу с лотами
                table = soup.select_one('table.table.table-striped.table-bordered')
                if not table:
                    logger.warning("Table not found on Pavlik page")
                    return []
                
                lots = []
                rows = table.find_all('tr')[1:]  # Пропускаем заголовок
                
                for row in rows:
                    try:
                        cells = row.find_all(['th', 'td'])
                        if len(cells) < 4:
                            continue
                        
                        # Извлекаем данные из ячеек
                        lot_number = cells[0].get_text(strip=True)
                        publish_date = cells[1].get_text(strip=True)
                        
                        # Название и ссылка
                        link_cell = cells[2].find('a')
                        lot_name = link_cell.get_text(strip=True) if link_cell else cells[2].get_text(strip=True)
                        lot_url = ""
                        if link_cell and link_cell.get('href'):
                            lot_url = urljoin(self.BASE_URL, link_cell['href'])
                        
                        deadline = cells[3].get_text(strip=True)
                        
                        # Парсим даты
                        try:
                            publish_date_obj = self._parse_date(publish_date)
                            deadline_obj = self._parse_date(deadline)
                        except:
                            publish_date_obj = datetime.utcnow()
                            deadline_obj = datetime.utcnow()
                        
                        lots.append({
                            'platform_name': 'АО "ПАВЛИК"',
                            'lot_number': lot_number,
                            'title': lot_name,
                            'description': f"Закупка: {lot_name}",
                            'budget': 0.0,  # Бюджет не указан на главной странице
                            'deadline': deadline_obj,
                            'status': 'active',
                            'customer': 'АО "ПАВЛИК"',
                            'nomenclature': None,  # Будет определено при фильтрации
                            'url': lot_url,
                            'publish_date': publish_date_obj,
                            'parsed_at': datetime.utcnow()
                        })
                    except Exception as e:
                        logger.error(f"Error parsing row in Pavlik parser: {e}")
                        continue
                
                logger.info(f"Pavlik parser: found {len(lots)} lots")
                return lots
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} while parsing Pavlik: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in Pavlik parser: {e}", exc_info=True)
            return []
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсит дату из строки"""
        # Попытка различных форматов дат
        formats = [
            "%d.%m.%Y",
            "%d.%m.%Y %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        # Если не удалось распарсить, возвращаем текущую дату
        logger.warning(f"Could not parse date: {date_str}")
        return datetime.utcnow()
    
    async def filter_lots(
        self,
        lots: List[Dict],
        nomenclature: Optional[List[str]] = None,
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None
    ) -> List[Dict]:
        """
        Фильтрует лоты по номенклатуре и бюджету
        
        Args:
            lots: Список лотов для фильтрации
            nomenclature: Список выбранных номенклатурных групп
            budget_min: Минимальная сумма бюджета
            budget_max: Максимальная сумма бюджета
        
        Returns:
            Отфильтрованный список лотов
        """
        filtered = []
        
        for lot in lots:
            # Проверка по номенклатуре
            if nomenclature:
                if not check_nomenclature_match(lot.get('title', ''), nomenclature):
                    continue
            
            # Проверка по бюджету
            budget = lot.get('budget', 0)
            if budget_min is not None and budget < budget_min:
                continue
            if budget_max is not None and budget > budget_max:
                continue
            
            filtered.append(lot)
        
        return filtered


async def fetch_new_lots() -> List[Dict]:
    """
    Основная функция для получения новых лотов (интеграция с существующей системой)
    
    Returns:
        Список новых лотов
    """
    parser = PavlikParser()
    lots = await parser.parse_current_lots()
    
    # Фильтрация будет применена в job.py на основе настроек пользователей
    return lots












