# Script PowerShell para crear el instalador completo del Dashboard de Embargos
# Uso: .\crear_instalador.ps1
# Ejecutar desde la carpeta construccion/ o desde la raíz del proyecto

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  CREADOR DE INSTALADOR - Dashboard Embargos" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Detectar si estamos en la carpeta construccion o en la raíz
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($scriptDir -match "construccion$") {
    $projectRoot = Split-Path -Parent $scriptDir
    $construccionDir = $scriptDir
} else {
    $projectRoot = $scriptDir
    $construccionDir = Join-Path $projectRoot "construccion"
}

Write-Host "[INFO] Directorio del proyecto: $projectRoot" -ForegroundColor Gray
Write-Host "[INFO] Directorio de construccion: $construccionDir" -ForegroundColor Gray
Write-Host ""

# Cambiar al directorio del proyecto
Set-Location $projectRoot

# ============================================
# PASO 1: Verificar requisitos
# ============================================
Write-Host "[PASO 1] Verificando requisitos..." -ForegroundColor Yellow

# Verificar Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python no esta instalado o no esta en el PATH" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] $pythonVersion" -ForegroundColor Green

# Verificar PyInstaller
$pyinstallerCheck = pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] PyInstaller no instalado. Instalando..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] No se pudo instalar PyInstaller" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  [OK] PyInstaller instalado" -ForegroundColor Green

# Verificar archivos necesarios
$launcherPath = Join-Path $projectRoot "src\orquestacion\launcher.py"
if (-not (Test-Path $launcherPath)) {
    Write-Host "[ERROR] No se encontro launcher.py en src\orquestacion\" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Archivos fuente encontrados" -ForegroundColor Green
Write-Host ""

# ============================================
# PASO 2: Crear el ejecutable
# ============================================
Write-Host "[PASO 2] Creando ejecutable con PyInstaller..." -ForegroundColor Yellow
Write-Host "         (Esto puede tardar 5-15 minutos)" -ForegroundColor Gray
Write-Host ""

$buildScript = Join-Path $construccionDir "build_executable.py"
python $buildScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Fallo la creacion del ejecutable" -ForegroundColor Red
    exit 1
}

$exePath = Join-Path $projectRoot "dist\DashboardEmbargos.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "[ERROR] El ejecutable no se creo correctamente" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Ejecutable creado: $exePath" -ForegroundColor Green
Write-Host ""

# ============================================
# PASO 3: Buscar Inno Setup
# ============================================
Write-Host "[PASO 3] Buscando Inno Setup Compiler..." -ForegroundColor Yellow

$innoSetupPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    "C:\Program Files\Inno Setup 5\ISCC.exe"
)

$isccPath = $null
foreach ($path in $innoSetupPaths) {
    if (Test-Path $path) {
        $isccPath = $path
        break
    }
}

if ($null -eq $isccPath) {
    Write-Host "[WARN] Inno Setup no encontrado automaticamente" -ForegroundColor Yellow
    Write-Host ""
    
    # Aun sin Inno Setup, crear el portable
    Write-Host "[PASO 4] Creando version portable (ZIP)..." -ForegroundColor Yellow
    
    $installerDir = Join-Path $projectRoot "installer"
    if (-not (Test-Path $installerDir)) {
        New-Item -ItemType Directory -Path $installerDir -Force | Out-Null
    }
    
    $portableTemp = Join-Path $installerDir "DashboardEmbargos_Portable"
    if (Test-Path $portableTemp) {
        Remove-Item -Recurse -Force $portableTemp
    }
    New-Item -ItemType Directory -Path $portableTemp -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $portableTemp "datos") -Force | Out-Null
    
    Copy-Item $exePath -Destination $portableTemp
    Copy-Item (Join-Path $projectRoot "README.md") -Destination $portableTemp -ErrorAction SilentlyContinue
    
    $portableZip = Join-Path $installerDir "DashboardEmbargos_Portable.zip"
    if (Test-Path $portableZip) {
        Remove-Item -Force $portableZip
    }
    Compress-Archive -Path "$portableTemp\*" -DestinationPath $portableZip -Force
    Remove-Item -Recurse -Force $portableTemp
    
    Write-Host "  [OK] Portable creado: $portableZip" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  PORTABLE CREADO EXITOSAMENTE!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Archivos generados:" -ForegroundColor Cyan
    Write-Host "  Ejecutable: $exePath" -ForegroundColor White
    Write-Host "  Portable:   $portableZip" -ForegroundColor White
    Write-Host ""
    Write-Host "Para crear tambien el instalador, instala Inno Setup desde:" -ForegroundColor Cyan
    Write-Host "  https://jrsoftware.org/isinfo.php" -ForegroundColor White
    Write-Host ""
    Write-Host "Luego ejecuta este script de nuevo, o abre:" -ForegroundColor Cyan
    Write-Host "  $construccionDir\installer_setup.iss" -ForegroundColor White
    Write-Host "y presiona F9 para compilar." -ForegroundColor Cyan
    exit 0
}

Write-Host "  [OK] Inno Setup encontrado: $isccPath" -ForegroundColor Green
Write-Host ""

# ============================================
# PASO 4: Crear version portable (ZIP)
# ============================================
Write-Host "[PASO 4] Creando version portable (ZIP)..." -ForegroundColor Yellow

$installerDir = Join-Path $projectRoot "installer"
if (-not (Test-Path $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir -Force | Out-Null
}

# Crear carpeta temporal para el portable
$portableTemp = Join-Path $installerDir "DashboardEmbargos_Portable"
if (Test-Path $portableTemp) {
    Remove-Item -Recurse -Force $portableTemp
}
New-Item -ItemType Directory -Path $portableTemp -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $portableTemp "datos") -Force | Out-Null

# Copiar archivos al portable
Copy-Item $exePath -Destination $portableTemp
Copy-Item (Join-Path $projectRoot "README.md") -Destination $portableTemp -ErrorAction SilentlyContinue

# Crear el ZIP
$portableZip = Join-Path $installerDir "DashboardEmbargos_Portable.zip"
if (Test-Path $portableZip) {
    Remove-Item -Force $portableZip
}
Compress-Archive -Path "$portableTemp\*" -DestinationPath $portableZip -Force

# Limpiar carpeta temporal
Remove-Item -Recurse -Force $portableTemp

Write-Host "  [OK] Portable creado: $portableZip" -ForegroundColor Green
Write-Host ""

# ============================================
# PASO 5: Crear el instalador
# ============================================
Write-Host "[PASO 5] Creando instalador con Inno Setup..." -ForegroundColor Yellow

$issPath = Join-Path $construccionDir "installer_setup.iss"

# Ejecutar Inno Setup
& $isccPath $issPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Fallo la creacion del instalador" -ForegroundColor Red
    exit 1
}

$installerPath = Join-Path $installerDir "DashboardEmbargos_Installer.exe"
if (-not (Test-Path $installerPath)) {
    Write-Host "[ERROR] El instalador no se creo correctamente" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  CONSTRUCCION COMPLETADA EXITOSAMENTE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Archivos generados:" -ForegroundColor Cyan
Write-Host "  Ejecutable:  $exePath" -ForegroundColor White
Write-Host "  Portable:    $portableZip" -ForegroundColor White
Write-Host "  Instalador:  $installerPath" -ForegroundColor White
Write-Host ""
Write-Host "Para distribuir:" -ForegroundColor Cyan
Write-Host "  - Instalador: DashboardEmbargos_Installer.exe (instalacion completa)" -ForegroundColor White
Write-Host "  - Portable:   DashboardEmbargos_Portable.zip (sin instalacion)" -ForegroundColor White
Write-Host ""
