#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для исправления кодировки в презентации PowerPoint
"""
from pptx import Presentation
import os
import sys

# Настройка кодировки для Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def fix_presentation(input_file: str, output_file: str = None):
    """
    Открывает презентацию и сохраняет её с исправленной кодировкой
    
    Args:
        input_file: Путь к исходному файлу .pptx
        output_file: Путь к выходному файлу (если None, добавляется _FIXED)
    """
    if not os.path.exists(input_file):
        print(f"[ERROR] Ошибка: Файл '{input_file}' не найден!")
        return False
    
    if output_file is None:
        # Создаём имя выходного файла
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_FIXED.pptx"
    
    try:
        print(f"[INFO] Открываю файл: {input_file}")
        prs = Presentation(input_file)
        
        print(f"[INFO] Сохраняю исправленный файл: {output_file}")
        prs.save(output_file)
        
        print(f"[OK] Файл успешно исправлен и сохранён: {output_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при обработке файла: {e}")
        return False

if __name__ == "__main__":
    # Определяем путь к файлу относительно скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "Zakupki-RMKSIB-AI-Assistent-1.pptx")
    
    # Если файл не найден, пробуем альтернативное имя
    if not os.path.exists(input_file):
        alt_file = os.path.join(script_dir, "Закупки РМКСИБ — AI-Ассистент.pptx")
        if os.path.exists(alt_file):
            input_file = alt_file
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = None
    
    fix_presentation(input_file, output_file)

