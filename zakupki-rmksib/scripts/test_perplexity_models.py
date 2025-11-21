"""Скрипт для проверки доступных моделей Perplexity API"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai.perplexity import ask_perplexity
from config.settings import settings

async def test_model(model_name: str):
    """Тестирует модель Perplexity API"""
    print(f"\n{'='*60}")
    print(f"Тестирование модели: {model_name}")
    print(f"{'='*60}")
    
    messages = [
        {"role": "system", "content": "Ты помощник. Отвечай кратко на русском языке."},
        {"role": "user", "content": "Привет! Ответь одним предложением: что такое Python?"}
    ]
    
    try:
        result = await ask_perplexity(messages, model=model_name, max_tokens=100)
        print(f"[OK] Uspekh! Model '{model_name}' rabotaet.")
        print(f"Otvet: {result[:200]}...")
        return True
    except Exception as e:
        print(f"[ERROR] Oshibka s model'yu '{model_name}': {str(e)}")
        return False

async def main():
    """Проверяет доступные модели Perplexity"""
    print("Проверка доступных моделей Perplexity API")
    print(f"API Key: {settings.PERPLEXITY_API_KEY[:10]}...{settings.PERPLEXITY_API_KEY[-4:] if settings.PERPLEXITY_API_KEY else 'NOT SET'}")
    
    if not settings.PERPLEXITY_API_KEY:
        print("[ERROR] PERPLEXITY_API_KEY ne ustanovlen v .env fayle!")
        return
    
    # Список моделей для проверки
    models_to_test = [
        "sonar",
        "sonar-pro",
        "llama-3.1-sonar-small-32k-online",
        "llama-3.1-sonar-large-32k-online",
    ]
    
    results = {}
    for model in models_to_test:
        results[model] = await test_model(model)
        await asyncio.sleep(1)  # Небольшая задержка между запросами
    
    # Itogi
    print(f"\n{'='*60}")
    print("ITOGI PROVERKI:")
    print(f"{'='*60}")
    for model, success in results.items():
        status = "[OK] RABOTAET" if success else "[ERROR] NE RABOTAET"
        print(f"{model:50} {status}")
    
    # Rekomendatsiya
    working_models = [m for m, s in results.items() if s]
    if working_models:
        print(f"\n[RECOMMENDED] Rekomenduemaya model': {working_models[0]}")
        print(f"Dobav'te v .env: PERPLEXITY_MODEL={working_models[0]}")
    else:
        print("\n[ERROR] Ni odna model' ne rabotaet. Prover'te API klyuch.")

if __name__ == "__main__":
    asyncio.run(main())

