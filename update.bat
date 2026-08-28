@echo off
cd /d C:\BiogasApp
cls
echo ==========================================
echo    BioOptima 360 - GitHub Cloud Snelkoppeling
echo ==========================================
echo.
echo 1. Lokale wijzigingen vastleggen...
git add .
set /p commit_msg="Typ een korte omschrijving van je wijzigingen: "
if "%commit_msg%"=="" set commit_msg="Update via batch script"
git commit -m "%commit_msg%"

echo.
echo 2. Ophalen en synchroniseren met de cloud...
git pull origin main --rebase --allow-unrelated-histories

echo.
echo 3. Uploaden naar GitHub...
git push origin main

echo.
echo ==========================================
echo Klaar! Je code staat veilig in de cloud.
echo ==========================================
pause