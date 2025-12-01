"""
АВТОМАТИЧЕСКИЙ ТЕСТИРОВЩИК ДЛЯ ЭКСПЕРИМЕНТОВ С НЕЙРО-СОТРУДНИКОМ

Этот скрипт автоматически запускает серию экспериментов с различными параметрами
и сохраняет результаты в структурированном виде для анализа.

Использование:
    python experiment_runner.py --api-key YOUR_API_KEY
    python experiment_runner.py --api-key YOUR_API_KEY --experiments 1,2,3
    python experiment_runner.py --api-key YOUR_API_KEY --output results.json
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Исправление кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Добавляем путь к модулю ноутбука
sys.path.insert(0, str(Path(__file__).parent.parent / "Ноутбук"))

try:
    from neuro_employee_colab_final import (
        ask_perplexity,
        analyze_lot_basic,
        analyze_lot_enhanced,
        search_suppliers
    )
except ImportError:
    print("Ошибка: Не удалось импортировать функции из neuro_employee_colab_final.py")
    print("Убедитесь, что файл находится в правильной директории.")
    sys.exit(1)


# Тестовые данные для экспериментов
TEST_LOT_DATA = {
    "lot_number": "123456789",
    "platform_name": "ПАВЛИК",
    "title": "Поставка метизов для промышленного производства",
    "budget": 2500000,
    "deadline": "2025-12-15",
    "customer": "ООО 'Промышленное предприятие'",
    "nomenclature": ["Метизы", "Крепеж"],
    "description": "Поставка метизов различных типов: болты, гайки, шайбы, шпильки. Требования: ГОСТ, оцинковка. Срок поставки: 30 дней."
}

TEST_PRODUCT = "Метизы оцинкованные"


class ExperimentRunner:
    """Класс для запуска экспериментов"""
    
    def __init__(self, api_key: str, output_file: str = "experiments_results.json"):
        self.api_key = api_key
        self.output_file = output_file
        self.results = []
    
    async def run_experiment(self, experiment_id: int, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Запуск одного эксперимента"""
        print(f"\n{'='*60}")
        print(f"ЭКСПЕРИМЕНТ №{experiment_id}: {experiment_config['name']}")
        print(f"{'='*60}")
        
        start_time = datetime.now()
        
        try:
            if experiment_config['type'] == 'basic_analysis':
                result = await analyze_lot_basic(
                    TEST_LOT_DATA,
                    self.api_key,
                    model=experiment_config.get('model', 'sonar'),
                    budget_threshold=experiment_config.get('budget_threshold', 3000000),
                    overhead_percent=experiment_config.get('overhead_percent', 15.0)
                )
            elif experiment_config['type'] == 'enhanced_analysis':
                result = await analyze_lot_enhanced(
                    TEST_LOT_DATA,
                    self.api_key,
                    model=experiment_config.get('model', 'sonar'),
                    budget_threshold=experiment_config.get('budget_threshold', 3000000),
                    overhead_percent=experiment_config.get('overhead_percent', 15.0)
                )
            elif experiment_config['type'] == 'supplier_search':
                result = await search_suppliers(
                    TEST_PRODUCT,
                    self.api_key,
                    model=experiment_config.get('model', 'sonar'),
                    max_suppliers=experiment_config.get('max_suppliers', 5)
                )
            else:
                raise ValueError(f"Неизвестный тип эксперимента: {experiment_config['type']}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            experiment_result = {
                "experiment_id": experiment_id,
                "name": experiment_config['name'],
                "type": experiment_config['type'],
                "parameters": {
                    "model": experiment_config.get('model', 'sonar'),
                    "temperature": experiment_config.get('temperature', 0.2),
                    "max_tokens": experiment_config.get('max_tokens', 2000),
                    **{k: v for k, v in experiment_config.items() if k not in ['name', 'type', 'model', 'temperature', 'max_tokens']}
                },
                "prompt": experiment_config.get('prompt', ''),
                "result": result,
                "duration_seconds": duration,
                "timestamp": start_time.isoformat(),
                "status": "success"
            }
            
            print(f"[OK] Эксперимент завершен за {duration:.2f} секунд")
            print(f"Длина результата: {len(result)} символов")
            
            return experiment_result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            experiment_result = {
                "experiment_id": experiment_id,
                "name": experiment_config['name'],
                "type": experiment_config['type'],
                "parameters": experiment_config,
                "result": None,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": start_time.isoformat(),
                "status": "error"
            }
            
            print(f"[ERROR] Ошибка в эксперименте: {e}")
            return experiment_result
    
    async def run_all_experiments(self, experiment_ids: List[int] = None):
        """Запуск всех экспериментов"""
        experiments = self.get_experiments_config()
        
        if experiment_ids:
            experiments = {k: v for k, v in experiments.items() if k in experiment_ids}
        
        print(f"\n{'='*60}")
        print(f"ЗАПУСК ЭКСПЕРИМЕНТОВ")
        print(f"{'='*60}")
        print(f"Всего экспериментов: {len(experiments)}")
        print(f"API ключ: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else '***'}")
        
        for exp_id, exp_config in sorted(experiments.items()):
            result = await self.run_experiment(exp_id, exp_config)
            self.results.append(result)
            
            # Небольшая задержка между экспериментами
            await asyncio.sleep(2)
        
        # Сохранение результатов
        self.save_results()
    
    def get_experiments_config(self) -> Dict[int, Dict[str, Any]]:
        """Конфигурация всех экспериментов"""
        return {
            1: {
                "name": "Базовый промпт для анализа лота",
                "type": "basic_analysis",
                "model": "sonar",
                "temperature": 0.2,
                "max_tokens": 1500,
                "budget_threshold": 3000000,
                "overhead_percent": 15.0,
                "prompt": "Базовый промпт без оценок, простой анализ"
            },
            2: {
                "name": "Расширенный промпт с оценками",
                "type": "enhanced_analysis",
                "model": "sonar",
                "temperature": 0.2,
                "max_tokens": 2000,
                "budget_threshold": 3000000,
                "overhead_percent": 15.0,
                "prompt": "Расширенный промпт с 10-балльной шкалой оценок"
            },
            3: {
                "name": "Базовый анализ с temperature=0.1",
                "type": "basic_analysis",
                "model": "sonar",
                "temperature": 0.1,
                "max_tokens": 1500,
                "budget_threshold": 3000000,
                "overhead_percent": 15.0,
                "prompt": "Базовый анализ с низкой temperature для более детерминированных ответов"
            },
            4: {
                "name": "Базовый анализ с temperature=0.5",
                "type": "basic_analysis",
                "model": "sonar",
                "temperature": 0.5,
                "max_tokens": 1500,
                "budget_threshold": 3000000,
                "overhead_percent": 15.0,
                "prompt": "Базовый анализ с повышенной temperature для более творческих ответов"
            },
            5: {
                "name": "Расширенный анализ с temperature=0.1",
                "type": "enhanced_analysis",
                "model": "sonar",
                "temperature": 0.1,
                "max_tokens": 2000,
                "budget_threshold": 3000000,
                "overhead_percent": 15.0,
                "prompt": "Расширенный анализ с низкой temperature"
            },
            6: {
                "name": "Расширенный анализ с temperature=0.7",
                "type": "enhanced_analysis",
                "model": "sonar",
                "temperature": 0.7,
                "max_tokens": 2000,
                "budget_threshold": 3000000,
                "overhead_percent": 15.0,
                "prompt": "Расширенный анализ с высокой temperature"
            },
            7: {
                "name": "Поиск поставщиков (5 компаний)",
                "type": "supplier_search",
                "model": "sonar",
                "temperature": 0.2,
                "max_tokens": 2000,
                "max_suppliers": 5,
                "prompt": "Поиск 5 российских поставщиков"
            },
            8: {
                "name": "Поиск поставщиков (10 компаний)",
                "type": "supplier_search",
                "model": "sonar",
                "temperature": 0.2,
                "max_tokens": 2000,
                "max_suppliers": 10,
                "prompt": "Поиск 10 российских поставщиков"
            },
            9: {
                "name": "Расширенный анализ с sonar-pro",
                "type": "enhanced_analysis",
                "model": "sonar-pro",
                "temperature": 0.2,
                "max_tokens": 2000,
                "budget_threshold": 3000000,
                "overhead_percent": 15.0,
                "prompt": "Расширенный анализ с использованием модели sonar-pro"
            },
            10: {
                "name": "Базовый анализ с увеличенным max_tokens",
                "type": "basic_analysis",
                "model": "sonar",
                "temperature": 0.2,
                "max_tokens": 3000,
                "budget_threshold": 3000000,
                "overhead_percent": 15.0,
                "prompt": "Базовый анализ с увеличенным лимитом токенов для более подробных ответов"
            }
        }
    
    def save_results(self):
        """Сохранение результатов в файл"""
        output_data = {
            "metadata": {
                "total_experiments": len(self.results),
                "successful": len([r for r in self.results if r['status'] == 'success']),
                "failed": len([r for r in self.results if r['status'] == 'error']),
                "timestamp": datetime.now().isoformat(),
                "test_lot_data": TEST_LOT_DATA,
                "test_product": TEST_PRODUCT
            },
            "experiments": self.results
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"РЕЗУЛЬТАТЫ СОХРАНЕНЫ")
        print(f"{'='*60}")
        print(f"Файл: {self.output_file}")
        print(f"Всего экспериментов: {output_data['metadata']['total_experiments']}")
        print(f"Успешных: {output_data['metadata']['successful']}")
        print(f"Ошибок: {output_data['metadata']['failed']}")
    
    def print_summary(self):
        """Вывод краткой сводки результатов"""
        print(f"\n{'='*60}")
        print(f"СВОДКА РЕЗУЛЬТАТОВ")
        print(f"{'='*60}")
        
        for result in self.results:
            status_icon = "[OK]" if result['status'] == 'success' else "[ERROR]"
            print(f"{status_icon} Эксперимент №{result['experiment_id']}: {result['name']}")
            if result['status'] == 'success':
                print(f"   Длительность: {result['duration_seconds']:.2f} сек")
                print(f"   Длина результата: {len(result['result'])} символов")
            else:
                print(f"   Ошибка: {result.get('error', 'Неизвестная ошибка')}")


async def main():
    parser = argparse.ArgumentParser(description='Автоматический тестировщик для экспериментов с нейро-сотрудником')
    parser.add_argument('--api-key', type=str, required=True, help='Perplexity API ключ')
    parser.add_argument('--experiments', type=str, help='Список номеров экспериментов через запятую (например: 1,2,3)')
    parser.add_argument('--output', type=str, default='experiments_results.json', help='Файл для сохранения результатов')
    
    args = parser.parse_args()
    
    # Парсинг списка экспериментов
    experiment_ids = None
    if args.experiments:
        try:
            experiment_ids = [int(x.strip()) for x in args.experiments.split(',')]
        except ValueError:
            print("Ошибка: Неверный формат списка экспериментов. Используйте формат: 1,2,3")
            sys.exit(1)
    
    # Создание и запуск тестировщика
    runner = ExperimentRunner(args.api_key, args.output)
    await runner.run_all_experiments(experiment_ids)
    runner.print_summary()


if __name__ == "__main__":
    asyncio.run(main())

