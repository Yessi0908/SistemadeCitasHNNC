@echo off
REM Respaldo automatico PostgreSQL — ajustar rutas segun instalacion
set FECHA=%date:~-4%%date:~3,2%%date:~0,2%
set ARCHIVO=respaldo_hospital_%FECHA%.sql
pg_dump -U postgres -h localhost hospital_nicolasacruz > "%ARCHIVO%"
echo Respaldo guardado: %ARCHIVO%
