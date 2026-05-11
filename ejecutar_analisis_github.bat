@echo off
title Ejecutar Analisis de Acciones en GitHub
color 0A

echo ==============================================
echo   ACTIVAR ANALISIS DE ACCIONES EN GITHUB
echo ==============================================
echo.

set /p TOKEN=Pega tu token de GitHub:
set /p USUARIO=Tu usuario de GitHub:
set /p REPO=Nombre del repositorio:

echo.
echo Enviando solicitud a GitHub Actions...
echo.

curl -X POST ^
-H "Authorization: Bearer %TOKEN%" ^
-H "Accept: application/vnd.github+json" ^
-H "X-GitHub-Api-Version: 2022-11-28" ^
https://api.github.com/repos/%USUARIO%/%REPO%/actions/workflows/analizar.yml/dispatches ^
-d "{\"ref\":\"main\"}"

echo.
echo.
echo Solicitud enviada.
echo Espera 1 a 3 minutos.
echo Luego abre tu pagina de GitHub Pages y presiona "Actualizar vista".
echo.
pause
