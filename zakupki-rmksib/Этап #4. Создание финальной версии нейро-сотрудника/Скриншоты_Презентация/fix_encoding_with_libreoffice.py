#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для исправления кодировки презентации через LibreOffice
LibreOffice лучше обрабатывает кодировку и сохраняет все элементы, включая диаграммы
"""
import os
import sys
import subprocess
import time

# Настройка кодировки для Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def find_libreoffice():
    """
    Находит путь к LibreOffice
    """
    possible_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        r"C:\Program Files\LibreOffice 7\program\soffice.exe",
        r"C:\Program Files\LibreOffice 6\program\soffice.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def fix_with_libreoffice(input_file: str, output_file: str = None):
    """
    Исправляет презентацию через LibreOffice
    LibreOffice автоматически исправляет кодировку и сохраняет все элементы
    """
    if not os.path.exists(input_file):
        print(f"[ERROR] Файл '{input_file}' не найден!")
        return False
    
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_FIXED_LO.pptx"
    
    # Находим LibreOffice
    lo_path = find_libreoffice()
    if not lo_path:
        print("[ERROR] LibreOffice не найден!")
        print("\n[INFO] Установите LibreOffice:")
        print("  https://www.libreoffice.org/download/")
        print("\n[INFO] Или используйте Microsoft PowerPoint:")
        print("  1. Откройте файл в PowerPoint")
        print("  2. Файл -> Сохранить как")
        print("  3. Выберите формат PowerPoint Presentation (.pptx)")
        print("  4. Сохраните с новым именем")
        return False
    
    try:
        print(f"[INFO] Используется LibreOffice: {lo_path}")
        print(f"[INFO] Открываю файл: {input_file}")
        
        # Команда для конвертации через LibreOffice
        # --headless - запуск без GUI
        # --convert-to pptx - конвертация в pptx
        # --outdir - папка для сохранения
        
        output_dir = os.path.dirname(os.path.abspath(output_file))
        output_name = os.path.basename(output_file)
        
        cmd = [
            lo_path,
            "--headless",
            "--convert-to", "pptx",
            "--outdir", output_dir,
            os.path.abspath(input_file)
        ]
        
        print(f"[INFO] Выполняю команду: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # LibreOffice сохраняет файл с тем же именем, но расширением .pptx
            # Нужно переименовать
            input_base = os.path.splitext(os.path.basename(input_file))[0]
            temp_output = os.path.join(output_dir, f"{input_base}.pptx")
            
            if os.path.exists(temp_output):
                if temp_output != output_file:
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    os.rename(temp_output, output_file)
                
                print(f"[OK] Файл успешно обработан: {output_file}")
                print("[INFO] LibreOffice автоматически исправил кодировку и сохранил все элементы")
                return True
            else:
                print(f"[ERROR] Временный файл не найден: {temp_output}")
                return False
        else:
            print(f"[ERROR] Ошибка выполнения LibreOffice:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] Превышено время ожидания выполнения LibreOffice")
        return False
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "Zakupki-RMKSIB-AI-Assistent-1.pptx")
    
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
    
    fix_with_libreoffice(input_file, output_file)

