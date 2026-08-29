@echo off
cd /d C:\BiogasApp
cls
echo ==========================================
echo    BioOptima 360 - GitHub Cloud Snelkoppeling
echo ==========================================
echo.
echo 0. Python, Git en vastgelopen locks opschonen...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im git.exe >nul 2>&1
git rebase --abort >nul 2>&1
git merge --abort >nul 2>&1
if exist .git\index.lock del /f /q .git\index.lock

echo.
echo 1. Lokale wijzigingen vastleggen...
git add .
set /p commit_msg="Typ een korte omschrijving van je wijzigingen: "
if "%commit_msg%"=="" set commit_msg="Update via batch script"
git commit -m "%commit_msg%"

echo.
echo 2. Synchroniseren en krachtig forceren naar GitHub...
git push origin main --force

echo.
echo ==========================================
echo Klaar! Je code staat veilig in de cloud.
echo ==========================================
pause