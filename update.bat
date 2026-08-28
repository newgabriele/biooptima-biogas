@echo off
cd /d C:\BiogasApp
cls
echo ==========================================
echo    BioOptima 360° - GitHub Cloud Snelkoppeling
echo ==========================================
echo.
git status
echo.
set /p commit_msg="Typ een korte omschrijving van je wijzigingen: "

if "%commit_msg%"=="" set commit_msg="Snelle update via batch script"

echo.
echo Bezig met toevoegen en vastleggen...
git add .
git commit -m "%commit_msg%"

echo.
echo Bezig met uploaden naar GitHub (cloud)...
git push origin main

echo.
echo ==========================================
echo Klaar! Je code staat veilig in de cloud.
echo ==========================================
pause