@echo off
cd /d C:\BiogasApp
cls
echo ==========================================
echo    BioOptima 360 - GitHub Cloud Snelkoppeling
echo ==========================================
echo.
echo 1. Ophalen en synchroniseren met cloud...
git pull origin main --rebase --allow-unrelated-histories

echo.
echo 2. Lokale bestanden toevoegen...
git add .

echo.
set /p commit_msg="Typ een korte omschrijving van je wijzigingen: "
if "%commit_msg%"=="" set commit_msg="Update via batch script"

echo.
echo 3. Vastleggen en uploaden naar GitHub...
git commit -m "%commit_msg%"
git push origin main

echo.
echo ==========================================
echo Klaar! Je code staat veilig in de cloud.
echo ==========================================
pause