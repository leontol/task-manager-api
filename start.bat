@echo off
chcp 65001 >nul
title Task Manager - FastAPI + PostgreSQL

:: Переходим в папку проекта
cd /d "E:\Task_manager"

:menu
cls
echo ========================================
echo    Task Manager API - Выбор режима
echo ========================================
echo.
echo   [1] PostgreSQL режим (данные сохраняются)
echo   [2] In-Memory режим (данные не сохраняются)
echo   [3] Выход
echo.
set /p choice="Выберите режим (1, 2 или 3): "

if "%choice%"=="1" goto postgres_mode
if "%choice%"=="2" goto memory_mode
if "%choice%"=="3" goto exit
goto menu

:: ========================================
:: РЕЖИМ 1: POSTGRESQL
:: ========================================
:postgres_mode
cls
echo ========================================
echo    Запуск в PostgreSQL режиме
echo ========================================
echo.

:: 1. Проверка Docker
echo [1/3] Проверка Docker...
docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo [ОШИБКА] Docker не запущен!
    echo Пожалуйста, запустите Docker Desktop и повторите попытку.
    echo.
    pause
    goto menu
)
echo [OK] Docker работает
echo.

:: 2. Запуск PostgreSQL
echo [2/3] Запуск PostgreSQL...
docker ps -a --format "table {{.Names}}" | findstr "task_postgres" >nul
if %errorlevel% equ 0 (
    echo Контейнер найден, запускаю...
    docker start task_postgres >nul 2>nul
) else (
    echo Создаю новый контейнер...
    docker run -d ^
        --name task_postgres ^
        -e POSTGRES_USER=admin ^
        -e POSTGRES_PASSWORD=admin123 ^
        -e POSTGRES_DB=taskdb ^
        -p 5432:5432 ^
        postgres:15-alpine >nul 2>nul
)

:: Ждём запуска
echo Ожидание запуска PostgreSQL...
timeout /t 8 /nobreak >nul
echo [OK] PostgreSQL запущен
echo.

:: 3. Настройка .env для PostgreSQL
echo [3/3] Настройка окружения...
(
echo USE_DATABASE=true
echo API_KEY=secret-api-key-12345
echo DB_HOST=localhost
echo DB_PORT=5432
echo DB_USER=admin
echo DB_PASSWORD=admin123
echo DB_NAME=taskdb
) > .env
echo [OK] Файл .env настроен для PostgreSQL
echo.

goto start_app

:: ========================================
:: РЕЖИМ 2: IN-MEMORY
:: ========================================
:memory_mode
cls
echo ========================================
echo    Запуск в In-Memory режиме
echo ========================================
echo.

:: Настройка .env для In-Memory
echo [1/1] Настройка окружения...
(
echo USE_DATABASE=false
echo API_KEY=secret-api-key-12345
) > .env
echo [OK] Файл .env настроен для In-Memory режима
echo.

goto start_app

:: ========================================
:: ЗАПУСК ПРИЛОЖЕНИЯ
:: ========================================
:start_app
:: Создаём папку для логов
if not exist "logs" mkdir logs

cls
echo ========================================
echo    Task Manager API - ЗАПУЩЕН
echo ========================================
echo.
echo Адрес:           http://localhost:8000
echo Документация:    http://localhost:8000/api/docs
echo Health check:    http://localhost:8000/health
echo.

if "%choice%"=="1" (
    echo Режим:           POSTGRESQL (данные сохраняются)
    echo База данных:     localhost:5432/taskdb
    echo.
    echo ВНИМАНИЕ: Убедитесь, что таблицы созданы!
    echo Если нет, выполните в другом окне:
    echo docker exec task_postgres psql -U admin -d taskdb -f scripts/init_db.sql
) else (
    echo Режим:           IN-MEMORY (данные НЕ сохраняются)
)
echo.
echo Логи:            logs\api.log
echo.
echo ========================================
echo Для остановки сервера нажмите Ctrl+C
echo ========================================
echo.

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

echo.
echo ========================================
echo    Сервер остановлен
echo ========================================
echo.
pause
goto menu

:exit
echo.
echo До свидания!
timeout /t 2 /nobreak >nul
exit