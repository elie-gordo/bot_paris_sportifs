@echo off
echo.
echo ======================================
echo        BetIQ 2.5 - BOT TELEGRAM
echo ======================================
echo.

echo Activation de l'environnement virtuel...
if not exist "venv\Scripts\activate.bat" (
    echo ERREUR: Environnement virtuel non trouve!
    echo Veuillez d'abord executer: python -m venv venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo.
echo Verification des dependances...
pip show python-telegram-bot >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installation des dependances...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ERREUR: Impossible d'installer les dependances
        pause
        exit /b 1
    )
)

echo.
echo Verification du fichier de configuration...
if not exist .env (
    echo ERREUR: Fichier .env manquant
    echo Creez le fichier .env avec vos cles API
    pause
    exit /b 1
)

echo.
echo ======================================
echo     DEMARRAGE DE BETIQ 2.5
echo ======================================
echo.
echo Ctrl+C pour arreter le bot
echo.

python main.py

pause
