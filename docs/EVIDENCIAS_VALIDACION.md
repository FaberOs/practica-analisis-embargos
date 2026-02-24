# Evidencias de Validación del Modelo de Machine Learning

**Proyecto:** Dashboard de Análisis de Embargos Bancarios  
**Fecha de generación:** Diciembre 2025  
**Versión:** 2.0

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Análisis del Dataset](#2-análisis-del-dataset)
3. [Evidencia de Tests de Integridad](#3-evidencia-de-tests-de-integridad)
4. [Métricas de los Modelos de Regresión](#4-métricas-de-los-modelos-de-regresión)
5. [Métricas de los Modelos de Clasificación](#5-métricas-de-los-modelos-de-clasificación)
6. [Gráficas de Validación](#6-gráficas-de-validación)
7. [Análisis de Resultados](#7-análisis-de-resultados)
8. [Conclusiones](#8-conclusiones)

---

## 1. Resumen Ejecutivo

Este documento presenta las evidencias de validación del sistema de Machine Learning implementado para el análisis predictivo de embargos bancarios. Se incluyen:

- **Tests de integridad** de los módulos del sistema
- **Métricas cuantitativas** de los modelos de regresión y clasificación
- **Gráficas de backtesting** que demuestran el comportamiento predictivo
- **Análisis granular** del dataset utilizado

### Datos Fuente

| Concepto | Valor |
|----------|-------|
| Archivo fuente | `embargos_consolidado_mensual.csv` |
| Origen de datos | Base de datos de embargos (semestres 2023-1, 2023-2, 2024-1, 2024-2) |
| Período temporal | Mayo 2023 - Septiembre 2024 |
| Total de meses | 17 |

---

## 2. Análisis del Dataset

### 2.1 Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| **Total de registros originales** | 2,227,458 |
| **Total de columnas** | 23 |
| **Registros con mes válido (YYYY-MM)** | 2,227,044 |
| **Registros filtrados (mes inválido)** | 414 |
| **Demandados únicos (identificaciones)** | 907,815 |

### 2.2 Análisis de Valores Nulos

| Columna | Nulos | Porcentaje |
|---------|-------|------------|
| `mes` | 0 | 0.00% |
| `identificacion` | 9,014 | 0.40% |
| `tipo_embargo` | 0 | 0.00% |
| `estado_embargo` | 0 | 0.00% |
| `es_cliente` | 0 | 0.00% |

### 2.3 Registros Filtrados

Se identificaron **414 registros** con valores inválidos en la columna `mes`, que fueron excluidos del análisis:

- Valores encontrados: `COLPATRIA`, `JUDICIAL`, `COOPCENTRAL`, `CONFIRMADO`, `SANTANDER`, `PROCESADO`, `FALABELLA`, `EMBARGO`
- Estos valores corresponden a errores de desplazamiento de columnas en los datos fuente originales
- **Impacto:** 0.02% del total de registros

### 2.4 Distribución de Registros por Mes

| Mes | Registros | Porcentaje |
|-----|-----------|------------|
| 2023-05 | 71,009 | 3.19% |
| 2023-06 | 111,284 | 5.00% |
| 2023-07 | 91,406 | 4.10% |
| 2023-08 | 115,480 | 5.19% |
| 2023-09 | 187,879 | 8.44% |
| 2023-10 | 128,095 | 5.75% |
| 2023-11 | 179,263 | 8.05% |
| 2023-12 | 107,185 | 4.81% |
| 2024-01 | 110,845 | 4.98% |
| 2024-02 | 96,333 | 4.33% |
| 2024-03 | 110,224 | 4.95% |
| 2024-04 | 152,468 | 6.85% |
| 2024-05 | 155,797 | 7.00% |
| 2024-06 | 94,752 | 4.25% |
| 2024-07 | 110,923 | 4.98% |
| 2024-08 | 152,150 | 6.83% |
| 2024-09 | 251,951 | 11.31% |
| **TOTAL** | **2,227,044** | **100%** |

### 2.5 División Entrenamiento / Validación

| Conjunto | Meses | Período | Registros |
|----------|-------|---------|-----------|
| **Entrenamiento** | 8 | 2023-05 a 2023-12 | 991,601 |
| **Validación (Test)** | 9 | 2024-01 a 2024-09 | 1,235,443 |

---

## 3. Evidencia de Tests de Integridad

### 3.1 Test: Carga del Dashboard (`test_dashboard_load.py`)

```
============================================================
TEST: Simulando carga del dashboard
============================================================

1. dtype_dict configurado: {'modelo': 'category', 'clase': 'category'}

2. Intentando cargar con encoding: utf-8
   ✓ Carga exitosa con utf-8

3. DataFrame cargado correctamente
   Filas: 10
   Columnas: ['modelo', 'clase', 'precision', 'recall', 'f1', 'soporte', 
              'matriz_confusion', 'clases_matriz']

4. Verificando columnas críticas:
   'matriz_confusion' presente: True
   'clases_matriz' presente: True

5. Verificando contenido de matriz_confusion:
   Tipo de dato: object
   Primer valor: [[320113, 3294, 0, 0], [2531, 116051, 0, 0], ...]
   Valores nulos: 0

============================================================
TEST COMPLETADO ✓
============================================================
```

**Resultado:** PASSED ✅

### 3.2 Test: Verificación de Matrices de Confusión (`test_matrices_load.py`)

```
============================================================
TEST: Verificación de Matrices de Confusión en CSV
============================================================

1. Cargando archivo: resultados_clasificaciones.csv
   ✓ Archivo cargado correctamente
   Filas: 10, Columnas: 8

2. Verificando columnas...
   ✓ Todas las columnas requeridas están presentes

3. Verificando contenido de matrices...
   Modelos encontrados: ['Tipo Embargo', 'Estado Embargo', 'Cliente']

   Modelo 1/3: Tipo Embargo
      ✓ Matriz deserializada correctamente
      Dimensiones: (4, 4)
      Clases: ['COACTIVO', 'JUDICIAL', 'PROCESADO', 'SIN_PROCESAR']
      Suma total: 442,066

   Modelo 2/3: Estado Embargo
      ✓ Matriz deserializada correctamente
      Dimensiones: (4, 4)
      Clases: ['CONFIRMADO', 'EMBARGO', 'PROCESADO', 'PROCESADO_CON_ERRORES']
      Suma total: 442,050

   Modelo 3/3: Cliente
      ✓ Matriz deserializada correctamente
      Dimensiones: (2, 2)
      Clases: ['NO_CLIENTE', 'CLIENTE']
      Suma total: 442,066

============================================================
TEST COMPLETADO ✓
============================================================
```

**Resultado:** PASSED ✅

### 3.3 Test: Generación de Predicciones Futuras (`test_predicciones_futuras.py`)

```
================================================================================
PRUEBA DE GENERACIÓN DE PREDICCIONES FUTURAS
================================================================================

============================================================
ENTRENANDO MODELOS Y GENERANDO PREDICCIONES
============================================================

[INFO] Entrenando modelo de regresión: Oficios por mes...
   RMSE: 80515.03, MAE: 70224.72
   [OK] Generado: predicciones_oficios_validacion.csv

[INFO] Generando predicciones futuras de oficios (12 meses)...
   Modelo entrenado con 64 registros históricos
   [OK] Generado: predicciones_oficios_futuro.csv
   Predicción para próximo mes (2024-10): 112,725 oficios
   Proyección anual (12 meses): 1,640,140 oficios

[INFO] Entrenando modelo de regresión: Demandados únicos por mes...
   RMSE: 41705.71, MAE: 38424.61
   [OK] Generado: predicciones_demandados_validacion.csv

[INFO] Generando predicciones futuras de demandados (12 meses)...
   Modelo entrenado con 64 registros históricos
   [OK] Generado: predicciones_demandados_futuro.csv
   Predicción para próximo mes (2024-10): 103,112 demandados
   Proyección anual (12 meses): 918,319 demandados

[INFO] Entrenando modelos de clasificación...
   [INFO] tipo_embargo_enc: se descartan 1 clases con soporte < 100
   [OK] Modelo: Tipo Embargo
   [INFO] estado_embargo_enc: se descartan 4 clases con soporte < 100
   [OK] Modelo: Estado Embargo
   [OK] Modelo: Cliente/No Cliente

[OK] Generado: resultados_clasificaciones.csv

============================================================
[OK] PROCESAMIENTO COMPLETADO ✓
============================================================

================================================================================
VERIFICACIÓN DE ARCHIVOS GENERADOS
================================================================================
✅ predicciones_oficios_validacion.csv - 277 bytes
✅ predicciones_oficios_futuro.csv - 573 bytes
✅ predicciones_demandados_validacion.csv - 274 bytes
✅ predicciones_demandados_futuro.csv - 576 bytes
✅ resultados_clasificaciones.csv - 2,188 bytes
================================================================================
```

**Resultado:** PASSED ✅

---

## 4. Métricas de los Modelos de Regresión

### 4.1 Modelo: Predicción de Oficios Mensuales

| Métrica | Valor | Descripción |
|---------|-------|-------------|
| **RMSE** | 80,515.03 | Root Mean Square Error - Error cuadrático medio |
| **MAE** | 70,224.72 | Mean Absolute Error - Error absoluto medio |
| **MAPE** | 54.44% | Mean Absolute Percentage Error |
| **R²** | -2.0303 | Coeficiente de determinación |

### 4.2 Modelo: Predicción de Demandados Únicos Mensuales

| Métrica | Valor | Descripción |
|---------|-------|-------------|
| **RMSE** | 41,705.71 | Root Mean Square Error - Error cuadrático medio |
| **MAE** | 38,424.61 | Mean Absolute Error - Error absoluto medio |
| **MAPE** | 58.58% | Mean Absolute Percentage Error |
| **R²** | -2.7957 | Coeficiente de determinación |

### 4.3 Datos de Validación Detallados

#### Oficios Mensuales (Real vs Predicción)

| Mes | Real | Predicción | Error Absoluto | Error % |
|-----|------|------------|----------------|---------|
| 2024-01 | 112,774 | 1,857 | 110,917 | 98.4% |
| 2024-02 | 99,045 | 1,857 | 97,188 | 98.1% |
| 2024-03 | 106,285 | 1,857 | 104,428 | 98.3% |
| 2024-04 | 151,312 | 47,459 | 103,853 | 68.6% |
| 2024-05 | 156,512 | 68,950 | 87,562 | 55.9% |
| 2024-06 | 92,263 | 96,962 | 4,699 | 5.1% |
| 2024-07 | 111,420 | 107,235 | 4,185 | 3.8% |
| 2024-08 | 149,647 | 96,962 | 52,685 | 35.2% |
| 2024-09 | 250,501 | 183,995 | 66,506 | 26.5% |

#### Demandados Únicos Mensuales (Real vs Predicción)

| Mes | Real | Predicción | Error Absoluto | Error % |
|-----|------|------------|----------------|---------|
| 2024-01 | 102,636 | 957 | 101,679 | 99.1% |
| 2024-02 | 90,256 | 957 | 89,299 | 98.9% |
| 2024-03 | 103,277 | 957 | 102,320 | 99.1% |
| 2024-04 | 140,355 | 44,116 | 96,239 | 68.6% |
| 2024-05 | 143,600 | 66,025 | 77,575 | 54.0% |
| 2024-06 | 88,231 | 93,995 | 5,764 | 6.5% |
| 2024-07 | 104,195 | 104,246 | 51 | 0.0% |
| 2024-08 | 141,091 | 93,996 | 47,095 | 33.4% |
| 2024-09 | 234,755 | 176,887 | 57,868 | 24.7% |

---

## 5. Métricas de los Modelos de Clasificación

### 5.1 Modelo: Tipo de Embargo

| Métrica Global | Valor |
|----------------|-------|
| **Total de predicciones** | 442,066 |
| **Accuracy** | 98.68% |
| **Número de clases** | 4 |

#### Métricas por Clase

| Clase | Precision | Recall | F1-Score | Soporte |
|-------|-----------|--------|----------|---------|
| COACTIVO | 0.9922 | 0.9898 | 0.9910 | Alto |
| JUDICIAL | 0.9724 | 0.9787 | 0.9755 | Alto |
| PROCESADO | 0.7143 | 0.6818 | 0.6977 | Bajo |
| SIN_PROCESAR | 0.8909 | 0.8909 | 0.8909 | Medio |

### 5.2 Modelo: Estado de Embargo

| Métrica Global | Valor |
|----------------|-------|
| **Total de predicciones** | 442,050 |
| **Accuracy** | 77.45% |
| **Número de clases** | 4 |

#### Métricas por Clase

| Clase | Precision | Recall | F1-Score | Soporte |
|-------|-----------|--------|----------|---------|
| CONFIRMADO | 0.7834 | 0.7773 | 0.7803 | Alto |
| EMBARGO | 1.0000 | 1.0000 | 1.0000 | Bajo |
| PROCESADO | 0.7651 | 0.7716 | 0.7683 | Alto |
| PROCESADO_CON_ERRORES | 0.0000 | 0.0000 | 0.0000 | Muy bajo |

### 5.3 Modelo: Cliente / No Cliente

| Métrica Global | Valor |
|----------------|-------|
| **Total de predicciones** | 442,066 |
| **Accuracy** | 86.65% |
| **Número de clases** | 2 |

#### Métricas por Clase

| Clase | Precision | Recall | F1-Score | Soporte |
|-------|-----------|--------|----------|---------|
| NO_CLIENTE | 0.9912 | 0.8631 | 0.9227 | Mayoritario |
| CLIENTE | 0.3532 | 0.9068 | 0.5084 | Minoritario |

---

## 6. Gráficas de Validación

Las siguientes gráficas se encuentran en la carpeta `docs/evidencias_validacion/`:

### 6.1 Backtesting de Oficios
![Backtesting Oficios](evidencias_validacion/backtesting_oficios.png)

**Archivo:** `backtesting_oficios.png`

Serie temporal que muestra:
- Línea azul: Datos de entrenamiento (2023-05 a 2023-12)
- Puntos verdes: Valores reales del conjunto de prueba
- Línea roja punteada: Predicciones del modelo XGBoost
- Área sombreada: Período de validación

### 6.2 Backtesting de Demandados
![Backtesting Demandados](evidencias_validacion/backtesting_demandados.png)

**Archivo:** `backtesting_demandados.png`

### 6.3 Comparativa Real vs Predicción
![Comparativa](evidencias_validacion/comparativa_real_vs_prediccion.png)

**Archivo:** `comparativa_real_vs_prediccion.png`

Gráfico de barras lado a lado comparando valores reales (verde) vs predicciones (rojo) para cada mes del conjunto de validación.

### 6.4 Correlación Real vs Predicción
![Correlación](evidencias_validacion/correlacion_real_vs_prediccion.png)

**Archivo:** `correlacion_real_vs_prediccion.png`

Scatter plot con línea de ajuste perfecto (y=x) mostrando la correlación entre valores reales y predichos.

---

## 7. Análisis de Resultados

### 7.1 Modelos de Regresión

#### Limitaciones Identificadas

1. **Tamaño del histórico limitado:** Solo 17 meses de datos disponibles, con 8 meses para entrenamiento
2. **Alta variabilidad estacional:** Los datos muestran patrones estacionales complejos que el modelo no captura completamente
3. **R² negativo:** Indica que el modelo promedio supera las predicciones en algunos casos, sugiriendo necesidad de más datos

#### Factores que afectan el rendimiento

- Los primeros meses de 2024 tienen predicciones muy bajas debido a la extrapolación del modelo
- El modelo mejora su precisión a medida que se acerca a los datos de entrenamiento
- Septiembre 2024 muestra un pico atípico que el modelo no pudo anticipar

### 7.2 Modelos de Clasificación

#### Fortalezas

1. **Tipo de Embargo:** Excelente rendimiento (98.68% accuracy) con todas las clases principales bien clasificadas
2. **Estado de Embargo:** Rendimiento aceptable (77.45%) con algunas clases desbalanceadas
3. **Cliente:** Buen accuracy general (86.65%) pero con sesgo hacia la clase mayoritaria

#### Áreas de Mejora

- Clase `PROCESADO_CON_ERRORES` no tiene soporte suficiente para entrenamiento
- La clase `CLIENTE` tiene bajo precision debido al desbalance de clases

### 7.3 Recomendaciones

1. **Aumentar histórico:** Incorporar datos de semestres anteriores (2022, 2021)
2. **Feature engineering:** Agregar variables estacionales y de tendencia
3. **Balanceo de clases:** Aplicar técnicas de oversampling/undersampling para clasificación
4. **Validación cruzada:** Implementar k-fold cross validation para evaluación más robusta

---

## 8. Conclusiones

### Tests de Integridad
✅ **Todos los tests pasaron exitosamente**, demostrando que:
- Los módulos cargan correctamente los datos
- Las matrices de confusión se deserializan sin errores
- El pipeline de predicciones genera todos los archivos esperados

### Modelos de Clasificación
✅ **Rendimiento satisfactorio** para casos de uso de categorización:
- Tipo de Embargo: 98.68% accuracy
- Estado de Embargo: 77.45% accuracy
- Cliente: 86.65% accuracy

### Modelos de Regresión
⚠️ **Rendimiento limitado** debido a:
- Histórico de entrenamiento reducido (8 meses)
- Alta variabilidad en los datos
- MAPE promedio de 54-58%

### Valor del Sistema
A pesar de las limitaciones en predicción temporal, el sistema aporta valor significativo:
1. **Clasificación automatizada** de embargos con alta precisión
2. **Visualización interactiva** de tendencias históricas
3. **Framework escalable** que mejorará con más datos históricos

---

## Anexos

### A. Archivos Generados

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| `backtesting_oficios.png` | `docs/evidencias_validacion/` | Gráfica de backtesting oficios |
| `backtesting_demandados.png` | `docs/evidencias_validacion/` | Gráfica de backtesting demandados |
| `comparativa_real_vs_prediccion.png` | `docs/evidencias_validacion/` | Comparativa barras |
| `correlacion_real_vs_prediccion.png` | `docs/evidencias_validacion/` | Scatter plot correlación |
| `estadisticas_validacion.json` | `docs/evidencias_validacion/` | Estadísticas en formato JSON |

### B. Ejecución de Validación

Para regenerar las evidencias:

```bash
# Ejecutar tests de integridad
python tests/test_dashboard_load.py
python tests/test_matrices_load.py
python tests/test_predicciones_futuras.py

# Generar gráficas y estadísticas
python tests/generar_evidencias_validacion.py
```

### C. Configuración del Entorno

- **Python:** 3.12.10
- **pandas:** 2.x
- **scikit-learn:** 1.x
- **XGBoost:** 2.x
- **matplotlib:** 3.x

---

*Documento generado automáticamente por el sistema de validación*  
*Dashboard de Análisis de Embargos Bancarios v2.0*
