@echo off
REM Script para crear el instalador completo del Dashboard de Embargos
REM Uso: crear_instalador.bat
REM Ejecutar desde la carpeta construccion/ o desde la raiz del proyecto

echo ============================================
echo   CREADOR DE INSTALADOR - Dashboard Embargos
echo ============================================
echo.

REM Detectar directorio actual
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Verificar si estamos en construccion o en la raiz
echo %SCRIPT_DIR% | findstr /i "construccion" >nul
if %ERRORLEVEL% EQU 0 (
    for %%I in ("%SCRIPT_DIR%\..") do set "PROJECT_ROOT=%%~fI"
    set "CONSTRUCCION_DIR=%SCRIPT_DIR%"
) else (
    set "PROJECT_ROOT=%SCRIPT_DIR%"
    set "CONSTRUCCION_DIR=%SCRIPT_DIR%\construccion"
)

echo [INFO] Directorio del proyecto: %PROJECT_ROOT%
echo [INFO] Directorio de construccion: %CONSTRUCCION_DIR%
echo.

REM Cambiar al directorio del proyecto
cd /d "%PROJECT_ROOT%"

REM ============================================
REM PASO 1: Verificar Python
REM ============================================
echo [PASO 1] Verificando requisitos...

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    pause
    exit /b 1
)
echo   [OK] Python encontrado

REM Verificar PyInstaller
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   [WARN] PyInstaller no instalado. Instalando...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] No se pudo instalar PyInstaller
        pause
        exit /b 1
    )
)
echo   [OK] PyInstaller instalado

REM Verificar archivos
if not exist "%PROJECT_ROOT%\src\orquestacion\launcher.py" (
    echo [ERROR] No se encontro launcher.py en src\orquestacion\
    pause
    exit /b 1
)
echo   [OK] Archivos fuente encontrados
echo.

REM ============================================
REM PASO 2: Crear el ejecutable
REM ============================================
echo [PASO 2] Creando ejecutable con PyInstaller...
echo          (Esto puede tardar 5-15 minutos)
echo.

python "%CONSTRUCCION_DIR%\build_executable.py"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo la creacion del ejecutable
    pause
    exit /b 1
)

if not exist "%PROJECT_ROOT%\dist\DashboardEmbargos.exe" (
    echo [ERROR] El ejecutable no se creo correctamente
    pause
    exit /b 1
)
echo [OK] Ejecutable creado: %PROJECT_ROOT%\dist\DashboardEmbargos.exe
echo.

REM ============================================
REM PASO 3: Buscar Inno Setup
REM ============================================
echo [PASO 3] Buscando Inno Setup Compiler...

set "ISCC_PATH="

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 5\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 5\ISCC.exe"
)

if "%ISCC_PATH%"=="" (
    echo [WARN] Inno Setup no encontrado automaticamente
    echo.
    
    REM Aun sin Inno Setup, crear el portable
    echo [PASO 4] Creando version portable ZIP...
    
    if not exist "%PROJECT_ROOT%\installer" mkdir "%PROJECT_ROOT%\installer"
    
    set "PORTABLE_DIR=%PROJECT_ROOT%\installer\DashboardEmbargos_Portable"
    if exist "%PORTABLE_DIR%" rmdir /s /q "%PORTABLE_DIR%"
    mkdir "%PORTABLE_DIR%"
    mkdir "%PORTABLE_DIR%\datos"
    
    copy "%PROJECT_ROOT%\dist\DashboardEmbargos.exe" "%PORTABLE_DIR%\" >nul
    copy "%PROJECT_ROOT%\README.md" "%PORTABLE_DIR%\" >nul 2>&1
    
    REM Crear ZIP usando PowerShell
    powershell -Command "Compress-Archive -Path '%PORTABLE_DIR%\*' -DestinationPath '%PROJECT_ROOT%\installer\DashboardEmbargos_Portable.zip' -Force"
    
    rmdir /s /q "%PORTABLE_DIR%"
    
    echo   [OK] Portable creado: %PROJECT_ROOT%\installer\DashboardEmbargos_Portable.zip
    echo.
    echo ============================================
    echo   PORTABLE CREADO EXITOSAMENTE!
    echo ============================================
    echo.
    echo Archivos generados:
    echo   Ejecutable: %PROJECT_ROOT%\dist\DashboardEmbargos.exe
    echo   Portable:   %PROJECT_ROOT%\installer\DashboardEmbargos_Portable.zip
    echo.
    echo Para crear tambien el instalador, instala Inno Setup desde:
    echo   https://jrsoftware.org/isinfo.php
    echo.
    echo Luego ejecuta este script de nuevo.
    echo.
    pause
    exit /b 0
)

echo   [OK] Inno Setup encontrado: %ISCC_PATH%
echo.

REM ============================================
REM PASO 4: Crear version portable (ZIP)
REM ============================================
echo [PASO 4] Creando version portable ZIP...

if not exist "%PROJECT_ROOT%\installer" mkdir "%PROJECT_ROOT%\installer"

set "PORTABLE_DIR=%PROJECT_ROOT%\installer\DashboardEmbargos_Portable"
if exist "%PORTABLE_DIR%" rmdir /s /q "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%\datos"

copy "%PROJECT_ROOT%\dist\DashboardEmbargos.exe" "%PORTABLE_DIR%\" >nul
copy "%PROJECT_ROOT%\README.md" "%PORTABLE_DIR%\" >nul 2>&1

REM Crear ZIP usando PowerShell
powershell -Command "Compress-Archive -Path '%PORTABLE_DIR%\*' -DestinationPath '%PROJECT_ROOT%\installer\DashboardEmbargos_Portable.zip' -Force"

rmdir /s /q "%PORTABLE_DIR%"

echo   [OK] Portable creado
echo.

REM ============================================
REM PASO 5: Crear el instalador
REM ============================================
echo [PASO 5] Creando instalador con Inno Setup...

"%ISCC_PATH%" "%CONSTRUCCION_DIR%\installer_setup.iss"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo la creacion del instalador
    pause
    exit /b 1
)

if not exist "%PROJECT_ROOT%\installer\DashboardEmbargos_Installer.exe" (
    echo [ERROR] El instalador no se creo correctamente
    pause
    exit /b 1
)

echo.
echo ============================================
echo   CONSTRUCCION COMPLETADA EXITOSAMENTE!
echo ============================================
echo.
echo Archivos generados:
echo   Ejecutable:  %PROJECT_ROOT%\dist\DashboardEmbargos.exe
echo   Portable:    %PROJECT_ROOT%\installer\DashboardEmbargos_Portable.zip
echo   Instalador:  %PROJECT_ROOT%\installer\DashboardEmbargos_Installer.exe
echo.
echo Para distribuir:
echo   - Instalador: DashboardEmbargos_Installer.exe (instalacion completa)
echo   - Portable:   DashboardEmbargos_Portable.zip (sin instalacion)
echo.
pause
