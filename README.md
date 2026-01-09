# Dashboard de Análisis de Embargos Bancarios

Sistema completo para la consolidación, visualización interactiva y modelado predictivo de oficios bancarios (embargos, desembargos y requerimientos) usando Python, Streamlit y Machine Learning.

## Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Características Principales](#características-principales)
- [Instalación y Requisitos](#instalación-y-requisitos)
- [Uso Rápido](#uso-rápido)
- [Uso del Ejecutable](#uso-del-ejecutable)
- [Crear el Ejecutable](#crear-el-ejecutable)
- [Crear el Instalador](#crear-el-instalador)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Solución de Problemas](#solución-de-problemas)
- [Referencias](#referencias)

---

## Descripción del Proyecto

Este proyecto aborda la necesidad de organizar, estandarizar y predecir la carga operativa de embargos bancarios mensuales en el sector financiero colombiano. Aplica la metodología CRISP-DM para limpiar y consolidar los datos históricos de oficios bancarios, genera dashboards interactivos para análisis exploratorio y entrena modelos de machine learning para pronóstico y clasificación.

### Casos de Uso

- Anticipar el volumen mensual de embargos y otros oficios por ciudad, banco y entidad remitente
- Detectar estacionalidad y anomalías en los datos
- Visualizar métricas y rankings relevantes para áreas legales, de riesgos y TI
- Distribuir como ejecutable independiente sin requerir Python instalado

---

## Características Principales

### Dashboards Interactivos

- **Dashboard de Embargos**: Análisis exploratorio con filtros interactivos, KPIs, gráficas y tablas detalladas
- **Dashboard de Predicciones**: Visualización de modelos ML, métricas de desempeño y comparación de predicciones vs reales

### Modelos de Machine Learning

- **Regresión XGBoost**: Predicción de volumen de oficios y demandados por mes
- **Clasificación**: Modelos para categorización de embargos (tipo, estado, cliente/no cliente)
- **Métricas completas**: MAE, RMSE, R², precisión, recall, F1-score

### Distribución

- **Ejecutable independiente**: No requiere Python instalado
- **Instalador Windows**: Instalación profesional con Inno Setup
- **Procesamiento automático**: Solo necesitas el CSV original de la BD, el modelo procesa automáticamente
- **Recálculo fácil**: Botón para regenerar archivos con nuevos datos

---

## Instalación y Requisitos

### Requisitos del Sistema

- **Python 3.8 o superior** (solo para desarrollo)
- **Windows 10 o superior** (para ejecutables)
- **4 GB RAM mínimo** (8 GB recomendado)
- **500 MB espacio en disco** (para ejecutables)

### Instalación para Desarrollo

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/FaberOs/practica-analisis-embargos.git
   cd practica-analisis-embargos
   ```

2. **Crear y activar entorno virtual:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   pip install jupyter  # Para ejecutar el notebook (opcional)
   ```

### Instalación para Usuario Final

1. **Descargar el instalador:**
   - `DashboardEmbargos_Installer.exe` desde la carpeta `installer\`

2. **Ejecutar el instalador:**
   - Seguir el asistente de instalación
   - El programa se instalará en `Program Files\Dashboard de Embargos Bancarios`

3. **¡Listo!** No se requiere Python ni dependencias adicionales.

---

## Uso Rápido

### Para Usuarios Finales (Ejecutable)

1. **Ejecutar** `DashboardEmbargos.exe` (desde el menú de inicio o escritorio)
2. **Seleccionar** el/los archivo(s) CSV original(es) de la BD (con años en el nombre, por semestres)
   - Ejemplo: `consulta detalle embargos-2023-01.csv`
3. **Iniciar** el dashboard deseado:
   - **Dashboard de Embargos**: Análisis exploratorio
   - **Dashboard de Predicciones**: Modelos ML y predicciones
4. El modelo **procesará automáticamente** los datos y generará los archivos necesarios
5. Los dashboards se abrirán con los datos procesados

### Para Desarrolladores

#### Opción 1: Usando el Launcher (Recomendado)

```bash
python src/orquestacion/launcher.py
```

Selecciona el dashboard que deseas ejecutar desde la interfaz gráfica.

#### Opción 2: Ejecutar Directamente

```bash
# Dashboard de Embargos
streamlit run src/dashboards/dashboard_embargos.py

# Dashboard de Predicciones
streamlit run src/dashboards/dashboard_predicciones.py
```

Los dashboards se abrirán automáticamente en tu navegador en `http://localhost:8501` y `http://localhost:8502`.

---

## Uso del Ejecutable

### Ubicación del Ejecutable

El ejecutable se encuentra en: **`dist\DashboardEmbargos.exe`**

Puedes:
- **Usarlo directamente desde ahí**, o
- **Copiarlo a otra ubicación** (por ejemplo, Escritorio o una carpeta de instalación)

### Archivos CSV Necesarios

**IMPORTANTE**: El ejecutable **NO** requiere archivos CSV pre-generados. Solo necesitas:

- **CSV original de la BD**: Archivos con años en el nombre (por semestres)
  - Ejemplo: `consulta detalle embargos-2023-01.csv`
  - Ejemplo: `consulta detalle embargos-2023-02.csv`

El modelo procesará automáticamente estos archivos y generará:
- `embargos_consolidado_mensual.csv`
- `predicciones_oficios_por_mes.csv`
- `predicciones_demandados_por_mes.csv`
- `resultados_clasificaciones.csv`

### Funcionalidades del Launcher

- **Selección de CSV originales**: Selecciona uno o más archivos CSV de la BD
- **Estado de archivos generados**: Visualiza qué archivos están disponibles (checkboxes)
- **Recalcular archivos**: Botón para regenerar todos los archivos con nuevos datos
- **Iniciar dashboards**: Botones para iniciar cada dashboard
- **Actualizar estado**: Verifica el estado actual de los archivos

### Ubicación de Archivos Generados

Los archivos generados se guardan automáticamente en:
- **Windows**: `C:\Users\[TuUsuario]\AppData\Roaming\DashboardEmbargos\datos\`

No necesitas hacer nada manual, el programa los gestiona automáticamente.

---

## Crear el Ejecutable

### Requisitos Previos

1. **Python 3.8 o superior** instalado
2. **Entorno virtual activado** con todas las dependencias instaladas
3. **PyInstaller** instalado (se instala automáticamente si no está)

### Método Rápido

```powershell
# 1. Activar entorno virtual
.\venv\Scripts\Activate.ps1

# 2. Ejecutar script de construcción
python construccion/build_executable.py
```

**Tiempo estimado:** 5-15 minutos  
**Resultado:** `dist\DashboardEmbargos.exe` (200-500 MB)

### Características del Ejecutable

- **Independiente**: No requiere Python ni dependencias instaladas
- **Menú interactivo**: Interfaz gráfica para seleccionar CSV y dashboards
- **Portable**: Un solo archivo ejecutable
- **Completo**: Incluye todos los módulos necesarios (Streamlit, pandas, plotly, sklearn, xgboost)
- **Procesamiento automático**: Solo necesitas el CSV original de la BD

### Archivos Incluidos en el Ejecutable

El ejecutable incluye automáticamente:
- `launcher.py` - Launcher principal
- `dashboard_embargos.py` - Dashboard de embargos
- `dashboard_predicciones.py` - Dashboard de predicciones
- `procesar_modelo.py` - Script de procesamiento del modelo
- `utils_csv.py` - Utilidades CSV
- Todas las dependencias de Python (pandas, numpy, plotly, streamlit, sklearn, xgboost, etc.)

### Solución de Problemas al Compilar

#### Error: "PyInstaller no encontrado"
```powershell
pip install pyinstaller
```

#### Error: "Módulo no encontrado"
Asegúrate de tener todas las dependencias instaladas:
```powershell
pip install -r requirements.txt
```

#### Error: "Acceso denegado" al compilar
1. Cierra el ejecutable `DashboardEmbargos.exe` si está corriendo
2. Cierra cualquier dashboard de Streamlit que esté abierto
3. Vuelve a ejecutar: `python build_executable.py`

#### El ejecutable es muy grande
Es normal. El ejecutable incluye Python y todas las librerías (200-500 MB).

---

## Crear el Instalador

### Requisitos Previos

1. **Inno Setup Compiler** (gratuito)
   - Descargar desde: https://jrsoftware.org/isinfo.php
   - Instalar la versión más reciente

2. **Ejecutable creado**
   - Asegúrate de haber ejecutado `build_executable.py` primero
   - El archivo `dist\DashboardEmbargos.exe` debe existir

### Método Rápido

```powershell
# Verificar que Inno Setup esté instalado
$innoPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $innoPath) {
    & $innoPath "installer_setup.iss"
} else {
    Write-Host "Inno Setup no encontrado. Instálalo desde: https://jrsoftware.org/isinfo.php"
}
```

**Tiempo estimado:** 2-5 minutos  
**Resultado:** `installer\DashboardEmbargos_Installer.exe`

### Estructura del Instalador

El instalador incluirá:
- `DashboardEmbargos.exe` - El ejecutable principal (incluye todas las dependencias)
- Documentación (README.md)
- Carpeta `datos` con instrucciones
- Accesos directos en el escritorio y menú de inicio
- Desinstalador automático

**NOTA IMPORTANTE:**
- Los archivos CSV NO se incluyen en el instalador
- El usuario solo necesita el CSV original de la BD (con años en el nombre)
- El modelo procesará los datos automáticamente
- El ejecutable es completamente autónomo (no requiere Python instalado)

### Solución de Problemas al Compilar el Instalador

#### Error: "No se encontró ISCC.exe"
- Verifica que Inno Setup esté instalado
- La ruta típica es: `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`

#### Error: "No se encontró DashboardEmbargos.exe"
- Ejecuta primero `build_executable.py`
- Verifica que el archivo exista en `dist\DashboardEmbargos.exe`

#### El instalador tarda mucho tiempo
- Ya está configurado con compresión rápida (`lzma2`)
- Tiempo esperado: 2-5 minutos
- Si tarda más de 10 minutos, verifica que el proceso no esté colgado

---

## Estructura del Proyecto

```
practica-analisis-embargos/
├── 📊 src/dashboards/                     # Dashboards Streamlit
│   ├── __init__.py
│   ├── dashboard_embargos.py              # Dashboard exploratorio (1,700+ líneas)
│   ├── dashboard_predicciones.py          # Dashboard de predicciones y métricas (1,450+ líneas)
│   ├── dashboard_styles.py                # CSS centralizado (paleta corporativa)
│   └── dashboard_tabs_futuro.py           # Componentes adicionales de tabs
│
├── 🤖 src/pipeline_ml/                    # Pipeline de Machine Learning
│   ├── __init__.py
│   ├── procesar_modelo.py                 # ETL + entrenamiento + predicción (866 líneas)
│   └── modelos_ml_embargos.ipynb          # Notebook experimental (desarrollo)
│
├── 🎛️ src/orquestacion/                   # Orquestación y utilidades
│   ├── __init__.py
│   ├── launcher.py                        # GUI Tkinter (hub principal, 1,500+ líneas)
│   └── utils_csv.py                       # Abstracción de rutas (dev vs ejecutable)
│
├── 📁 datos/                              # Datos generados (output)
│   ├── embargos_consolidado_mensual.csv
│   ├── predicciones_oficios_validacion.csv
│   ├── predicciones_oficios_futuro.csv
│   ├── predicciones_demandados_validacion.csv
│   ├── predicciones_demandados_futuro.csv
│   └── resultados_clasificaciones.csv
│
├── 🧪 tests/                              # Tests automatizados
│   ├── __init__.py
│   ├── test_dashboard_load.py             # Validación carga CSV
│   ├── test_matrices_load.py              # Deserialización JSON
│   └── test_predicciones_futuras.py       # Pipeline completo
│
├── 📦 construccion/                       # Herramientas de construcción
│   ├── build_executable.py                # Script PyInstaller
│   ├── DashboardEmbargos.spec             # Configuración PyInstaller
│   └── installer_setup.iss                # Configuración Inno Setup
│
├── 📝 docs/                               # Documentación técnica
│   ├── INFORME_PROYECTO_DASHBOARD_EMBARGOS.md
│   ├── ANALISIS_COLUMNAS.md
│   ├── GUIA_CREAR_INSTALADOR.md
│   └── HISTORIAL_DE_CAMBIOS_Y_MEJORAS.md
│
├── 📦 dist/                               # Distribución (generado)
│   └── DashboardEmbargos.exe              # Ejecutable final
│
├── ob.ico                                 # Icono de la aplicación
├── README.md                              # Este archivo
└── requirements.txt                       # Dependencias Python
```

### Archivos Necesarios para el Ejecutable

- `src/orquestacion/launcher.py` - Punto de entrada
- `src/dashboards/dashboard_embargos.py`, `dashboard_predicciones.py`, `dashboard_styles.py`
- `src/pipeline_ml/procesar_modelo.py`
- `src/orquestacion/utils_csv.py`
- Estos archivos se empaquetan dentro del ejecutable

### Archivos SOLO para Desarrollo

- Scripts de compilación: `construccion/build_executable.py`, `construccion/installer_setup.iss`
- Configuración: `construccion/DashboardEmbargos.spec` (se regenera automáticamente)
- Notebook: `src/pipeline_ml/modelos_ml_embargos.ipynb` (solo para desarrollo)
- Carpeta `build/` - Archivos temporales de PyInstaller (se puede eliminar)
- Carpeta `venv/` - Entorno virtual (solo para desarrollo)

---

## Solución de Problemas

### El ejecutable no encuentra los archivos CSV

**Problema:** El dashboard muestra "No se encontró el archivo: embargos_consolidado_mensual.csv"

**Solución:**
1. Verifica que hayas seleccionado el CSV original de la BD en el launcher
2. Verifica que el procesamiento se haya completado (revisa la ventana de progreso)
3. Los archivos se generan en: `AppData\Roaming\DashboardEmbargos\datos\`
4. Usa el botón "Recalcular Archivos" si es necesario

### Error: "Cannot find XGBoost Library"

**Problema:** El procesamiento falla con error de XGBoost DLL

**Solución:**
1. Recompila el ejecutable con los cambios más recientes
2. El script `build_executable.py` ahora incluye automáticamente las DLLs de XGBoost
3. Ejecuta: `python build_executable.py`

### El dashboard no muestra datos

**Problema:** El dashboard se abre pero muestra "No se encontraron registros"

**Solución:**
1. Verifica que el procesamiento se haya completado correctamente
2. Revisa la ventana de progreso para ver si hubo errores
3. Usa el botón "Recalcular Archivos" para regenerar los datos
4. Verifica que el CSV original tenga el formato correcto

### El ejecutable no inicia

**Problema:** Al hacer doble clic, no pasa nada o aparece un error

**Solución:**
1. Verifica que tengas permisos de ejecución
2. Si Windows muestra una advertencia de seguridad, haz clic en "Más información" y luego "Ejecutar de todas formas"
3. Verifica que no falten dependencias del sistema (normalmente no debería ser necesario)
4. Prueba ejecutar desde la línea de comandos para ver errores

### El procesamiento tarda mucho tiempo

**Problema:** El procesamiento parece estar colgado

**Solución:**
1. El procesamiento puede tardar varios minutos dependiendo del tamaño de los CSV
2. Revisa la ventana de progreso para ver los mensajes
3. Si no hay progreso después de 10 minutos, cancela y verifica los CSV originales
4. Asegúrate de tener al menos 2 años de datos para entrenar los modelos de regresión

### Los archivos de predicciones no se generan

**Problema:** Solo se genera `embargos_consolidado_mensual.csv`, pero no los de predicciones

**Solución:**
1. Esto es normal si solo tienes datos de 1 año
2. Los modelos de regresión requieren al menos 2 años de datos
3. El dashboard de embargos funcionará con solo el archivo consolidado
4. Para obtener predicciones, necesitas datos de múltiples años

---

## Referencias

- Guía CRISP-DM para predicción de embargos bancarios
- Documentación XGBoost: https://xgboost.readthedocs.io/
- Documentación Streamlit: https://docs.streamlit.io/
- Documentación PyInstaller: https://pyinstaller.org/
- Documentación Inno Setup: https://jrsoftware.org/isinfo.php
- Géron, A. Hands-on Machine Learning with Scikit-Learn, Keras, and TensorFlow (O'Reilly, 2019)
- Raschka, S.; Mirjalili, V. Python Machine Learning (Packt, 2019)

---

## Licencia

MIT License. Desarrollado por Faber Ospina

---

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## Soporte

Para problemas o preguntas:

1. Consulta esta documentación
2. Revisa la sección de [Solución de Problemas](#solución-de-problemas)
3. Abre un issue en el repositorio

---

**Última actualización:** 2025-01-XX  
**Versión:** 2.1  
**Estado:** Producción
