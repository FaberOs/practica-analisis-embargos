# Guía: Cómo Crear el Instalador del Dashboard de Embargos

Esta guía te explica paso a paso cómo crear el instalador ejecutable del Dashboard de Análisis de Embargos Bancarios.

## 🚀 Método Rápido (Recomendado)

Si quieres crear el instalador de forma automática, usa uno de estos scripts desde la carpeta `construccion/`:

### Windows (PowerShell) - Recomendado:
```powershell
cd construccion
.\crear_instalador.ps1
```

### Windows (CMD/Batch):
```cmd
cd construccion
crear_instalador.bat
```

Estos scripts automatizan todo:
1. ✅ Verifican que Python y PyInstaller estén instalados
2. ✅ Crean el ejecutable (.exe)
3. ✅ Buscan Inno Setup automáticamente
4. ✅ Compilan el instalador final

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

1. **Python 3.8 o superior** (recomendado: Python 3.10+)
2. **PyInstaller** - Para crear el ejecutable
   ```bash
   pip install pyinstaller
   ```
3. **Inno Setup Compiler** - Para crear el instalador Windows
   - Descarga desde: https://jrsoftware.org/isinfo.php
   - Instala la versión más reciente (6.x o superior)

---

## 📁 Estructura del Proyecto

```
practica-analisis-embargos/
├── src/
│   ├── dashboards/           # Dashboards de Streamlit
│   ├── orquestacion/         # Launcher y utilidades
│   └── pipeline_ml/          # Modelos de ML
├── construccion/             # ← Archivos de construcción
│   ├── build_executable.py   # Script para crear .exe
│   ├── installer_setup.iss   # Script de Inno Setup
│   ├── crear_instalador.ps1  # Automatización PowerShell
│   ├── crear_instalador.bat  # Automatización CMD
│   └── DashboardEmbargos.spec
├── datos/                    # Archivos CSV
├── docs/                     # Documentación
├── dist/                     # ← Aquí se genera el .exe
├── installer/                # ← Aquí se genera el instalador
└── ...
```

---

## 🔧 Método Manual (Paso a Paso)

### Paso 1: Crear el Ejecutable (.exe)

#### 1.1. Preparar el Entorno

1. Abre una terminal (PowerShell o CMD) en la carpeta raíz del proyecto
2. Activa el entorno virtual si lo tienes:
   ```bash
   .\venv\Scripts\activate
   ```
3. Verifica que todas las dependencias estén instaladas:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

#### 1.2. Ejecutar el Script de Construcción

```bash
python construccion/build_executable.py
```

**Tiempo estimado:** 5-15 minutos (depende de tu computadora)

#### 1.3. Verificar el Ejecutable

Una vez completado, deberías encontrar el ejecutable en:
```
dist\DashboardEmbargos.exe
```

**Importante:**
- Si el ejecutable anterior está en uso, ciérralo primero
- Si aparece un error de "Acceso denegado", cierra cualquier proceso relacionado

#### 1.4. Probar el Ejecutable (Opcional pero Recomendado)

Antes de crear el instalador, prueba que el ejecutable funcione:

1. Ejecuta `dist\DashboardEmbargos.exe`
2. Verifica que la interfaz se abra correctamente
3. Prueba las funciones básicas

---

### Paso 2: Crear el Instalador con Inno Setup

#### 2.1. Abrir Inno Setup Compiler

1. Abre **Inno Setup Compiler**
2. Ve a: **File → Open**
3. Navega a la carpeta `construccion/`
4. Selecciona el archivo: `installer_setup.iss`

#### 2.2. Compilar el Instalador

1. Haz clic en **Build → Compile** (o presiona `F9`)
2. Espera a que termine la compilación
3. El instalador se generará en: `installer\DashboardEmbargos_Installer.exe`

**Tiempo estimado:** 1-3 minutos

#### 2.3. Compilar desde la Consola (Alternativa)

Si prefieres usar la línea de comandos:

```powershell
# PowerShell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "construccion\installer_setup.iss"
```

```cmd
# CMD
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" construccion\installer_setup.iss
```

---

## ✅ Checklist Final

Antes de distribuir el instalador, verifica:

- [ ] El ejecutable se creó correctamente (`dist\DashboardEmbargos.exe`)
- [ ] El ejecutable funciona correctamente (prueba local)
- [ ] El instalador se compiló sin errores (`installer\DashboardEmbargos_Installer.exe`)
- [ ] El instalador instala correctamente en una máquina de prueba
- [ ] La aplicación funciona después de la instalación

---

## 🔍 Solución de Problemas

### Error: "Acceso denegado" al crear el ejecutable
- Cierra `DashboardEmbargos.exe` si está ejecutándose
- Cierra cualquier dashboard de Streamlit abierto
- Cierra el Administrador de Tareas si muestra procesos relacionados

### Error: "No se encontró el ejecutable"
- Verifica que `dist\DashboardEmbargos.exe` exista
- Asegúrate de que el script `build_executable.py` se ejecutó sin errores

### Error en Inno Setup: "Archivo no encontrado"
- Verifica que `dist\DashboardEmbargos.exe` exista
- Asegúrate de ejecutar Inno Setup desde la ruta correcta
- Revisa que el archivo `ob.ico` exista en la raíz del proyecto

### El instalador se crea pero la aplicación no funciona
- Verifica que el ejecutable funcione antes de crear el instalador
- Prueba ejecutar el launcher directamente: `python src/orquestacion/launcher.py`

### PowerShell no permite ejecutar scripts
Si ves un error de "ejecución de scripts deshabilitada":
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📦 Distribución

Una vez que el instalador esté listo y probado:

1. **Ubicación del instalador:** `installer\DashboardEmbargos_Installer.exe`
2. **Tamaño esperado:** 150-400 MB (incluye todas las dependencias)
3. **Requisitos del sistema destino:**
   - Windows 7 o superior (64-bit recomendado)
   - No requiere Python instalado
   - No requiere dependencias adicionales

---

## 📝 Notas Importantes

### Sobre el Ejecutable
- **Tamaño:** El ejecutable puede ser grande (100-300 MB) porque incluye todas las dependencias de Python
- **Autónomo:** No requiere Python instalado en el sistema destino
- **Dependencias incluidas:** Streamlit, pandas, numpy, plotly, scikit-learn, xgboost

### Sobre el Instalador
- **Permisos:** El instalador requiere permisos de administrador
- **Ubicación de instalación:** Por defecto instala en `Program Files`
- **Datos del usuario:** Los archivos CSV se guardan en la carpeta `datos` dentro del directorio de instalación

---

## 🆘 Soporte

Si encuentras problemas al crear el instalador:

1. Revisa los mensajes de error en la consola
2. Verifica que todos los requisitos estén instalados
3. Asegúrate de que no haya procesos bloqueando archivos
4. Consulta la documentación en la carpeta `docs/`

---

**Última actualización:** Diciembre 2025  
**Versión del instalador:** 2.0

