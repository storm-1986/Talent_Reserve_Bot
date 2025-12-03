@echo off
chcp 65001 >nul
title Talent Reserve Bot
echo ========================================
echo    Запуск бота опроса Telegram
echo ========================================

cd /d C:\Talent_Reserve_Bot

:: Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    echo Установите Python или проверьте PATH
    pause
    exit /b 1
)

:: Проверка наличия файла бота
if not exist "bot.py" (
    echo Ошибка: Файл bot.py не найден!
    pause
    exit /b 1
)

echo Python найден: 
python --version
echo Запуск бота...
echo.

:: Запуск бота
python bot.py

:: Если бот завершился с ошибкой
if errorlevel 1 (
    echo.
    echo ========================================
    echo    Бот завершился с ошибкой!
    echo ========================================
    echo Код ошибки: %errorlevel%
    echo.
    echo Возможные причины:
    echo 1. Отсутствуют библиотеки
    echo 2. Неверный токен в .env
    echo 3. Проблемы с сетью
    echo.
    pause
)