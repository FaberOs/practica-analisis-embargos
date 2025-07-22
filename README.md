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


## Instalación y requisitos

Antes de comenzar, asegúrate de cumplir con los siguientes requisitos:

1. **Tener Python instalado**
   - Se recomienda Python 3.8 o superior. Puedes descargarlo desde [python.org](https://www.python.org/downloads/).
   - Verifica la instalación ejecutando:
     ```sh
     python --version
     ```

2. **Clonar el repositorio y crear un entorno virtual:**
   ```sh
   git clone https://github.com/FaberOs/practica-analisis-embargos.git
   cd practica-analisis-embargos
   python -m venv venv
   venv\Scripts\activate  # En Windows
   # En Linux/Mac: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Instalar Jupyter Notebook** (recomendado para ejecutar el notebook de procesamiento):
   - Una vez activado el entorno virtual, instala Jupyter Notebook dentro de la carpeta del proyecto:
     ```sh
     pip install jupyter
     ```
   - Abre el notebook directamente ejecutando:
     ```sh
     jupyter notebook modelos_ml_embargos.ipynb
     ```
   - Se abrirá una ventana en tu navegador mostrando el notebook listo para ejecutar.
   - Ejecuta cada celda del notebook en orden (usando Shift+Enter o el botón de ejecutar) hasta completar el procesamiento y generación de los archivos CSV necesarios.


4. **Prepara los datasets fuente:**
   - Antes de ejecutar el notebook `modelos_ml_embargos.ipynb`, asegúrate de tener los archivos CSV originales de los embargos bancarios en la carpeta raíz del repositorio, con el formato:
     - `consulta detalle embargos-*.csv` (por ejemplo: `consulta detalle embargos-2024-01.csv`, `consulta detalle embargos-2024-02.csv`, etc.)
   - Si estos archivos no están presentes, el notebook no podrá procesar ni generar los datasets necesarios para los dashboards.

---


## Uso y orden de ejecución

Sigue estos pasos para ejecutar el proyecto correctamente:

1. **Preparar los datos fuente:**
   - Coloca todos los archivos `consulta detalle embargos-*.csv` en la carpeta raíz del repositorio antes de abrir el notebook.

2. **Procesar y generar datasets:**
   - Abre el notebook Jupyter `modelos_ml_embargos.ipynb` ejecutando:
     ```sh
     jupyter notebook modelos_ml_embargos.ipynb
     ```
   - Ejecuta cada celda en orden (usando Shift+Enter o el botón de ejecutar). El notebook consolidará, limpiará y procesará los datos, generando los siguientes archivos CSV:
     - `embargos_consolidado_mensual.csv`
     - `predicciones_oficios_por_mes.csv`
     - `predicciones_demandados_por_mes.csv`
     - `resultados_clasificaciones.csv`

3. **Ejecutar los dashboards interactivos:**
   - Una vez generados los archivos CSV anteriores, puedes lanzar los dashboards para análisis exploratorio y visualización:
     - Para el dashboard de embargos:
       ```sh
       streamlit run dashboard_embargos.py
       ```
     - Para el dashboard de predicciones y métricas:
       ```sh
       streamlit run dashboard_predicciones.py
       ```
   - Ambos dashboards requieren los archivos CSV generados en el paso anterior y deben estar en la carpeta raíz.

---

## Referencias

- Guía CRISP-DM para predicción de embargos bancarios (PDF)
- Documentación XGBoost
- Géron, A. Hands-on Machine Learning with Scikit-Learn, Keras, and TensorFlow (O’Reilly, 2019)
- Raschka, S.; Mirjalili, V. Python Machine Learning (Packt, 2019)

## Licencia

MIT License. Desarrollado por Faber Ospina

