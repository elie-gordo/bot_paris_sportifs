@echo off
echo.
echo ========================================
echo     BetIQ 2.5 - MODE DEMO
echo ========================================
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
echo Demarrage en mode demonstration...
echo Les donnees affichees sont factices
echo.

python main.py --demo

echo.
echo Bot arrete.
pause
