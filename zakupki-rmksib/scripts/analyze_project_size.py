#!/usr/bin/env python3
"""Анализ размера файлов проекта"""
import os
from collections import defaultdict
from pathlib import Path

def get_size(path):
    """Получить размер файла или директории"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        total = 0
        try:
            for entry in os.scandir(path):
                total += get_size(entry.path)
        except PermissionError:
            pass
        return total
    return 0

def format_size(size_bytes):
    """Форматировать размер в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def analyze_project():
    """Анализ размера проекта"""
    project_root = Path('.')
    
    # Исключаемые директории
    exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'env', 'node_modules', 
                   '.pytest_cache', '.mypy_cache', '.idea', '.vscode', 'dist', 'build'}
    
    # Исключаемые расширения
    exclude_exts = {'.pyc', '.pyo', '.pyd', '.egg-info'}
    
    # Категории файлов
    categories = defaultdict(int)
    file_types = defaultdict(int)
    dir_sizes = defaultdict(int)
    
    total_size = 0
    file_count = 0
    
    for root, dirs, files in os.walk(project_root):
        # Исключаем директории
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        # Определяем категорию
        rel_path = Path(root).relative_to(project_root)
        if rel_path == Path('.'):
            category = 'root'
        elif 'bot' in rel_path.parts:
            category = 'bot'
        elif 'database' in rel_path.parts:
            category = 'database'
        elif 'services' in rel_path.parts:
            category = 'services'
        elif 'config' in rel_path.parts:
            category = 'config'
        elif 'utils' in rel_path.parts:
            category = 'utils'
        elif 'scripts' in rel_path.parts:
            category = 'scripts'
        elif rel_path.suffix == '.md' or 'docs' in rel_path.parts:
            category = 'documentation'
        else:
            category = 'other'
        
        for file in files:
            file_path = Path(root) / file
            
            # Пропускаем исключаемые файлы
            if file_path.suffix in exclude_exts:
                continue
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            
            try:
                size = file_path.stat().st_size
                total_size += size
                file_count += 1
                
                # По категориям
                categories[category] += size
                
                # По типам файлов
                ext = file_path.suffix or 'no_extension'
                file_types[ext] += size
                
                # По директориям (топ-20)
                dir_sizes[str(rel_path)] = dir_sizes.get(str(rel_path), 0) + size
                
            except (OSError, PermissionError):
                pass
    
    # Вывод результатов
    print("=" * 70)
    print("АНАЛИЗ РАЗМЕРА ПРОЕКТА")
    print("=" * 70)
    print()
    
    print(f"📊 Общая статистика:")
    print(f"   Всего файлов: {file_count}")
    print(f"   Общий размер: {format_size(total_size)}")
    print()
    
    print("📁 Размер по категориям:")
    for cat, size in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        percentage = (size / total_size * 100) if total_size > 0 else 0
        print(f"   {cat:20s}: {format_size(size):>12s} ({percentage:5.1f}%)")
    print()
    
    print("📄 Размер по типам файлов (топ-15):")
    for ext, size in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:15]:
        percentage = (size / total_size * 100) if total_size > 0 else 0
        ext_name = ext if ext else '(без расширения)'
        print(f"   {ext_name:20s}: {format_size(size):>12s} ({percentage:5.1f}%)")
    print()
    
    print("📂 Размер по директориям (топ-20):")
    for dir_path, size in sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)[:20]:
        percentage = (size / total_size * 100) if total_size > 0 else 0
        print(f"   {dir_path:50s}: {format_size(size):>12s} ({percentage:5.1f}%)")
    print()
    
    # Рекомендации
    print("=" * 70)
    print("💡 РЕКОМЕНДАЦИИ ДЛЯ СЕРВЕРА")
    print("=" * 70)
    print()
    
    code_size = categories.get('bot', 0) + categories.get('services', 0) + categories.get('database', 0)
    docs_size = categories.get('documentation', 0)
    
    print(f"Размер кода: {format_size(code_size)}")
    print(f"Размер документации: {format_size(docs_size)}")
    print(f"Размер проекта (без .git, venv, cache): {format_size(total_size)}")
    print()
    
    # Учитываем данные из RESOURCE_REQUIREMENTS.md
    print("📦 Рекомендуемый размер диска на сервере:")
    print()
    print("   Минимум (для кода и базовой БД):")
    print(f"   - Код приложения: {format_size(total_size)}")
    print("   - PostgreSQL: 1-5 GB (см. RESOURCE_REQUIREMENTS.md)")
    print("   - Redis: 64-256 MB")
    print("   - Файлы КП (за год): 8-20 GB")
    print("   - Запас (20%): ~2-5 GB")
    print("   ─────────────────────────────────────")
    print("   ИТОГО МИНИМУМ: ~15-30 GB")
    print()
    print("   Рекомендуется (с запасом на рост):")
    print("   - Код приложения: ~20 MB")
    print("   - PostgreSQL: 5-10 GB")
    print("   - Redis: 256-512 MB")
    print("   - Файлы КП (3+ года): 50-100 GB")
    print("   - Логи и временные файлы: 5-10 GB")
    print("   - Запас (30%): ~20-40 GB")
    print("   ─────────────────────────────────────")
    print("   ИТОГО РЕКОМЕНДУЕТСЯ: ~80-160 GB")
    print()
    print("=" * 70)

if __name__ == "__main__":
    analyze_project()

