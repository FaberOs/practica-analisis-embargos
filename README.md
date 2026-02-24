<p align="center">
  <img src="assets/HeroImage.png" alt="Dashboard de Análisis de Embargos Bancarios" width="100%"/>
</p>

# Dashboard de Análisis de Embargos Bancarios

## Descripción del Proyecto

Sistema integral de consolidación, análisis exploratorio, modelado predictivo y distribución de oficios bancarios (embargos, desembargos y requerimientos) para el sector financiero colombiano, desarrollado con Python, Streamlit, XGBoost y metodología CRISP-DM.

El proyecto nace de la necesidad de las áreas legales, de riesgos y TI de organizar, estandarizar y anticipar la carga operativa mensual de embargos bancarios. A partir de archivos CSV semestrales extraídos de la base de datos, el sistema ejecuta un pipeline completo de ETL, entrenamiento de modelos de machine learning (regresión y clasificación), generación de predicciones y visualización interactiva mediante dos dashboards especializados. Todo se empaqueta en un ejecutable autónomo con instalador para Windows, sin requerir Python ni dependencias adicionales en el equipo del usuario final.

### ¿Qué hace este proyecto?

1. **Consolida** múltiples CSVs semestrales en un dataset mensual limpio y estandarizado
2. **Entrena** modelos XGBoost de regresión (predicción de volumen de oficios y demandados) y clasificación (tipo de embargo, estado, cliente/no cliente)
3. **Genera predicciones** a 12 meses con intervalos de confianza y niveles de certeza
4. **Visualiza** resultados en dashboards interactivos con filtros, KPIs, gráficas Plotly y tablas exportables
5. **Distribuye** como ejecutable Windows independiente con instalador profesional

### Casos de Uso

- Anticipar el volumen mensual de embargos y oficios por ciudad, banco y entidad remitente
- Detectar estacionalidad y anomalías en los datos históricos
- Evaluar la precisión de los modelos con métricas de validación (MAE, RMSE, MAPE, F1-score)
- Visualizar matrices de confusión y rankings relevantes para la operación
- Distribuir como herramienta lista para usar sin requerir Python instalado

---

## Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Características Principales](#características-principales)
- [Instalación y Requisitos](#instalación-y-requisitos)
- [Uso Rápido](#uso-rápido)
- [Uso del Ejecutable](#uso-del-ejecutable)
- [Crear el Ejecutable](#crear-el-ejecutable)
- [Crear el Instalador](#crear-el-instalador)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Tests](#tests)
- [Solución de Problemas](#solución-de-problemas)
- [Referencias](#referencias)

---

## Características Principales

### Dashboards Interactivos

- **Dashboard de Embargos** (~1,600 líneas): Análisis exploratorio con 6 filtros combinables (banco, ciudad, estado, tipo, mes, tipo de documento), KPIs dinámicos, Top 10 (entidades, ciudades, funcionarios, remitentes), gráficas de distribución y evolución mensual, búsqueda por texto y exportación a Excel
- **Dashboard de Predicciones** (~1,450 líneas): Predicciones futuras con bandas de confianza, validación histórica (real vs predicción), métricas de error (MAE, RMSE, MAPE), matrices de confusión interactivas con análisis automático de patrones de confusión, y tooltips contextuales para cada métrica

### Pipeline de Machine Learning

- **Regresión XGBoost**: Predicción de volumen de oficios y demandados por mes con features temporales y variables de rezago
- **Clasificación XGBoost**: Modelos para categorización de embargos (tipo, estado, cliente/no cliente) con matrices de confusión serializadas
- **Validación robusta**: Backtesting con último año conocido, métricas completas (MAE, RMSE, R², precisión, recall, F1-score)
- **Predicciones a 12 meses**: Con intervalos de confianza al 95% y niveles de certeza (Alta, Media, Baja)

### Interfaz de Orquestación

- **Launcher GUI (Tkinter)**: Hub central para seleccionar CSVs, monitorear el estado de archivos generados, lanzar dashboards y recalcular modelos
- **Detección automática de puertos**: Los dashboards Streamlit se lanzan en puertos disponibles sin conflictos
- **Compatibilidad dual**: Funciona idéntico en modo desarrollo (scripts) y modo producción (ejecutable PyInstaller)

### Distribución

- **Ejecutable independiente**: Un solo archivo `.exe` que incluye Python, Streamlit, pandas, Plotly, scikit-learn, XGBoost y openpyxl
- **Instalador Windows**: Generado con Inno Setup, con accesos directos y desinstalador automático
- **Procesamiento automático**: Solo necesitas el CSV original de la BD, el pipeline procesa todo
- **Recálculo fácil**: Botón para regenerar todos los archivos con datos nuevos

---

## Instalación y Requisitos

### Requisitos del Sistema

- **Python 3.8 o superior** (solo para desarrollo)
- **Windows 10 o superior** (para ejecutables)
- **4 GB RAM mínimo** (8 GB recomendado)
- **500 MB espacio en disco** (para ejecutables)

### Dependencias (desarrollo)

```
streamlit
pandas
numpy
plotly
scikit-learn
xgboost
openpyxl
```

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

1. **Descargar el instalador** `DashboardEmbargos_Installer.exe` desde la carpeta `installer/`
2. **Ejecutar el instalador** y seguir el asistente (se instala en `Program Files\Dashboard de Embargos Bancarios`)
3. **¡Listo!** No se requiere Python ni dependencias adicionales

---

## Uso Rápido

### Para Usuarios Finales (Ejecutable)

1. **Ejecutar** `DashboardEmbargos.exe` (desde el menú de inicio o escritorio)
2. **Seleccionar** el/los archivo(s) CSV original(es) de la BD (con años en el nombre, por semestres)
   - Ejemplo: `consulta detalle embargos-2023-01.csv`, `consulta detalle embargos-2024-02.csv`
3. **Iniciar** el dashboard deseado:
   - **Dashboard de Embargos**: Análisis exploratorio
   - **Dashboard de Predicciones**: Modelos ML y predicciones
4. El pipeline **procesará automáticamente** los datos y generará los archivos necesarios
5. Los dashboards se abrirán en el navegador con los datos procesados

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

Puedes usarlo directamente desde ahí o copiarlo a otra ubicación (por ejemplo, Escritorio).

### Archivos CSV Necesarios

**IMPORTANTE**: El ejecutable **NO** requiere archivos CSV pre-generados. Solo necesitas:

- **CSV original de la BD**: Archivos semestrales con años en el nombre
  - Ejemplo: `consulta detalle embargos-2023-01.csv`
  - Ejemplo: `consulta detalle embargos-2024-02.csv`

El pipeline procesará automáticamente estos archivos y generará:
- `embargos_consolidado_mensual.csv` — Dataset consolidado mensual
- `predicciones_oficios_validacion.csv` — Backtesting oficios
- `predicciones_oficios_futuro.csv` — Predicciones a 12 meses (oficios)
- `predicciones_demandados_validacion.csv` — Backtesting demandados
- `predicciones_demandados_futuro.csv` — Predicciones a 12 meses (demandados)
- `resultados_clasificaciones.csv` — Métricas y matrices de confusión

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
- **Menú interactivo**: Interfaz gráfica Tkinter para seleccionar CSV y dashboards
- **Portable**: Un solo archivo ejecutable
- **Completo**: Incluye todos los módulos necesarios (Streamlit, pandas, Plotly, scikit-learn, XGBoost, openpyxl)
- **Procesamiento automático**: Solo necesitas el CSV original de la BD

### Archivos Empaquetados en el Ejecutable

- `launcher.py` — Punto de entrada (GUI Tkinter)
- `dashboard_embargos.py` — Dashboard exploratorio
- `dashboard_predicciones.py` — Dashboard de predicciones
- `dashboard_styles.py` — Estilos CSS centralizados
- `procesar_modelo.py` — Pipeline ETL + ML
- `utils_csv.py` — Abstracción de rutas
- `ob.ico` — Icono de la aplicación
- DLL de XGBoost y todas las dependencias de Python

### Solución de Problemas al Compilar

| Problema | Solución |
|---|---|
| PyInstaller no encontrado | `pip install pyinstaller` |
| Módulo no encontrado | `pip install -r requirements.txt` |
| Acceso denegado | Cierra el `.exe` y los dashboards abiertos, reintenta |
| Ejecutable muy grande | Es normal (200-500 MB), incluye Python completo y librerías |

---

## Crear el Instalador

### Requisitos Previos

1. **Inno Setup Compiler** (gratuito) — Descargar desde: https://jrsoftware.org/isinfo.php
2. **Ejecutable creado** — `dist\DashboardEmbargos.exe` debe existir

### Método Rápido

```powershell
# Usando el script de PowerShell
.\construccion\crear_instalador.ps1

# O directamente con Inno Setup
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "construccion\installer_setup.iss"
```

**Tiempo estimado:** 2-5 minutos
**Resultado:** `installer\DashboardEmbargos_Installer.exe`

### Contenido del Instalador

- `DashboardEmbargos.exe` — Ejecutable principal (autónomo)
- Carpeta `datos` con instrucciones
- Accesos directos en escritorio y menú de inicio
- Desinstalador automático
- Soporte para español e inglés

> **Nota:** Los archivos CSV NO se incluyen. El usuario solo necesita el CSV original de la BD.

---

## Estructura del Proyecto

```
practica-analisis-embargos/
│
├── 📊 src/dashboards/                     # Dashboards Streamlit
│   ├── __init__.py
│   ├── dashboard_embargos.py              # Dashboard exploratorio (~1,600 líneas)
│   ├── dashboard_predicciones.py          # Dashboard de predicciones (~1,450 líneas)
│   ├── dashboard_styles.py               # CSS centralizado (paleta corporativa, ~450 líneas)
│   └── dashboard_tabs_futuro.py           # Componentes adicionales de tabs
│
├── 🤖 src/pipeline_ml/                    # Pipeline de Machine Learning
│   ├── __init__.py
│   ├── procesar_modelo.py                 # ETL + entrenamiento + predicción (~870 líneas)
│   └── modelos_ml_embargos.ipynb          # Notebook experimental (desarrollo)
│
├── 🎛️ src/orquestacion/                   # Orquestación y utilidades
│   ├── __init__.py
│   ├── launcher.py                        # GUI Tkinter - hub principal (~1,580 líneas)
│   └── utils_csv.py                       # Abstracción de rutas dev/exe (~210 líneas)
│
├── 🧪 tests/                              # Tests y validación
│   ├── __init__.py
│   ├── test_dashboard_load.py             # Validación de carga de CSV y columnas
│   ├── test_matrices_load.py              # Deserialización de matrices de confusión JSON
│   ├── test_predicciones_futuras.py       # Test end-to-end del pipeline completo
│   └── generar_evidencias_validacion.py   # Genera evidencias de backtesting (~550 líneas)
│
├── 📦 construccion/                       # Herramientas de construcción
│   ├── build_executable.py                # Script de compilación PyInstaller
│   ├── DashboardEmbargos.spec             # Configuración PyInstaller (auto-generado)
│   ├── installer_setup.iss                # Configuración Inno Setup
│   ├── crear_instalador.bat               # Script batch para crear instalador
│   └── crear_instalador.ps1               # Script PowerShell para crear instalador
│
├── 📝 docs/                               # Documentación técnica
│   ├── INFORME_PROYECTO_DASHBOARD_EMBARGOS.md
│   ├── ANALISIS_COLUMNAS.md
│   ├── EVIDENCIAS_VALIDACION.md
│   └── GUIA_CREAR_INSTALADOR.md
│
├── 🖼️ assets/                              # Recursos gráficos
│   └── HeroImage.png                      # Imagen de portada del proyecto
│
├── 📁 datos/                              # Datos generados (output, no versionados)
├── 📦 dist/                               # Ejecutable compilado (no versionado)
├── 📦 installer/                          # Instalador compilado (no versionado)
│
├── ob.ico                                 # Icono de la aplicación
├── README.md                              # Este archivo
├── requirements.txt                       # Dependencias Python
└── .gitignore                             # Reglas de exclusión de Git
```

### Archivos Necesarios para el Ejecutable

- `src/orquestacion/launcher.py` — Punto de entrada
- `src/dashboards/dashboard_embargos.py`, `dashboard_predicciones.py`, `dashboard_styles.py`
- `src/pipeline_ml/procesar_modelo.py`
- `src/orquestacion/utils_csv.py`
- Todos se empaquetan automáticamente dentro del ejecutable

### Archivos Solo para Desarrollo

- `construccion/` — Scripts de compilación y configuración del instalador
- `src/pipeline_ml/modelos_ml_embargos.ipynb` — Notebook de experimentación
- `build/` — Archivos temporales de PyInstaller (se puede eliminar)
- `venv/` — Entorno virtual (no versionado)

---

## Tests

El proyecto incluye tests de validación en la carpeta `tests/`:

| Test | Descripción |
|---|---|
| `test_dashboard_load.py` | Verifica la carga correcta de CSVs con múltiples codificaciones y valida columnas críticas |
| `test_matrices_load.py` | Comprueba la deserialización de matrices de confusión almacenadas como JSON en el CSV |
| `test_predicciones_futuras.py` | Test end-to-end: ejecuta el pipeline completo y verifica que se generen los 5 archivos de salida con columnas correctas |
| `generar_evidencias_validacion.py` | Genera evidencias de backtesting con matplotlib: gráficas real vs predicción, métricas de error y exporta estadísticas a JSON |

```bash
# Ejecutar tests
python tests/test_dashboard_load.py
python tests/test_matrices_load.py
python tests/test_predicciones_futuras.py
```

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
1. Recompila el ejecutable con `python construccion/build_executable.py`
2. El script incluye automáticamente las DLLs de XGBoost

### El dashboard no muestra datos

**Solución:**
1. Verifica que el procesamiento se haya completado correctamente
2. Usa el botón "Recalcular Archivos" para regenerar los datos
3. Verifica que el CSV original tenga el formato correcto

### El ejecutable no inicia

**Solución:**
1. Si Windows muestra advertencia de seguridad, haz clic en "Más información" → "Ejecutar de todas formas"
2. Prueba ejecutar desde la línea de comandos para ver errores detallados

### Los archivos de predicciones no se generan

**Solución:**
1. Esto es normal si solo tienes datos de 1 año
2. Los modelos de regresión requieren al menos 2 años de datos para entrenarse
3. El dashboard de embargos funcionará con solo el archivo consolidado

---

## Referencias

- Guía CRISP-DM para predicción de embargos bancarios
- Documentación XGBoost: https://xgboost.readthedocs.io/
- Documentación Streamlit: https://docs.streamlit.io/
- Documentación PyInstaller: https://pyinstaller.org/
- Documentación Inno Setup: https://jrsoftware.org/isinfo.php
- Géron, A. *Hands-on Machine Learning with Scikit-Learn, Keras, and TensorFlow* (O'Reilly, 2019)
- Raschka, S.; Mirjalili, V. *Python Machine Learning* (Packt, 2019)

---

## Licencia

MIT License. Desarrollado por Faber Ospina.

---

## Contribuciones

Las contribuciones son bienvenidas:

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

**Última actualización:** Febrero 2026
**Versión:** 2.2
**Estado:** Producción
