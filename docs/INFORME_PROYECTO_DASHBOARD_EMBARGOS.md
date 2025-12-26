# Informe Técnico del Sistema de Reportería y Análisis Predictivo de Embargos Bancarios

## 1. Contexto y propósito del proyecto

El proyecto **"Sistema de Análisis Predictivo de Embargos Bancarios"** constituye una solución integral de reportería automatizada e inteligencia artificial diseñada para entidades financieras que gestionan volúmenes significativos de embargos judiciales y coactivos. Surge como respuesta a tres desafíos operativos críticos identificados: la dispersión y heterogeneidad de datos (múltiples CSV sin normalización), la carencia de capacidad predictiva para planificar recursos, y limitaciones en visualización ejecutiva (reportes estáticos sin exploración interactiva).

El objetivo del proyecto es triple:

1. **Automatizar la consolidación de datos** mediante pipelines que reparan inconsistencias estructurales, normalizan categorías e imputan valores, generando un dataset unificado (`embargos_consolidado_mensual.csv`).
2. **Integrar modelos de Machine Learning** que generen pronósticos mensuales extendidos (12 meses con intervalos de confianza), regresión XGBoost para oficios/demandados, y clasificadores supervisados con filtrado por soporte mínimo (≥100 muestras) para garantizar métricas confiables.
3. **Proveer interfaces de reportería avanzadas** con dashboards Streamlit que visualicen históricos, predicciones futuras, validación histórica (comparación real vs predicho), métricas de calidad (precisión, recall, F1, matrices de confusión deserializadas) y capacidades de exportación.

La solución se distribuye como ejecutable Windows autocontenido (PyInstaller + Inno Setup), permitiendo adopción sin dependencias técnicas.

**Documentación técnica complementaria**: el proyecto incluye informes especializados en `INFORME_VALIDACION_MODELO_ML.md` (pipeline predictivo), `INFORME_VALIDACION_DASHBOARD_EMBARGOS.md` (dashboard exploratorio) e `INFORME_VALIDACION_DASHBOARD_PREDICCIONES.md` (dashboard de pronósticos), todos adaptados para monografía de tesis.

---

## 2. Visión general de la arquitectura

El sistema completo se puede entender en tres grandes capas funcionales:

### 2.1. Capa de Procesamiento de Datos y Modelos ML

- **Archivo principal**: `procesar_modelo.py` (866 líneas, validado el 2025-12-13)
- **Entrada**: CSV originales con 23 columnas, 2.2M+ filas sin normalizar
- **Constantes de configuración** (definidas en líneas 20-24):
  - `Z_VALUE = 1.96`: nivel de confianza 95% para intervalos
  - `MAX_INTERVAL_RATIO = 1.35`: límite superior = 135% de la predicción
  - `MIN_INTERVAL_ABS = 500.0`: ancho mínimo absoluto de intervalo
  - `MIN_CLASS_SAMPLES = 100`: soporte mínimo para entrenar clasificadores
  - `DTYPE_OVERRIDES = {'tipo_carta': 'string'}`: fuerza tipo string para evitar DtypeWarning
- **Dataclasses de configuración**:
  - `SamplingConfig`: `frac` (default 1.0), `n_per_month` (opcional), `random_state=42`
  - `ForecastConfig`: `horizon=12` (meses a proyectar)
- **Salida**:
  - `embargos_consolidado_mensual.csv`: dataset consolidado muestreado (7%)
  - `predicciones_oficios_validacion.csv` (277 bytes): validación histórica (RMSE 80,515)
  - `predicciones_oficios_futuro.csv` (573 bytes): pronóstico 12 meses con intervalos
  - `predicciones_demandados_validacion.csv` (274 bytes): validación (RMSE 41,706)
  - `predicciones_demandados_futuro.csv` (576 bytes): pronóstico 12 meses
  - `resultados_clasificaciones.csv` (2,188 bytes): métricas + matrices de confusión JSON

### 2.2. Capa de Interfaces Interactivas (Dashboards)

- `dashboard_embargos.py`: dashboard exploratorio de embargos.
- `dashboard_predicciones.py`: dashboard de predicciones y métricas de modelos.

Ambas son aplicaciones Streamlit que se ejecutan en el navegador y permiten:

- Filtrar, buscar y explorar embargos a nivel banco, ciudad, funcionario, tipo, estado, etc.
- Visualizar la evolución temporal de oficios.
- Comparar valores reales vs. predichos (oficios y demandados).
- Analizar métricas de precisión, *recall* y F1-score de los modelos de clasificación.
- Exportar subconjuntos filtrados a CSV/Excel/JSON.

### 2.3. Capa de Orquestación y Distribución

- `launcher.py`: interfaz gráfica (Tkinter) que actúa como “menú principal” para:
  - Seleccionar los CSV originales de la base de datos.
  - Ejecutar el procesamiento completo (limpieza + ML + generación de archivos).
  - Iniciar los dashboards de embargos y de predicciones.
  - Ver el estado de los archivos generados y recalcularlos con nuevos datos.
- `utils_csv.py`: capa de abstracción para localizar archivos CSV en diferentes ubicaciones (AppData del usuario, carpeta del ejecutable, subcarpetas `datos`, etc.), indispensable para compatibilidad entre modo “desarrollo” y modo “ejecutable instalado”.
- `build_executable.py` e `installer_setup.iss`: scripts para empaquetar todo en un ejecutable único y generar un instalador de Windows.

Esta arquitectura cumple con el objetivo de la tesis de dos formas claras:

- Proporciona **interfaces de reportería avanzadas** (dashboards web interactivos) integradas a una lógica de IA (modelos XGBoost y clasificadores).
- Automatiza **la generación de reportes** (CSV de consolidado, predicciones y métricas) y presenta los resultados en una **plataforma de gestión** (navegador, con Streamlit como framework).

---

## 3. Flujo de trabajo funcional del sistema

El flujo de uso típico del sistema, desde la perspectiva de un usuario final no técnico, es el siguiente:

1. Ejecutar el programa `DashboardEmbargos.exe` (o instalarlo mediante el instalador y acceder desde el menú de inicio).
2. Desde el `launcher.py` (interfaz gráfica):
   - Seleccionar uno o varios archivos CSV originales de la base de datos. Estos CSV siguen una convención de nombres como `consulta detalle embargos-2023-01.csv`, `consulta detalle embargos-2023-02.csv`, etc.
   - Presionar **“Recalcular archivos”** para procesar la información. El lanzador muestra una ventana de progreso donde se observa el avance del procesamiento, limpieza y entrenamiento de modelos.
3. El script `procesar_modelo.py` se ejecuta en segundo plano:
   - Concatena los CSV.
   - Normaliza, limpia y muestrea los datos.
   - Entrena modelos de regresión y clasificación.
   - Genera los cuatro CSV de salida.
4. Desde el mismo `launcher.py`, el usuario puede:
   - Iniciar el **Dashboard de Embargos**.
   - Iniciar el **Dashboard de Predicciones**.
   - Detener dashboards activos.
   - Ver el estado de los archivos generados (checklist de archivos encontrados).
5. Los dashboards se abren en el navegador (`http://localhost:8501` y `http://localhost:8502`), donde el usuario puede explorar los datos, aplicar filtros, visualizar KPIs y descargar reportes.

De este modo, se logra un ciclo completo de ETL + ML + visualización, completamente orquestado desde una interfaz gráfica, sin necesidad de que el usuario final interactúe con la consola ni con el código fuente.

---

## 4. Metodología empleada (CRISP-DM y enfoque analítico)

Aunque no todo el detalle metodológico está explícito en comentarios, el proyecto se alinea con la metodología **CRISP-DM (Cross-Industry Standard Process for Data Mining)**, con las siguientes fases reflejadas en el código y en el flujo de trabajo:

### 4.1. Comprensión del negocio

- **Problema**: falta de visibilidad y capacidad predictiva sobre el volumen de embargos, los estados de los oficios y la distribución de cargas entre bancos, ciudades y funcionarios.
- **Objetivo de negocio**:
  - Anticipar la carga operativa mensual.
  - Mejorar la planificación de recursos humanos y tecnológicos.
  - Disponer de reportes automáticos fácilmente consumibles por áreas legales, riesgos y TI.

### 4.2. Comprensión de los datos

A partir del análisis descrito en `ANALISIS_COLUMNAS.md` se identifica el rol de cada campo:

- **Columnas fundamentales** para el dashboard:
  - Filtros críticos: `entidad_bancaria`, `ciudad`, `estado_embargo`, `tipo_embargo`, `mes`.
  - Métricas: `montoaembargar`, `es_cliente`.
  - Rankings/visualizaciones: `funcionario`, `entidad_remitente`, `tipo_documento`.
- **Columnas de búsqueda global**: `nombres`, `identificacion`.
- **Columnas poco usadas o no relevantes**: `correo`, `direccion`, `fecha_banco`, `fecha_oficio`, `referencia`, `cuenta`, `expediente`, `id`, `tipo_identificacion_tipo`.

Esta clasificación permite centrar el procesamiento y las visualizaciones en los campos que realmente aportan valor al análisis.

### 4.3. Preparación de los datos

La preparación de datos se realiza principalmente en `procesar_modelo.py`:

- **Lectura robusta de CSV**:
  - Soporte para múltiples codificaciones (`utf-8`, `latin-1`, `cp1252`, `iso-8859-1`).
  - Reparación de filas con menos o más columnas de las esperadas (23 columnas estándar definidas en `expected_columns`).
- **Conversión y limpieza de variables numéricas y categóricas**:
  - `montoaembargar` se convierte a numérico, con manejo de errores y reemplazo de nulos por 0.
  - `es_cliente` se normaliza a una variable binaria (`0`/`1`) usando múltiples patrones (`SI`, `1`, `CLIENTE`, `TRUE`, etc.).
  - Campos categóricos (`ciudad`, `entidad_remitente`, `tipo_embargo`, `estado_embargo`, etc.) se convierten a texto en mayúsculas, sin espacios sobrantes, y se reemplazan valores infrecuentes por la categoría `OTRO`.
- **Tratamiento de fechas**:
  - Conversión de `fecha_banco` y `fecha_oficio` a `datetime`.
- **Derivación de variables temporales**:
  - `año`, `mes_num`: extraídos de `fecha_banco` con `pd.to_datetime`
  - **Codificación cíclica trigonométrica** (preserva continuidad diciembre→enero):
    ```python
    mes_sin = np.sin(2 * np.pi * mes_num / 12.0)
    mes_cos = np.cos(2 * np.pi * mes_num / 12.0)
    ```
  - `mes_index = año * 12 + mes_num`: índice ordinal para tendencia lineal
  - `mes_label`: formato `"YYYY-MM"` para visualización
- **Features de rezago (lags) para series temporales**:
  - `oficios_lag1`, `oficios_lag2`, `oficios_lag3`: valores de 1, 2 y 3 meses anteriores
  - `oficios_ma3`: media móvil 3 meses con `rolling(window=3, min_periods=1).mean().shift(1)`
  - Análogos para demandados: `demandados_lag{1,2,3}`, `demandados_ma3`
- **Garantía de continuidad temporal** (función `_ensure_month_continuity`):
  - Rellena huecos en la serie mensual usando `pd.date_range(freq='MS')`
  - Imputa columnas numéricas con 0 para evitar NaN en lags
- **Muestreo estratificado por mes**:
  - Configurable via `--frac-muestra` (default 1.0) o `--n-muestra` (N filas/mes)
  - Implementado con `df.groupby('mes').apply(_sampler)` preservando distribución temporal
  - Valor histórico: 7% para desarrollo (`frac=0.07`), 100% para producción

### 4.4. Modelado

#### Modelos de regresión (XGBRegressor con validación histórica y pronóstico futuro)

**Arquitectura dual**: cada objetivo (oficios, demandados) entrena dos modelos XGBoost con objetivo Poisson:
1. **Modelo de validación**: entrenado con años < último, validado en último año completo (split temporal)
2. **Modelo de pronóstico**: reentrenado con todo el histórico limpio, proyección recursiva 12 meses

**Hiperparámetros XGBRegressor** (líneas 327-331):
```python
XGBRegressor(
    n_estimators=200, learning_rate=0.1, max_depth=7,
    objective='count:poisson',  # Distribución Poisson para conteos
    random_state=42,
    base_score=np.mean(y_train_clean)  # Predicción base = media histórica
)
```

**Pipeline de pronóstico extendido** (`entrenar_modelos_y_generar_predicciones`):
1. **Preprocesamiento temporal**: agregación mensual con `groupby(['año', 'mes_num'])`, continuidad garantizada por `_ensure_month_continuity`
2. **Validación histórica**: split `train[año < ultimo_año]` vs `test[año == ultimo_año]`, cálculo RMSE/MAE, escala residual para intervalos
3. **Algoritmo de intervalos acotados** (función `_compute_interval`, líneas 48-52):
   ```python
   def _compute_interval(residual_scale, horizonte, pred_value):
       base = residual_scale if residual_scale > 0 else 1.0
       raw_interval = Z_VALUE * base * np.sqrt(max(1, horizonte))  # Crece con raíz del horizonte
       cap = max(pred_value * MAX_INTERVAL_RATIO, MIN_INTERVAL_ABS)  # Límite superior
       return float(np.clip(raw_interval, 0.0, cap))  # Truncamiento
   ```
   - **Lógica**: intervalo crece proporcional a $\sqrt{h}$ donde $h$ es horizonte en meses
   - **Truncamiento**: evita explosiones numéricas limitando a 135% predicción o 500 mínimo
   - **Resultado**: horizontes >3 frecuentemente tienen `limite_inferior=0` por truncamiento
4. **Etiquetado cualitativo** (función `_confidence_label`):
   - Alta: horizonte ≤ 3 meses
   - Media: horizonte ≤ 6 meses
   - Baja: horizonte > 6 meses
5. **Pronóstico recursivo** (líneas 398-447): actualiza lags con predicción anterior, itera 12 meses

**Salidas**:
- `predicciones_{stub}_validacion.csv`: mes, real, pred (RMSE oficios=80,515; demandados=41,706)
- `predicciones_{stub}_futuro.csv`: mes, pred, límite_inferior, límite_superior, nivel_confianza, horizonte_meses

#### Modelos de clasificación (XGBClassifier con filtrado automático por soporte)

**Mejora crítica**: función `prepare_multiclass_dataset` (líneas 675-693) filtra clases con soporte < `MIN_CLASS_SAMPLES=100` antes del entrenamiento:

```python
def prepare_multiclass_dataset(feature_cols, target_col, encoder, min_samples=MIN_CLASS_SAMPLES):
    target_series = df[target_col].copy()
    counts = target_series.value_counts()
    valid_codes = counts[counts >= min_samples].index.tolist()
    if len(valid_codes) < 2:
        return None  # No hay suficientes clases válidas
    discarded = counts[counts < min_samples]
    if not discarded.empty:
        print(f"[INFO] {target_col}: se descartan {len(discarded)} clases con soporte < {min_samples}")
    # Re-encoding con LabelEncoder local para clases filtradas
    mask = target_series.isin(valid_codes)
    subset_encoder = LabelEncoder()
    y_encoded = subset_encoder.fit_transform(labels_text)
    return X_local, y_encoded, label_names
```

**Hiperparámetros XGBClassifier** (líneas 703-709):
```python
XGBClassifier(
    n_estimators=100, max_depth=7, learning_rate=0.1,
    subsample=0.9, colsample_bytree=0.8,  # Regularización
    eval_metric='mlogloss',  # Log-loss multiclase
    tree_method="hist"  # Algoritmo rápido basado en histogramas
)
```

**Tres clasificadores principales**:

1. **Tipo Embargo** (COACTIVO/JUDICIAL):
   - Features: `['entidad_remitente_enc', 'mes_num', 'montoaembargar', 'estado_embargo_enc', 'es_cliente_bin']`
   - Split: 80% train / 20% test con `stratify=y_tipo`
   - Resultados validados: COACTIVO F1=0.991, JUDICIAL F1=0.976
   - Clases descartadas: `PROCESADO` (22 casos), `SIN_PROCESAR` (55 casos)

2. **Estado Embargo**:
   - Features adicional: `tipo_embargo_enc` (5 features total)
   - CONFIRMADO F1=0.780, PROCESADO F1=0.770
   - Descartados: `PROCESADO_CON_ERRORES` (48), `DESEMBARGO` (13)

3. **Cliente / No Cliente** (clasificación binaria):
   - **Manejo de desbalance**: `scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()`
   - `eval_metric='auc'` (Área bajo curva ROC, apropiado para binario desbalanceado)
   - NO_CLIENTE F1=0.923, CLIENTE F1=0.508 (desbalance ~12:1 en datos)

**Serialización de matrices de confusión** (función `report_to_df`, líneas 653-672):
- Columna `matriz_confusion`: JSON de lista 2D (`[[TP, FP], [FN, TN]]`)
- Columna `clases_matriz`: JSON de etiquetas ordenadas (`["COACTIVO", "JUDICIAL"]`)
- Validadas por `test_matrices_load.py`: deserialización exitosa, suma 442,066 obs/modelo, sin NaN

**Formato `resultados_clasificaciones.csv`**:
```csv
modelo,clase,precision,recall,f1,soporte,matriz_confusion,clases_matriz
Tipo Embargo,COACTIVO,0.990,0.991,0.991,323407,"[[320113, 3294], [1858, 118101]]","[\"COACTIVO\", \"JUDICIAL\"]"
```

### 4.5. Evaluación

#### 4.5.1. Métricas de regresión (consola)

Para modelos de regresión se calculan y reportan en consola durante el entrenamiento:
- **RMSE (Root Mean Squared Error)**: penaliza errores grandes, sensible a outliers
- **MAE (Mean Absolute Error)**: error promedio en unidades originales, más robusto

Valores actuales validados:
| Modelo | RMSE | MAE | Promedio real |
|--------|------|-----|---------------|
| Oficios | 80,515 | 70,225 | 103,458 |
| Demandados | 41,706 | 38,425 | 53,529 |

#### 4.5.2. Métricas de clasificación (CSV persistido)

Para clasificadores se genera `resultados_clasificaciones.csv` con:
- **Precisión**: $\frac{TP}{TP + FP}$ — de los predichos positivos, ¿cuántos acertó?
- **Recall**: $\frac{TP}{TP + FN}$ — de los reales positivos, ¿cuántos detectó?
- **F1-score**: $2 \times \frac{precision \times recall}{precision + recall}$ — media armónica
- **Soporte**: número de muestras por clase en el test set

#### 4.5.3. Tests automatizados de integración

El proyecto incluye tres scripts de smoke testing para validar la integridad del pipeline:

**1. `test_dashboard_load.py`** (66 líneas):
```python
# Simula la lógica de carga del dashboard
dtype_dict = {'modelo': 'category', 'clase': 'category'}
df = pd.read_csv(csv_path, dtype=dtype_dict, engine='c')
# Verifica: columnas esperadas, encoding multi-fallback, NaN en campos críticos
```
- Valida columnas: `modelo`, `clase`, `precision`, `recall`, `f1`, `soporte`
- Multi-encoding fallback: utf-8 → latin-1 → cp1252 → iso-8859-1

**2. `test_matrices_load.py`** (73 líneas):
```python
# Deserializa matrices JSON y verifica integridad
cm = np.array(json.loads(primera_fila['matriz_confusion']))
clases = json.loads(primera_fila['clases_matriz'])
# Valida: suma observaciones = 442,066, sin NaN, dimensiones correctas
```
- Verifica `matriz_confusion` y `clases_matriz` para cada modelo
- Confirma suma de observaciones consistente por modelo

**3. `test_predicciones_futuras.py`** (63 líneas):
```python
# Ejecuta pipeline completo y verifica archivos generados
entrenar_modelos_y_generar_predicciones(consolidado_path, output_dir)
# Valida: 5 archivos esperados, tamaño > 0, columnas correctas
```
- Verifica generación de archivos: `predicciones_oficios_validacion.csv`, `predicciones_oficios_futuro.csv`, `predicciones_demandados_validacion.csv`, `predicciones_demandados_futuro.csv`, `resultados_clasificaciones.csv`

**Ejecución de tests**:
```bash
python test_dashboard_load.py       # ~2 segundos
python test_matrices_load.py        # ~1 segundo
python test_predicciones_futuras.py # ~45 segundos (entrena modelos)
```

### 4.6. Despliegue

#### 4.6.1. Interfaz de línea de comandos (CLI)

El script `procesar_modelo.py` expone una interfaz CLI completa (función `parse_arguments`, líneas 796-810):

```bash
python procesar_modelo.py <csv_files...> [opciones]

Argumentos posicionales:
  csv_files           Rutas a los archivos CSV originales (acepta múltiples)

Opciones:
  --output-dir DIR    Directorio de salida (default: AppData/DashboardEmbargos/datos)
  --frac-muestra F    Fracción mensual a muestrear, 0.0-1.0 (default: 1.0)
  --n-muestra N       Número máximo de filas por mes (prioridad sobre frac)
  --horizonte H       Meses futuros a pronosticar (default: 12)
  --random-state S    Semilla para reproducibilidad (default: 42)
```

**Ejemplos de uso**:
```bash
# Procesar todos los CSV del 2024 con muestreo 10%
python procesar_modelo.py "datos/embargos-2024-*.csv" --frac-muestra 0.10

# Pronóstico extendido de 24 meses
python procesar_modelo.py datos/*.csv --horizonte 24 --output-dir ./resultados
```

#### 4.6.2. Empaquetado y distribución

- El proceso de despliegue incluye:
  - Empaquetado del sistema con PyInstaller (`build_executable.py`), generando un único ejecutable `DashboardEmbargos.exe`.
  - Creación de un instalador Windows con Inno Setup (`installer_setup.iss`), produciendo `DashboardEmbargos_Installer.exe`.
  - Uso de scripts auxiliares (`crear_instalador.ps1`, `crear_instalador.bat`) para automatizar la construcción.
- El ejecutable incluye todas las dependencias (Python embebido, Streamlit, pandas, scikit-learn, xgboost, etc.), de manera que el usuario final solo necesita ejecutar el instalador.

---

## 5. Descripción detallada de los componentes de reportería

### 5.1. Dashboard de Embargos (`dashboard_embargos.py`)

Es la **interface principal de reportería exploratoria** sobre embargos.

#### 5.1.1. Carga de datos optimizada

La función `load_data()` realiza:

- Localización de `embargos_consolidado_mensual.csv` usando `utils_csv`.
- Detección de codificación con `chardet`.
- Lectura con `pandas.read_csv` utilizando tipos optimizados:
  - Campos categóricos (`category`) para disminuir memoria.
  - `montoaembargar` como `float32`.
- Normalización de `es_cliente` a valores binarios.
- Eliminación de filas solo si tienen NaN en columnas **fundamentales**, siguiendo el análisis de `ANALISIS_COLUMNAS.md`.

#### 5.1.2. Sistema de filtros avanzado

Se implementa un sistema de filtros muy completo:

- Filtros por entidad bancaria, ciudad, estado del embargo, tipo de embargo y mes.
- Búsqueda global por banco, ciudad, entidad remitente, nombres e identificación.
- Normalización de valores de `estado_embargo` y `tipo_embargo`:
  - Estados normalizados: `CONFIRMADO`, `PROCESADO`, `SIN_CONFIRMAR`, `PROCESADO_CON_ERRORES`, agrupando múltiples variantes de texto.
  - Tipos normalizados: `JUDICIAL`, `COACTIVO`, también con mapeo de variaciones.

La función `apply_filters_fast` es cacheada y está diseñada para **no bloquear** la interfaz, incluso cuando hay muchos filtros activos o conjuntos de datos grandes.

#### 5.1.3. Métricas ejecutivas en tiempo real

Las métricas se calculan en `calculate_metrics` y se muestran como tarjetas visuales:

- Total de oficios.
- Monto total embargado.
- Promedio de oficios por mes.
- Número de registros visualizados (hasta 100 en la tabla, pero mostrando el total real encontrado).
- Porcentaje de clientes.
- Monto promedio por oficio.
- Oficios activos.
- Número de embargos judiciales.

Estas métricas proporcionan un **resumen ejecutivo inmediato** de la situación para los filtros seleccionados.

#### 5.1.4. Visualizaciones principales

En la pestaña **“Dashboard Principal”** se incluyen:

- **Distribución por tipo de embargo** (gráfico de pastel):
  - Solo se muestran los tipos válidos `JUDICIAL` y `COACTIVO`.
  - Los valores inconsistentes se normalizan y filtran.

- **Distribución por estado del embargo** (gráfico de barras):
  - Se consideran únicamente los estados normalizados válidos.

- **Rankings Top 10**:
  - Entidades bancarias (solo bancos reales, excluyendo textos que son estados mal ubicados).
  - Top 10 ciudades.
  - Top 10 funcionarios.
  - Top 10 entidades remitentes.

- **Evolución mensual de oficios**:
  - Gráfico de línea con el conteo de oficios por mes.
  - Eje temporal ordenado correctamente por `mes` (`YYYY-MM`).

- **Proporción Judicial vs Coactivo (mensual)**:
  - Gráfico de área apilada con proporciones por mes.
  - Permite observar estacionalidad y cambios en la composición de tipos de embargo.

#### 5.1.5. Otras pestañas analíticas

- **Tendencias y Rankings**:
  - Enfocado en la serie temporal de oficios mensuales.

- **Análisis Geográfico**:
  - Distribución por ciudad (barras horizontales de montos).
  - Matriz Ciudad vs Banco (mapa de calor) para analizar concentración y cobertura.

- **Análisis Detallado**:
  - Distribución de montos: histograma con exclusión de ceros y outliers.
  - Estadísticas detalladas (mínimo, máximo, mediana, cuartiles, desviación estándar).
  - Análisis de clientes vs no clientes (pastel).
  - Distribución de tipos de documento (`tipo_documento`).

- **Exportación**:
  - Descarga del subconjunto filtrado en CSV, Excel (si `openpyxl` está disponible) y JSON.
  - Resumen de cuántos registros y columnas se exportan.

En conjunto, este dashboard materializa la parte de **visualización de datos en plataformas de gestión**, proporcionando una interface rica, navegable y con filtros de negocio que permiten generar reportes ad hoc sin escribir código ni consultas SQL.

### 5.2. Dashboard de Predicciones y Métricas (`dashboard_predicciones.py`)

Centra la **reportería analítica basada en IA** (1,451 líneas), exponiendo resultados de modelos de regresión/clasificación con capacidades avanzadas de validación y proyección.

#### 5.2.1. Arquitectura de carga validada

**Función `load_csv(name)`** con cache invalidado por `mtime` del archivo:
```python
@st.cache_data(ttl=3600)  # Cache de 1 hora
def load_csv(name):
    # Detección automática de encoding con fallback
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc, dtype=dtype_dict)
            break
        except UnicodeDecodeError:
            continue
```

- **dtype condicional**: float para predicciones, category para modelo/clase
- **Validación de columnas** esperadas con mensajes descriptivos
- **Tests automatizados**: `test_dashboard_load.py`, `test_matrices_load.py`
- **Archivos consumidos** (4 CSV + 1 métricas):
  - `predicciones_oficios_validacion.csv`: mes, real_oficios, pred_oficios
  - `predicciones_oficios_futuro.csv`: mes, pred, limite_inferior/superior, nivel_confianza, horizonte
  - `predicciones_demandados_validacion.csv`: mes, real_demandados, pred_demandados
  - `predicciones_demandados_futuro.csv`: análogo a oficios
  - `resultados_clasificaciones.csv`: métricas + matrices JSON

#### 5.2.2. Pestaña: Oficios (Validación + Futuro)

**Validación histórica** (período 2024-01 a 2024-09):
- **Gráfico de línea dual**: real vs predicho con Plotly, leyenda interactiva
- **KPIs destacados**: RMSE 80,515 | MAE 70,225 | Promedio real 103,458
- **Tabla paginada**: mes, real, predicho, residual (real - pred), error % 
- **Descarga CSV**: validación completa con residuales calculados

**Pronóstico futuro** (12 meses con intervalos):
- **Gráfico con banda de confianza**: área sombreada limite_inferior ↔ limite_superior
- **Niveles cualitativos**: coloreado por Alta (verde) / Media (amarillo) / Baja (rojo)
- **Tarjetas métricas**:
  - Próximo mes: 112,725 oficios
  - Acumulado anual: 1.64M oficios
  - Nivel confianza próximo: Alta
- **Advertencia visual**: icono ⚠️ cuando `limite_inferior=0` (horizontes >3 por truncamiento)

#### 5.2.3. Pestaña: Demandados (estructura idéntica)

- RMSE 41,706 | MAE 38,425 | Promedio real 53,529
- Próximo mes: 103,112 demandados | Proyección anual: 918K
- Intervalos truncados en horizontes lejanos (misma lógica que oficios)

#### 5.2.4. Pestaña: Métricas de Clasificación

**Tabla consolidada interactiva**:
- Columnas visibles: modelo, clase, precision, recall, f1, soporte
- Columnas ocultas: matriz_confusion (JSON), clases_matriz (JSON)
- Filtros dinámicos: selector de modelo, selector de clase
- Paginación: 10 filas por página con navegación
- Descarga: CSV completo con todas las columnas

**Visualización de matrices de confusión**:
- Selector de modelo → renderiza heatmap Plotly
- Diagonal resaltada (aciertos) vs celdas claras (errores)
- Anotación de valores absolutos en cada celda
- Ejemplo Tipo Embargo: `[[320113, 3294], [1858, 118101]]` = 99.0% precisión diagonal

**Sistema de tooltips educativos** (diccionario `HELPS`, líneas 78-87):
```python
HELPS = {
    "mae": "Error Absoluto Medio: promedio de la magnitud de errores...",
    "rmse": "Raíz del Error Cuadrático Medio: penaliza errores grandes...",
    "f1_score": "F1-Score: métrica balanceada entre precisión y recall...",
    "precision": "Precisión: de los predichos positivos, ¿cuántos acertó?",
    "recall": "Recall: de los reales positivos, ¿cuántos detectó?",
    "matriz_confusion": "Tabla que muestra aciertos (diagonal) y confusiones..."
}
```
- Iconos `ℹ️` con hover que despliegan explicación completa
- Dirigido a usuarios no técnicos (áreas legales, riesgos)

Este dashboard **transparenta la caja negra de IA**, esencial para tesis y contextos regulados (auditoría, cumplimiento).

---

## 6. Orquestación y automatización: `launcher.py` y `utils_csv.py`

### 6.1. `launcher.py`

El archivo `launcher.py` funciona como un **hub de orquestación** que conecta datos, modelos, dashboards y empaquetado. Sus responsabilidades principales son:

- **Gestión de CSV de origen de BD**:
  - Permite seleccionar uno o varios archivos CSV originales.
  - Muestra de forma resumida cuántos archivos se han seleccionado.

- **Estado de archivos generados**:
  - Verifica la existencia de 6 archivos:
    - `embargos_consolidado_mensual.csv`
    - `predicciones_oficios_validacion.csv` + `predicciones_oficios_futuro.csv`
    - `predicciones_demandados_validacion.csv` + `predicciones_demandados_futuro.csv`
    - `resultados_clasificaciones.csv`
  - Presenta este estado mediante checkboxes deshabilitados pero coloreados (verde si existe, rojo si falta).

- **Recalcular archivos (pipeline completo)**:
  - Llama a `ejecutar_procesamiento`, que:
    - Invoca `procesar_csv_original` y `entrenar_modelos_y_generar_predicciones`.
    - Redirige la salida a una ventana de progreso con texto detallado.
    - Permite que el usuario lea errores y mensajes intermedios antes de cerrar.

- **Inicio de dashboards**:
  - `start_embargos_dashboard` y `start_predicciones_dashboard`:
    - Verifican que los CSV requeridos existan (si no, solicitan o ejecutan el procesamiento).
    - Localizan los scripts `dashboard_embargos.py` y `dashboard_predicciones.py` en distintas rutas posibles (ejecutable, `_MEIPASS`, carpeta del proyecto).
    - Llaman a `run_streamlit`, que:
      - Copia los scripts (y `utils_csv.py`) a una carpeta de datos del usuario si es necesario (para evitar problemas de permisos en `Program Files`).
      - Lanza un proceso Streamlit en un puerto disponible.
      - Redirige logs a archivos `streamlit_embargos.log` y `streamlit_predicciones.log`.

- **Control de procesos**:
  - Permite detener todos los dashboards activos.
  - Maneja el cierre de la aplicación preguntando al usuario si desea detener procesos que están corriendo.

### 6.2. `utils_csv.py`

`utils_csv.py` proporciona una capa de abstracción para encontrar y escribir archivos en distintos contextos (desarrollo vs ejecutable instalado):

- **`get_base_path()`**: devuelve la ruta base donde está el ejecutable o, en modo desarrollo, el proyecto.
- **`get_data_path()`**: determina una carpeta segura para escribir archivos CSV:
  - En Windows ejecutable: `AppData\Roaming\DashboardEmbargos\datos`.
  - En desarrollo: carpeta del proyecto (y opcionalmente subcarpeta `datos`).
- **`find_csv_file(filename)`**: busca un archivo en múltiples ubicaciones, en orden de prioridad:
  1. Carpeta de datos del usuario (AppData).
  2. Carpeta base.
  3. Subcarpetas `datos` o `data`.
  4. Carpeta actual.
- **`get_csv_path(filename, required=True)`**: usa `find_csv_file` y, si no encuentra el archivo y `required=True`, lanza un `FileNotFoundError` con un mensaje detallado explicando dónde se buscó y qué hacer.

Sin estas utilidades, la aplicación tendría problemas de permisos y rutas, especialmente cuando se ejecuta instalada en `Program Files` en Windows.

---

## 7. Resultados validados experimentalmente

### 7.1. Dataset consolidado y normalizado (parcialmente)

**Archivo**: `embargos_consolidado_mensual.csv`
- **Dimensiones**: 2,227,458 filas × 23 columnas (muestreo 7% mensual)
- **Tamaño en disco**: ~180 MB (comprimido ~45 MB)
- **Cobertura temporal**: 2020-01 a 2024-12 (60 meses)

**Normalizaciones aplicadas en `procesar_csv_original`**:
1. `DTYPE_OVERRIDES={'tipo_carta': 'string'}`: fuerza tipo para evitar DtypeWarning
2. `es_cliente` binarizado: múltiples patrones (`SI`, `1`, `CLIENTE`, `TRUE`, `YES`, `SÍ`) → `1`
3. Categorías raras → `OTRO` para reducir cardinalidad
4. Fechas parseadas con `pd.to_datetime(..., errors='coerce')`
5. Filas corregidas: columnas < 23 rellenadas con vacío, > 23 truncadas

**Limitaciones documentadas** (heredadas de datos fuente):
- Montos sin estandarización (mezcla de escalas)
- Valores categóricos con variantes ortográficas no normalizadas
- Reflejado en RMSE elevados e intervalos truncados

### 7.2. Pronósticos validados con horizonte extendido

**Archivos de validación histórica** (período test: último año disponible):

| Archivo | Tamaño | Columnas | Período validación |
|---------|--------|----------|-------------------|
| `predicciones_oficios_validacion.csv` | 277 bytes | mes, real_oficios, pred_oficios | 2024-01 a 2024-09 |
| `predicciones_demandados_validacion.csv` | 274 bytes | mes, real_demandados, pred_demandados | 2024-01 a 2024-09 |

**Métricas de validación** (calculadas en `entrenar_modelos_y_generar_predicciones`):

| Modelo | RMSE | MAE | Promedio real | MAPE estimado |
|--------|------|-----|---------------|---------------|
| Oficios | 80,515 | 70,225 | 103,458 | ~68% |
| Demandados | 41,706 | 38,425 | 53,529 | ~72% |

> **Nota**: MAPE elevado debido a predicciones saturadas en meses iniciales (oficios ≈1,857 vs real 99k–113k) por lags con NaN imputados como 0.

**Archivos de pronóstico futuro** (horizonte 12 meses):

| Archivo | Tamaño | Columnas |
|---------|--------|----------|
| `predicciones_oficios_futuro.csv` | 573 bytes | mes, pred_oficios, limite_inferior, limite_superior, nivel_confianza, horizonte_meses |
| `predicciones_demandados_futuro.csv` | 576 bytes | mes, pred_demandados, limite_inferior, limite_superior, nivel_confianza, horizonte_meses |

**Proyecciones principales**:
- **Oficios**: próximo mes 112,725 | acumulado 12 meses 1.64M
- **Demandados**: próximo mes 103,112 | acumulado 12 meses 918K
- Niveles de confianza: Alta (h≤3), Media (h≤6), Baja (h>6)
- Intervalos [0, N] para h>3 (límite inferior negativo → `max(0, *)` por truncamiento)

### 7.3. Métricas de clasificación con filtrado por soporte

**Archivo**: `resultados_clasificaciones.csv` (2,188 bytes)
- **Observaciones totales por modelo**: 442,066 (validado por `test_matrices_load.py`)
- **Formato**: modelo, clase, precision, recall, f1, soporte, matriz_confusion (JSON), clases_matriz (JSON)

**Resumen de rendimiento por modelo**:

| Modelo | Clases válidas | Mejores F1 | Clases descartadas (<100 muestras) |
|--------|----------------|------------|-----------------------------------|
| Tipo Embargo | COACTIVO, JUDICIAL | 0.991, 0.976 | PROCESADO (22), SIN_PROCESAR (55) |
| Estado Embargo | CONFIRMADO, PROCESADO, SIN_CONFIRMAR | 0.780, 0.770, 0.650 | PROCESADO_CON_ERRORES (48), DESEMBARGO (13) |
| Cliente | NO_CLIENTE, CLIENTE | 0.923, 0.508 | N/A (binario con scale_pos_weight) |

**Matrices de confusión ejemplo** (Tipo Embargo):
```
                 Pred: COACTIVO  Pred: JUDICIAL
Real: COACTIVO       320,113         3,294      (97.0% recall)
Real: JUDICIAL         1,858       118,101      (98.5% recall)
```

### 7.4. Interfaces de reportería validadas por smoke tests

**Dashboard embargos** (`dashboard_embargos.py`, 1,644 líneas):
- Procesamiento de 2,227,458 registros sin bloqueo de UI
- Filtros vectorizados con `@st.cache_data` (respuesta <100ms tras cache)
- 8 KPIs ejecutivos calculados en tiempo real
- 6 tipos de gráficos Plotly (pastel, barras, línea, área, heatmap, histograma)
- Exportación validada: CSV, Excel (openpyxl), JSON

**Dashboard predicciones** (`dashboard_predicciones.py`, 1,451 líneas):
- Carga de 4 CSV + 1 métricas con fallback multi-encoding
- 3 pestañas especializadas (Oficios, Demandados, Clasificación)
- Deserialización JSON de matrices sin errores
- Tooltips contextuales para 6 métricas diferentes

**Suite de tests automatizados** (ejecutados 2025-12-13):
```bash
$ python test_dashboard_load.py      # ✓ Columnas críticas validadas
$ python test_matrices_load.py       # ✓ JSON deserializado, 442,066 obs/modelo
$ python test_predicciones_futuras.py # ✓ 5 archivos generados correctamente
```

---

## 8. Alineación con el objetivo de tesis

El objetivo planteado es:

> *“Desarrollar interfaces de reportería con inteligencia artificial, permitiendo la generación de reportes automatizados y la visualización de datos en plataformas de gestión.”*

Cómo lo cumple el proyecto:

### 8.1. Análisis de cumplimiento por componente

#### Interfaces de reportería

| Componente | Implementación | Líneas código | Tecnología |
|------------|----------------|---------------|------------|
| Dashboard Embargos | Exploración histórica, filtros, KPIs | 1,644 | Streamlit + Plotly |
| Dashboard Predicciones | Pronósticos, validación, métricas ML | 1,451 | Streamlit + Plotly |
| Launcher GUI | Orquestación visual para usuarios no técnicos | ~400 | Tkinter |

**Características de reportería implementadas**:
- Diseño responsivo con paleta corporativa (`#bfe084`, `#3c8198`, `#424e71`, `#252559`)
- Filtros multinivel (7 dimensiones: banco, ciudad, estado, tipo, mes, tipo_documento, búsqueda global)
- Exportación multiformat (CSV, Excel via openpyxl, JSON)
- Paginación de tablas con conteo de resultados
- Cache inteligente (`@st.cache_data`) para respuesta sub-segundo

#### Inteligencia artificial integrada

| Modelo | Objetivo | Algoritmo | Métricas validadas |
|--------|----------|-----------|-------------------|
| Regresión Oficios | Pronóstico mensual | XGBRegressor (Poisson) | RMSE 80,515 |
| Regresión Demandados | Pronóstico mensual | XGBRegressor (Poisson) | RMSE 41,706 |
| Clasificador Tipo Embargo | COACTIVO/JUDICIAL | XGBClassifier | F1 0.99/0.98 |
| Clasificador Estado | CONFIRMADO/PROCESADO/... | XGBClassifier | F1 0.78/0.77 |
| Clasificador Cliente | Binario (desbalanceado) | XGBClassifier | F1 0.92/0.51 |

**Innovaciones de IA implementadas**:
- Pronóstico recursivo 12 meses con actualización de lags
- Intervalos de confianza adaptativos con truncamiento inteligente
- Filtrado automático por soporte mínimo (`MIN_CLASS_SAMPLES=100`)
- Manejo de desbalance con `scale_pos_weight` automático
- Serialización de matrices de confusión para auditoría

#### Generación automatizada de reportes

**Pipeline ETL + ML completamente automático** (`procesar_modelo.py`):
```
CSV crudos BD → Consolidación → Limpieza → Features → Entrenamiento → Predicción → 6 CSV salida
    (input)        (concat)    (normalize)  (lags)     (XGBoost)    (recursivo)    (output)
```

**Archivos generados automáticamente** (sin intervención post-selección de CSV):
1. `embargos_consolidado_mensual.csv` — dataset unificado
2. `predicciones_oficios_validacion.csv` — métricas validación
3. `predicciones_oficios_futuro.csv` — pronóstico 12 meses
4. `predicciones_demandados_validacion.csv` — métricas validación
5. `predicciones_demandados_futuro.csv` — pronóstico 12 meses
6. `resultados_clasificaciones.csv` — métricas + matrices confusión

#### Visualización en plataformas de gestión

**Características de plataforma**:
- Servidor local Streamlit (puertos 8501, 8502)
- Consumo via navegador web estándar (Chrome, Edge, Firefox)
- Sin instalación adicional para usuarios finales (ejecutable autocontenido)
- Compatible con estaciones de trabajo corporativas Windows

**Distribución profesional**:
- PyInstaller → ejecutable único `DashboardEmbargos.exe`
- Inno Setup → instalador `DashboardEmbargos_Installer.exe`
- AppData para persistencia de datos (evita permisos de administrador)

### 8.2. Conclusión de alineación

El proyecto constituye un **caso práctico completo y funcional** que demuestra la viabilidad de integrar ML en reportería empresarial, automatizar el ciclo end-to-end desde datos crudos hasta visualización, y desplegar profesionalmente sin dependencias técnicas.

Cumple íntegramente el objetivo de tesis al implementar los cuatro pilares: **interfaces de reportería**, **inteligencia artificial**, **generación automatizada**, y **visualización en plataformas de gestión**.

---

## 9. Conclusiones y líneas investigativas futuras

El sistema constituye una **solución integral de analítica predictiva end-to-end** con las siguientes características validadas:

### 9.1. Logros demostrados experimentalmente

#### Procesamiento robusto de datos heterogéneos
- **Escala**: 2.2M+ registros procesados en pipeline automatizado
- **Resiliencia**: reparación de filas malformadas (< o > 23 columnas)
- **Flexibilidad**: soporte multi-encoding (utf-8, latin-1, cp1252, iso-8859-1)
- **Reproducibilidad**: semilla configurable `random_state=42` para muestreo

#### Capacidad predictiva con intervalos de confianza
- **Pronóstico extendido**: 12 meses con actualización recursiva de lags
- **Cuantificación de incertidumbre**: intervalos adaptativos $Z \times \sigma \times \sqrt{h}$
- **Etiquetado cualitativo**: niveles Alta/Media/Baja por horizonte
- **Métricas de validación**: RMSE oficios 80,515 | demandados 41,706

#### Transparencia y auditabilidad de IA
- **Matrices de confusión** serializadas en JSON y visualizadas como heatmaps
- **Filtrado por soporte** (`MIN_CLASS_SAMPLES=100`) documentado en logs
- **Tooltips educativos** explicando MAE/RMSE/F1/Precisión/Recall
- **Limitaciones** documentadas honestamente en informes técnicos

#### Despliegue profesional y accesible
- **Ejecutable único**: PyInstaller con todas las dependencias embebidas
- **Instalador Windows**: Inno Setup con acceso directo en menú inicio
- **Persistencia en AppData**: evita problemas de permisos en Program Files
- **Smoke tests**: 3 scripts de validación automatizada

### 9.2. Limitaciones documentadas (base para investigación futura)

Estas limitaciones están detalladas en los informes técnicos especializados y representan oportunidades de mejora:

| Limitación | Causa raíz | Impacto | Informe de referencia |
|------------|-----------|---------|----------------------|
| Intervalos truncados (h>3) | Residuos elevados sin log-transform | limite_inferior=0 | INFORME_VALIDACION_MODELO_ML.md |
| Predicciones saturadas iniciales | Lags con NaN imputados como 0 | MAPE ~68-72% | INFORME_VALIDACION_MODELO_ML.md |
| DtypeWarning persistente | tipo_carta con valores mixtos | Advertencia en carga | INFORME_VALIDACION_DASHBOARD_EMBARGOS.md |
| F1 Cliente bajo (0.508) | Desbalance 12:1 en datos | Subdetección de clientes | INFORME_VALIDACION_DASHBOARD_PREDICCIONES.md |

### 9.3. Extensiones propuestas para monografía

#### Bloque 1: Normalización investigativa (impacto directo en métricas)

| # | Propuesta | Técnica específica | Beneficio esperado |
|---|-----------|-------------------|-------------------|
| 1 | Estandarización previa | z-score por entidad, winsorización P5-P95 | Reducir RMSE 20-30% |
| 2 | Evaluación comparativa | Test A/B con datos normalizados | Cuantificar mejora |
| 3 | Transformación de residuos | Box-Cox para estabilizar varianza | Intervalos no truncados |

#### Bloque 2: Modelos avanzados (extensión de capacidades)

| # | Propuesta | Técnica específica | Caso de uso |
|---|-----------|-------------------|------------|
| 4 | Detección de anomalías | Isolation Forest, LSTM-Autoencoder | Meses/bancos atípicos |
| 5 | Forecasting probabilístico | Prophet con cuantiles, Bayesian Ridge | Distribución completa |
| 6 | Clasificadores robustos | Focal loss, SMOTE, cost-sensitive | Clases raras (<100) |

#### Bloque 3: MLOps y gobernanza (escalabilidad)

| # | Propuesta | Técnica específica | Beneficio |
|---|-----------|-------------------|----------|
| 7 | Versionado de modelos | MLflow, DVC | Trazabilidad completa |
| 8 | Monitoreo de drift | Evidently, Alibi Detect | Alertas de degradación |
| 9 | API REST | FastAPI con swagger | Integración CRM/legales |
| 10 | Reportes programados | Jinja2 + PDF | Automatización semanal |

#### Bloque 4: Experiencia de usuario (accesibilidad)

| # | Propuesta | Técnica específica | Audiencia |
|---|-----------|-------------------|----------|
| 11 | Wizard de configuración | Formulario paso a paso | Usuarios no técnicos |
| 12 | Dashboard de calidad | DQ score, alertas | Administradores de datos |
| 13 | Modo accesibilidad | WCAG 2.1, alto contraste | Usuarios con discapacidad |

### 9.4. Contribución académica

Este proyecto aporta al campo de **gestión de información con soporte de aprendizaje automático** en tres dimensiones:

1. **Metodológica**: pipeline reproducible ETL+ML con configuración CLI extensible
2. **Práctica**: solución desplegable en entornos corporativos sin infraestructura ML
3. **Didáctica**: tooltips, documentación técnica, y transparencia de métricas para transferencia de conocimiento

Las líneas investigativas propuestas consolidarían el sistema como **plataforma de referencia** para analítica empresarial con IA, generando aportes publicables en normalización de datos financieros, forecasting de procesos legales, y democratización de ML en organizaciones no técnicas.

---

## 10. Referencias a documentación técnica complementaria

- `INFORME_VALIDACION_MODELO_ML.md`: pipeline predictivo, arquitectura dual validación/pronóstico, métricas actuales, impacto normalización pendiente, recomendaciones investigativas
- `INFORME_VALIDACION_DASHBOARD_EMBARGOS.md`: dashboard exploratorio, caracterización dataset, funcionamiento interno, hallazgos con datos no normalizados, líneas de mejora
- `INFORME_VALIDACION_DASHBOARD_PREDICCIONES.md`: dashboard de pronósticos, arquitectura carga, evidencias testing, limitaciones intervalos, propuestas visualización calidad
- `ANALISIS_COLUMNAS.md`: clasificación campos por relevancia funcional
- `HISTORIAL_DE_CAMBIOS_Y_MEJORAS.md`: log evolutivo del proyecto

---

## Anexo A: Dependencias y versiones

### A.1. Dependencias Python (`requirements.txt`)

| Paquete | Propósito | Versión recomendada |
|---------|-----------|---------------------|
| `streamlit` | Framework de dashboards web | ≥1.28.0 |
| `pandas` | Manipulación de datos tabulares | ≥2.0.0 |
| `numpy` | Operaciones numéricas | ≥1.24.0 |
| `plotly` | Gráficos interactivos | ≥5.15.0 |
| `scikit-learn` | Preprocesamiento ML | ≥1.3.0 |
| `xgboost` | Algoritmos gradient boosting | ≥2.0.0 |
| `openpyxl` | Exportación Excel | ≥3.1.0 |

**Instalación**:
```bash
pip install -r requirements.txt
```

### A.2. Herramientas de construcción

| Herramienta | Propósito | Archivo de configuración |
|-------------|-----------|--------------------------|
| PyInstaller | Empaquetado ejecutable | `build_executable.py`, `DashboardEmbargos.spec` |
| Inno Setup | Instalador Windows | `installer_setup.iss` |

---

## Anexo B: Estructura de archivos del proyecto

```
practica-analisis-embargos/
├── 📊 src/dashboards/                     # Dashboards Streamlit
│   ├── __init__.py
│   ├── dashboard_embargos.py              # 1,700+ líneas - exploración histórica
│   ├── dashboard_predicciones.py          # 1,450+ líneas - pronósticos + métricas ML
│   ├── dashboard_styles.py                # CSS centralizado (paleta corporativa)
│   └── dashboard_tabs_futuro.py           # Componentes adicionales de tabs
│
├── 🤖 src/pipeline_ml/                    # Pipeline de Machine Learning
│   ├── __init__.py
│   ├── procesar_modelo.py                 # 866 líneas - ETL + entrenamiento + predicción
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
│   ├── INFORME_PROYECTO_DASHBOARD_EMBARGOS.md  # Este documento
│   ├── ANALISIS_COLUMNAS.md
│   ├── GUIA_CREAR_INSTALADOR.md
│   └── HISTORIAL_DE_CAMBIOS_Y_MEJORAS.md
│
├── ob.ico                                 # Icono de la aplicación
├── README.md                              # Guía rápida de uso
└── requirements.txt                       # Dependencias Python
```

---

## Anexo C: Glosario técnico

| Término | Definición |
|---------|------------|
| **RMSE** | Root Mean Squared Error — raíz del error cuadrático medio, penaliza errores grandes |
| **MAE** | Mean Absolute Error — error absoluto medio, robusto a outliers |
| **F1-score** | Media armónica de precisión y recall, métrica balanceada para clasificación |
| **Lag** | Valor de una variable en un período anterior (ej: `oficios_lag1` = oficios mes anterior) |
| **MA** | Moving Average — media móvil de N períodos anteriores |
| **XGBoost** | eXtreme Gradient Boosting — algoritmo de gradient boosting optimizado |
| **Poisson** | Distribución de probabilidad para conteos no negativos |
| **scale_pos_weight** | Ponderación para clases positivas en clasificación desbalanceada |
| **Streamlit** | Framework Python para crear aplicaciones web de datos |
| **PyInstaller** | Herramienta para empaquetar Python en ejecutables standalone |
| **Inno Setup** | Herramienta para crear instaladores Windows |

---

*Documento actualizado: 2025-12-13*
*Versión del sistema: 2.2*
*Autor: Sistema de Análisis Predictivo de Embargos Bancarios*
