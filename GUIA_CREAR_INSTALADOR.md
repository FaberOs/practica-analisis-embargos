# Guía: Cómo Crear el Instalador del Dashboard de Embargos

Esta guía te explica paso a paso cómo crear el instalador ejecutable del Dashboard de Análisis de Embargos Bancarios.

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

1. **Python 3.8 o superior** (recomendado: Python 3.10)
2. **PyInstaller** - Para crear el ejecutable
   ```bash
   pip install pyinstaller
   ```
3. **Inno Setup Compiler** - Para crear el instalador Windows
   - Descarga desde: https://jrsoftware.org/isinfo.php
   - Instala la versión más reciente (6.x o superior)

## 🔧 Paso 1: Crear el Ejecutable (.exe)

### 1.1. Preparar el Entorno

1. Abre una terminal (PowerShell o CMD) en la carpeta del proyecto
2. Activa el entorno virtual si lo tienes:
   ```bash
   .\venv\Scripts\activate
   ```
3. Verifica que todas las dependencias estén instaladas:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

### 1.2. Ejecutar el Script de Construcción

Ejecuta el script `build_executable.py`:

```bash
python build_executable.py
```

**⏱️ Tiempo estimado:** 5-15 minutos (depende de tu computadora)

### 1.3. Verificar el Ejecutable

Una vez completado, deberías encontrar el ejecutable en:
```
dist\DashboardEmbargos.exe
```

**⚠️ Importante:**
- Si el ejecutable anterior está en uso, ciérralo primero
- Si aparece un error de "Acceso denegado", cierra cualquier proceso relacionado

### 1.4. Probar el Ejecutable (Opcional pero Recomendado)

Antes de crear el instalador, prueba que el ejecutable funcione:

1. Ejecuta `dist\DashboardEmbargos.exe`
2. Verifica que la interfaz se abra correctamente
3. Prueba seleccionar un archivo CSV y procesarlo

## 📦 Paso 2: Crear el Instalador con Inno Setup

### 2.1. Abrir Inno Setup Compiler

1. Abre **Inno Setup Compiler**
2. Ve a: **File → Open**
3. Selecciona el archivo: `installer_setup.iss`

### 2.2. Verificar la Configuración

El archivo `installer_setup.iss` ya está configurado con:
- Nombre de la aplicación: "Dashboard de Embargos Bancarios"
- Versión: 2.0
- Ruta de salida: `installer\DashboardEmbargos_Installer.exe`
- Archivos a incluir: El ejecutable y documentación

**Verifica que:**
- La ruta del ejecutable sea correcta: `dist\DashboardEmbargos.exe`
- Los archivos de documentación existan (si los incluyes):
  - `README.md`
  - `INSTRUCCIONES_EJECUTABLE.md` (opcional)
  - `INSTRUCCIONES_CSV.txt` (opcional)

### 2.3. Compilar el Instalador

1. En Inno Setup, haz clic en el botón **Build → Compile** (o presiona `F9`)
2. Espera a que termine la compilación
3. El instalador se generará en: `installer\DashboardEmbargos_Installer.exe`

**⏱️ Tiempo estimado:** 1-3 minutos

### 2.4. Verificar el Instalador

1. Ve a la carpeta `installer`
2. Deberías ver: `DashboardEmbargos_Installer.exe`
3. **Prueba el instalador:**
   - Ejecuta el instalador en una máquina de prueba
   - Verifica que instale correctamente
   - Prueba que la aplicación funcione después de la instalación

## 🚀 Proceso Completo desde la Consola

### Método Automático (Recomendado)

He creado scripts que automatizan todo el proceso:

**Windows (PowerShell):**
```powershell
.\crear_instalador.ps1
```

**Windows (CMD/Batch):**
```cmd
crear_instalador.bat
```

Estos scripts:
1. ✅ Crean el ejecutable automáticamente
2. ✅ Buscan Inno Setup en ubicaciones comunes
3. ✅ Compilan el instalador
4. ✅ Verifican que todo se haya creado correctamente

### Método Manual (Paso a Paso)

Si prefieres hacerlo manualmente:

```bash
# 1. Activar entorno virtual (si aplica)
.\venv\Scripts\activate

# 2. Instalar dependencias (si es necesario)
pip install -r requirements.txt
pip install pyinstaller

# 3. Crear el ejecutable
python build_executable.py

# 4. Crear el instalador con Inno Setup desde la consola
# PowerShell:
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer_setup.iss"

# O CMD:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_setup.iss
```

**Nota:** Ajusta la ruta de ISCC.exe según tu instalación de Inno Setup.

## 📝 Notas Importantes

### Sobre el Ejecutable

- **Tamaño:** El ejecutable puede ser grande (100-300 MB) porque incluye todas las dependencias de Python
- **Autónomo:** No requiere Python instalado en el sistema destino
- **Dependencias incluidas:** Streamlit, pandas, numpy, plotly, scikit-learn, xgboost

### Sobre el Instalador

- **Permisos:** El instalador requiere permisos de administrador
- **Ubicación de instalación:** Por defecto instala en `Program Files`
- **Datos del usuario:** Los archivos CSV se guardan en `AppData\Roaming\DashboardEmbargos\datos`

### Solución de Problemas

#### Error: "Acceso denegado" al crear el ejecutable
- Cierra `DashboardEmbargos.exe` si está ejecutándose
- Cierra cualquier dashboard de Streamlit abierto
- Cierra el Administrador de Tareas si muestra procesos relacionados

#### Error: "No se encontró el ejecutable"
- Verifica que `dist\DashboardEmbargos.exe` exista
- Asegúrate de que el script `build_executable.py` se ejecutó sin errores

#### Error en Inno Setup: "Archivo no encontrado"
- Verifica que `dist\DashboardEmbargos.exe` exista
- Revisa las rutas en `installer_setup.iss`
- Asegúrate de que los archivos de documentación existan (si los incluyes)

#### El instalador se crea pero la aplicación no funciona
- Verifica que el ejecutable funcione antes de crear el instalador
- Revisa los logs en `AppData\Roaming\DashboardEmbargos\datos\streamlit_*.log`
- Asegúrate de que todas las dependencias estén incluidas en el ejecutable

## 📂 Estructura de Archivos Después de la Compilación

```
proyecto/
├── dist/
│   └── DashboardEmbargos.exe          ← Ejecutable creado
├── build/                               ← Archivos temporales (se puede eliminar)
├── installer/
│   └── DashboardEmbargos_Installer.exe ← Instalador final
├── build_executable.py                  ← Script para crear .exe
├── installer_setup.iss                  ← Script de Inno Setup
└── ...
```

## ✅ Checklist Final

Antes de distribuir el instalador, verifica:

- [ ] El ejecutable se creó correctamente (`dist\DashboardEmbargos.exe`)
- [ ] El ejecutable funciona correctamente (prueba local)
- [ ] El instalador se compiló sin errores
- [ ] El instalador instala correctamente en una máquina de prueba
- [ ] La aplicación funciona después de la instalación
- [ ] Los archivos CSV se pueden procesar correctamente
- [ ] Los dashboards se abren correctamente

## 🎯 Distribución

Una vez que el instalador esté listo y probado:

1. **Ubicación del instalador:** `installer\DashboardEmbargos_Installer.exe`
2. **Tamaño esperado:** 150-400 MB (depende de las dependencias)
3. **Requisitos del sistema destino:**
   - Windows 7 o superior (64-bit recomendado)
   - No requiere Python instalado
   - No requiere dependencias adicionales

## 📞 Soporte

Si encuentras problemas al crear el instalador:

1. Revisa los mensajes de error en la consola
2. Verifica que todos los requisitos estén instalados
3. Asegúrate de que no haya procesos bloqueando archivos
4. Revisa los logs si la aplicación no funciona después de instalar

---

**Última actualización:** 2024
**Versión del instalador:** 2.0

