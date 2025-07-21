# Analisis Bancario

# Dashboard y modelos de machine learning para embargos bancarios

Proyecto para la consolidación, visualización interactiva y modelado predictivo de oficios bancarios (embargos, desembargos y requerimientos) usando Python. Este repositorio contiene scripts para la limpieza de datos, generación de muestras, creación de dashboards con Streamlit y entrenamiento de modelos de regresión y clasificación (XGBoost).


## Tabla de contenido

- [Descripción del proyecto](#descripción-del-proyecto)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Instalación y requisitos](#instalación-y-requisitos)
- [Uso y orden de ejecución](#uso-y-orden-de-ejecución)
- [Referencias](#referencias)
- [Licencia](#licencia)

---

## Descripción del proyecto

Este proyecto aborda la necesidad de organizar, estandarizar y predecir la carga operativa de embargos bancarios mensuales en el sector financiero colombiano. Aplica la metodología CRISP-DM para limpiar y consolidar los datos históricos de oficios bancarios, genera dashboards interactivos para análisis exploratorio y entrena modelos de machine learning para pronóstico y clasificación.

**Casos de uso:**
- Anticipar el volumen mensual de embargos y otros oficios por ciudad, banco y entidad remitente.
- Detectar estacionalidad y anomalías.
- Visualizar métricas y rankings relevantes para áreas legales, de riesgos y TI.

---

## Estructura del Repositorio

```text
practica-analisis-embargos/
├── dashboard_embargos.py                 # Dashboard exploratorio en Streamlit (embargos)
├── dashboard_predicciones.py             # Dashboard de predicciones y métricas
├── modelos_ml_embargos.ipynb             # Notebook Jupyter para consolidación, limpieza y modelos ML
├── embargos_consolidado_mensual.csv      # Dataset procesado y muestreado (generado por el notebook)
├── predicciones_oficios_por_mes.csv      # Resultados de predicción de oficios (generado por el notebook)
├── predicciones_demandados_por_mes.csv   # Resultados de predicción de demandados (generado por el notebook)
├── resultados_clasificaciones.csv        # Métricas de clasificación (generado por el notebook)
├── consulta detalle embargos-*.csv       # Archivos fuente originales (entrada, deben estar en la raíz)
├── requirements.txt                      # Dependencias del proyecto
└── README.md
```

## Instalación

## Instalación y requisitos

1. **Clona este repositorio:**
   ```sh
   git clone https://github.com/FaberOs/practica-analisis-embargos.git
   cd practica-analisis-embargos
   python -m venv venv
   venv\Scripts\activate  # En Windows
   # En Linux/Mac: source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Prepara los datasets fuente:**
   - Es necesario contar con los archivos CSV originales de los embargos bancarios, con el formato:
     - `consulta detalle embargos-*.csv` (por ejemplo: `consulta detalle embargos-2024-1.csv`, `consulta detalle embargos-2024-2.csv`, etc.)
   - Coloca estos archivos en la raíz del repositorio para que el procesamiento y los dashboards funcionen correctamente.

## Uso y orden de ejecución

**Importante:** El orden correcto para ejecutar el proyecto es el siguiente:

1. **Procesamiento y generación de datasets:**
   - Abre y ejecuta el notebook Jupyter `modelos_ml_embargos.ipynb`.
   - Este notebook realiza la consolidación, limpieza y entrenamiento de modelos, y genera los archivos CSV procesados necesarios para los dashboards:
     - `embargos_consolidado_mensual.csv`
     - `predicciones_oficios_por_mes.csv`
     - `predicciones_demandados_por_mes.csv`
     - `resultados_clasificaciones.csv`

2. **Dashboards interactivos:**
   - Una vez generados los CSV anteriores, puedes lanzar los dashboards para análisis exploratorio y visualización:
     - Para el dashboard de embargos:
       ```sh
       streamlit run dashboard_embargos.py
       ```
     - Para el dashboard de predicciones y métricas:
       ```sh
       streamlit run dashboard_predicciones.py
       ```
   - Ambos dashboards requieren los archivos CSV generados en el paso anterior.

---

## Referencias

- Guía CRISP-DM para predicción de embargos bancarios (PDF)
- Documentación XGBoost
- Géron, A. Hands-on Machine Learning with Scikit-Learn, Keras, and TensorFlow (O’Reilly, 2019)
- Raschka, S.; Mirjalili, V. Python Machine Learning (Packt, 2019)

## Licencia

MIT License. Desarrollado por Faber Ospina

