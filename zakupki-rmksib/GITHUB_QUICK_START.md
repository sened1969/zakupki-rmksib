# Быстрый старт: Размещение на GitHub

## Минимальные шаги (для опытных пользователей)

### 1. Создайте репозиторий на GitHub
- Перейдите на github.com → New repository
- Скопируйте HTTPS URL репозитория

### 2. Настройте Git (если еще не настроено)
```bash
git config --global user.name "Ваше Имя"
git config --global user.email "your.email@example.com"
```

### 3. Добавьте удаленный репозиторий
```bash
git remote add origin https://github.com/ваш-username/zakupki-rmksib.git
```

### 4. Первый коммит и отправка
```bash
git add .
git commit -m "Initial commit: AI-ассистент закупок"
git branch -M main
git push -u origin main
```

### 5. Авторизация
При запросе используйте **Personal Access Token** (не пароль):
- GitHub → Settings → Developer settings → Personal access tokens → Generate new token
- Выберите права: `repo`
- Используйте токен как пароль

---

## Проверка перед публикацией

✅ Убедитесь, что в `.gitignore` есть:
- `.env`
- `*.db`
- `procurement.db`
- `SECURITY_ENCRYPTION_KEY.md`

✅ Проверьте, что не загружаете:
- API ключи
- Пароли
- Базу данных
- Секретные файлы

---

## Последующие обновления

```bash
git add .
git commit -m "Описание изменений"
git push origin main
```

---

**Подробная инструкция**: см. `GITHUB_DEPLOYMENT.md`

