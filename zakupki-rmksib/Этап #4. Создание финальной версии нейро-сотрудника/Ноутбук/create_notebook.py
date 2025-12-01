"""
Скрипт для создания .ipynb файла из neuro_employee_colab_final.py

Использование:
    python create_notebook.py
"""

import json
from pathlib import Path


def create_notebook_from_py(py_file: str, output_file: str):
    """Создание .ipynb файла из .py файла с разбивкой по ячейкам"""
    
    # Читаем Python файл
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Разбиваем на ячейки по комментариям
    cells = []
    current_cell = []
    current_type = 'code'
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Проверяем начало новой ячейки
        if '# ============================================================================' in line:
            # Сохраняем предыдущую ячейку
            if current_cell:
                cells.append({
                    'cell_type': current_type,
                    'metadata': {},
                    'source': current_cell
                })
            
            # Определяем тип следующей ячейки
            i += 1
            if i < len(lines):
                comment_line = lines[i]
                if 'ЯЧЕЙКА' in comment_line:
                    # Это кодовая ячейка
                    current_type = 'code'
                    current_cell = []
                    # Пропускаем строку с комментарием
                    i += 1
                    continue
                elif 'ТЕСТОВАЯ' in comment_line or 'Запустите' in comment_line:
                    # Это тоже кодовая ячейка
                    current_type = 'code'
                    current_cell = []
                    i += 1
                    continue
            
        current_cell.append(line + '\n')
        i += 1
    
    # Добавляем последнюю ячейку
    if current_cell:
        cells.append({
            'cell_type': current_type,
            'metadata': {},
            'source': current_cell
        })
    
    # Создаем структуру ноутбука
    notebook = {
        'cells': cells,
        'metadata': {
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3'
            },
            'language_info': {
                'name': 'python',
                'version': '3.8.0'
            }
        },
        'nbformat': 4,
        'nbformat_minor': 4
    }
    
    # Сохраняем ноутбук
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, ensure_ascii=False, indent=2)
    
    print(f"Ноутбук успешно создан: {output_file}")


def create_notebook_manual():
    """Создание ноутбука вручную с правильной структурой"""
    
    py_file = Path(__file__).parent / "neuro_employee_colab_final.py"
    
    with open(py_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Разбиваем на секции по комментариям ЯЧЕЙКА
    sections = []
    current_section = []
    section_title = None
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if '# ЯЧЕЙКА' in line or '# ============================================================================' in line:
            if current_section and section_title:
                sections.append({
                    'title': section_title,
                    'code': '\n'.join(current_section)
                })
            current_section = []
            # Извлекаем название секции
            if '# ЯЧЕЙКА' in line:
                section_title = line.split('# ЯЧЕЙКА')[1].strip()
            else:
                section_title = None
        else:
            current_section.append(line)
    
    # Добавляем последнюю секцию
    if current_section:
        sections.append({
            'title': section_title or 'Код',
            'code': '\n'.join(current_section)
        })
    
    # Создаем ячейки ноутбука
    cells = []
    
    # Ячейка 1: Установка зависимостей
    cells.append({
        'cell_type': 'code',
        'metadata': {},
        'source': ['!pip install httpx -q\n'],
        'execution_count': None,
        'outputs': []
    })
    
    # Ячейка 2: Импорты и функции (объединяем все функции)
    all_code = []
    for section in sections:
        if section['code'].strip():
            all_code.append(section['code'])
    
    cells.append({
        'cell_type': 'code',
        'metadata': {},
        'source': '\n'.join(all_code).split('\n'),
        'execution_count': None,
        'outputs': []
    })
    
    # Ячейка 3: Запуск main()
    cells.append({
        'cell_type': 'code',
        'metadata': {},
        'source': ['await main()\n'],
        'execution_count': None,
        'outputs': []
    })
    
    # Создаем ноутбук
    notebook = {
        'cells': cells,
        'metadata': {
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3'
            },
            'language_info': {
                'name': 'python',
                'version': '3.8.0'
            },
            'colab': {
                'name': 'neuro_employee_colab_final.ipynb',
                'provenance': []
            }
        },
        'nbformat': 4,
        'nbformat_minor': 4
    }
    
    output_file = Path(__file__).parent / "neuro_employee_colab_final.ipynb"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, ensure_ascii=False, indent=2)
    
    print(f"Ноутбук успешно создан: {output_file}")


if __name__ == "__main__":
    create_notebook_manual()

