# Инструкция по исправлению презентации

## Проблема
При попытке выполнить Python код напрямую в bash терминале возникают ошибки:
```
bash: from: command not found
bash: syntax error near unexpected token `('
```

## Решение

### ✅ Правильный способ использования

**Вариант 1: Использовать готовый скрипт (рекомендуется)**

```bash
# Перейти в папку со скриптом
cd "Этап #4. Создание финальной версии нейро-сотрудника/Скриншоты_Презентация"

# Запустить скрипт
python fix_presentation.py
```

Скрипт автоматически:
- Найдет файл `Zakupki-RMKSIB-AI-Assistent-1.pptx`
- Создаст исправленный файл `Zakupki-RMKSIB-AI-Assistent-1_FIXED.pptx`

**Вариант 2: Указать файлы вручную**

```bash
python fix_presentation.py "путь/к/файлу.pptx" "путь/к/выходному_файлу.pptx"
```

**Вариант 3: Интерактивный режим Python**

```bash
# Запустить Python
python

# В интерактивном режиме выполнить:
>>> from pptx import Presentation
>>> prs = Presentation('Zakupki-RMKSIB-AI-Assistent-1.pptx')
>>> prs.save('Zakupki-RMKSIB-AI-Assistent-FIXED.pptx')
>>> exit()
```

**Вариант 4: Однострочная команда**

```bash
python -c "from pptx import Presentation; prs = Presentation('Zakupki-RMKSIB-AI-Assistent-1.pptx'); prs.save('Zakupki-RMKSIB-AI-Assistent-FIXED.pptx')"
```

## ❌ Неправильные способы

### Неправильно 1: Выполнение Python кода в bash
```bash
$ from pptx import Presentation  # ❌ ОШИБКА!
```
**Почему не работает:** Bash не понимает синтаксис Python. Нужно использовать `python` для выполнения Python кода.

### Неправильно 2: Копирование примеров как команд
```bash
$ # Вариант 1: Создать .py файл и запустить  # ❌ Это комментарий, не команда!
$ python fix_presentation.py  # ✅ Это правильная команда
```
**Почему не работает:** Строки с `#` - это комментарии, их не нужно копировать. Копируйте только команды без `#`.

### Неправильно 3: Копирование интерактивного режима как команд
```bash
$ >>> from pptx import Presentation  # ❌ ОШИБКА!
```
**Почему не работает:** `>>>` - это приглашение Python интерактивного режима, не команда bash. Сначала запустите `python`, затем введите команды.

## Результат

После правильного выполнения скрипта будет создан файл:
- `Zakupki-RMKSIB-AI-Assistent-1_FIXED.pptx`

Этот файл содержит исправленную кодировку и готов к использованию.

## Проверка результата

Убедитесь, что файл создан:
```bash
ls -la *.pptx
# или в Windows PowerShell:
dir *.pptx
```

