@echo off
:: Ejecutar este archivo con clic derecho -> "Ejecutar como administrador"
:: Restablece la contraseña de postgres y crea la base del hospital.

if not defined PG_DATA_DIR (
  set /p DATA_DIR=Ruta del data directory de PostgreSQL (ej. C:\Program Files\PostgreSQL\18\data): 
) else (
  set DATA_DIR=%PG_DATA_DIR%
)
set PSQL=C:\Program Files\PostgreSQL\18\bin\psql.exe
set PGCTL=C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe
if "%DATA_DIR%"=="" (
  echo ERROR: Debes indicar el data directory de PostgreSQL.
  pause
  exit /b 1
)
set HBA=%DATA_DIR%\pg_hba.conf
set BAK=%DATA_DIR%\pg_hba.conf.bak_setup
set /p NEWPASS=Escribe la nueva contrasena para el usuario postgres: 

if "%NEWPASS%"=="" (
  echo ERROR: Debes indicar una contrasena.
  pause
  exit /b 1
)

echo.
echo === Configurar PostgreSQL para Demo02 ===
echo.

if not exist "%HBA%" (
  echo ERROR: No se encuentra %HBA%
  pause
  exit /b 1
)

copy /Y "%HBA%" "%BAK%" >nul
powershell -NoProfile -Command "(Get-Content -Raw '%HBA%') -replace 'scram-sha-256','trust' -replace '(?m)\bmd5\b','trust' | Set-Content -Encoding ascii '%HBA%'"

"%PGCTL%" reload -D "%DATA_DIR%"
if errorlevel 1 (
  echo Recarga fallo; reiniciando servicio...
  net stop postgresql-x64-18
  net start postgresql-x64-18
)
timeout /t 2 /nobreak >nul

"%PSQL%" -U postgres -h 127.0.0.1 -p 5432 -c "ALTER USER postgres WITH PASSWORD '%NEWPASS%';"
"%PSQL%" -U postgres -h 127.0.0.1 -p 5432 -c "SELECT 1 FROM pg_database WHERE datname='hospital_nicolasacruz'" -tA > "%TEMP%\dbcheck.txt"
findstr /R /C:"1" "%TEMP%\dbcheck.txt" >nul
if errorlevel 1 (
  "%PSQL%" -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE hospital_nicolasacruz OWNER postgres ENCODING 'UTF8';"
) else (
  echo La base hospital_nicolasacruz ya existe.
)

copy /Y "%BAK%" "%HBA%" >nul
"%PGCTL%" reload -D "%DATA_DIR%"
if errorlevel 1 (
  net stop postgresql-x64-18
  net start postgresql-x64-18
)

set PGPASSWORD=%NEWPASS%
echo.
echo === Verificacion ===
"%PSQL%" -U postgres -h 127.0.0.1 -p 5432 -c "\l hospital_nicolasacruz"
echo.
echo Listo. Contraseña de postgres actualizada (no se muestra por seguridad).
echo Base: hospital_nicolasacruz
echo Recuerde poner la misma clave en DB_PASSWORD de su archivo .env
echo.
pause
