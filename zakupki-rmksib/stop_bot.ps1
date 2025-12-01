# Скрипт для остановки всех экземпляров бота
# Использование: powershell -ExecutionPolicy Bypass -File stop_bot.ps1

Write-Host "Поиск процессов бота..." -ForegroundColor Yellow

# Найти все процессы Python
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "Найдено процессов Python: $($pythonProcesses.Count)" -ForegroundColor Cyan
    
    foreach ($proc in $pythonProcesses) {
        Write-Host "Процесс PID: $($proc.Id), Путь: $($proc.Path)" -ForegroundColor Gray
    }
    
    Write-Host "`nОстановка всех процессов Python..." -ForegroundColor Yellow
    Write-Host "ВНИМАНИЕ: Это остановит ВСЕ процессы Python!" -ForegroundColor Red
    
    $response = Read-Host "Продолжить? (y/n)"
    
    if ($response -eq "y" -or $response -eq "Y") {
        $pythonProcesses | Stop-Process -Force
        Write-Host "Все процессы Python остановлены!" -ForegroundColor Green
    } else {
        Write-Host "Отменено." -ForegroundColor Yellow
    }
} else {
    Write-Host "Процессы Python не найдены." -ForegroundColor Green
}

Write-Host "`nПроверка после остановки..." -ForegroundColor Cyan
$remaining = Get-Process python -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "Осталось процессов: $($remaining.Count)" -ForegroundColor Red
} else {
    Write-Host "Все процессы остановлены. Можно запускать бота заново." -ForegroundColor Green
}

