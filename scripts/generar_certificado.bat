@echo off
REM Genera certificado autofirmado para HTTPS local (OpenSSL requerido)
mkdir ..\nginx\certs 2>nul
openssl req -x509 -nodes -days 365 -newkey rsa:2048 ^
  -keyout ..\nginx\certs\key.pem ^
  -out ..\nginx\certs\cert.pem ^
  -subj "/CN=hospital.local/O=HNNCJ"
echo Certificados creados en nginx\certs\
