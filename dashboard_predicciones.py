import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import json
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

if getattr(sys, 'frozen', False):
    if hasattr(sys, '_MEIPASS'):
        if sys._MEIPASS not in sys.path:
            sys.path.insert(0, sys._MEIPASS)
    exe_dir = os.path.dirname(sys.executable)
    if exe_dir not in sys.path:
        sys.path.insert(0, exe_dir)

try:
    from utils_csv import get_csv_path, find_csv_file, get_data_path, get_base_path
except ImportError as e:
    # Fallback si no se puede importar utils_csv
    st.warning(f"No se pudo importar utils_csv: {e}")
    def get_csv_path(filename, required=True):
        # Buscar en ubicaciones comunes
        search_paths = [
            os.path.join(os.getenv('APPDATA', ''), "DashboardEmbargos", "datos"),
            os.path.dirname(os.path.abspath(__file__)),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos"),
            os.getcwd(),
        ]
        for path in search_paths:
            if path:
                file_path = os.path.join(path, filename)
                if os.path.exists(file_path):
                    return file_path
        if required:
            st.error(f"No se encontró el archivo: {filename}")
            st.info(f"Coloca el archivo '{filename}' en la misma carpeta del programa o en una subcarpeta 'datos'")
        return None
    
    def find_csv_file(filename):
        return get_csv_path(filename, required=False)
    
    def get_data_path():
        appdata = os.getenv('APPDATA')
        if appdata:
            return os.path.join(appdata, "DashboardEmbargos", "datos")
        return os.path.dirname(os.path.abspath(__file__))
    
    def get_base_path():
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="Oficios Bancarios",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === DICCIONARIO DE AYUDAS CONTEXTUALES (TOOLTIPS) ===
HELPS = {
    "mae": "Error Absoluto Medio (MAE): Promedio de la magnitud de los errores. Indica cuánto se equivoca el modelo en promedio (en unidades originales). Menor es mejor.",
    "rmse": "Raíz del Error Cuadrático Medio (RMSE): Similar a MAE pero penaliza más los errores grandes. Útil para detectar predicciones muy desviadas. Menor es mejor.",
    "mape": "Error Porcentual Absoluto Medio (MAPE): Error promedio expresado como porcentaje del valor real. Permite comparar modelos de diferentes escalas. <10% es excelente, <20% aceptable, >20% requiere mejora.",
    "residuos": "Residuales: Diferencia entre valor real y predicción (Real - Pred). Residuos aleatorios indican buen modelo. Patrones sistemáticos (todos positivos o negativos) indican problemas del modelo.",
    "f1_score": "F1-Score: Métrica balanceada entre precisión y recall. Rango de 0 a 1, donde 1.0 = perfecto, 0.5 = regular, <0.3 = malo.",
    "precision": "Precisión: De todos los casos que el modelo predijo como positivos, ¿cuántos realmente lo eran? Alta precisión = pocas falsas alarmas.",
    "recall": "Recall (Sensibilidad): De todos los casos reales positivos, ¿cuántos detectó el modelo? Alto recall = detecta la mayoría de casos positivos.",
    "matriz_confusion": "Matriz de Confusión: Tabla que muestra aciertos (diagonal) y confusiones (fuera de diagonal) del clasificador. Diagonal oscura = buen modelo. Permite identificar qué clases se confunden entre sí.",
}

# === ESTILOS CSS PERSONALIZADOS (paleta personalizada) ===
st.markdown("""
<style>
    /* Variables de color */
    :root {
        --color-primary: #bfe084;
        --color-secondary: #3c8198;
        --color-tertiary: #424e71;
        --color-quaternary: #252559;
    }
    
    /* Sidebar personalizado */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #bfe084 0%, #3c8198 25%, #424e71 75%, #252559 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: white !important;
    }
    
    /* Botones del sidebar - navegación */
    [data-testid="stSidebar"] button {
        background-color: transparent !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        text-align: left !important;
        padding: 0.6rem 1rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s !important;
        justify-content: flex-start !important;
    }
    
    [data-testid="stSidebar"] button p {
        text-align: left !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(191, 224, 132, 0.1) !important;
        color: white !important;
    }
    
    [data-testid="stSidebar"] button:active,
    [data-testid="stSidebar"] button:focus {
        background-color: rgba(191, 224, 132, 0.2) !important;
        color: #bfe084 !important;
        box-shadow: none !important;
        font-weight: 600 !important;
    }
    
    /* Estado activo para botones seleccionados */
    [data-testid="stSidebar"] button[aria-pressed="true"],
    [data-testid="stSidebar"] button.active {
        color: #bfe084 !important;
        background-color: rgba(191, 224, 132, 0.15) !important;
        font-weight: 600 !important;
    }
    
    /* Navegación personalizada en sidebar */
    .nav-item {
        color: white;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.3s;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        font-size: 1rem;
        font-weight: 500;
    }
    
    .nav-item:hover {
        background-color: rgba(191, 224, 132, 0.1);
    }
    
    .nav-item.active {
        color: #bfe084;
        background-color: rgba(191, 224, 132, 0.05);
    }
    
    /* Cards de métricas mejoradas */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border-left: 5px solid;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3c8198, #bfe084);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    .metric-card:hover::before {
        transform: scaleX(1);
    }
    
    /* Métricas con gradientes - Paleta personalizada */
    .metric-card-1 { border-left-color: #bfe084; }
    .metric-card-2 { border-left-color: #3c8198; }
    .metric-card-3 { border-left-color: #424e71; }
    .metric-card-4 { border-left-color: #252559; }
    .metric-card-5 { border-left-color: #bfe084; }
    
    /* Styling para st.metric */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: bold !important;
        background: linear-gradient(135deg, #3c8198, #424e71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #424e71 !important;
        font-weight: 600 !important;
    }
    
    /* Secciones de contenido */
    .content-section {
        background: rgba(60, 129, 152, 0.05);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border: 1px solid rgba(60, 129, 152, 0.1);
    }
    .section-title {
        font-size: 1.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #3c8198, #424e71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid;
        border-image: linear-gradient(90deg, #3c8198, #bfe084) 1;
    }
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(60, 129, 152, 0.1);
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(60, 129, 152, 0.1);
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
        color: #424e71;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3c8198, #424e71);
        color: white;
        box-shadow: 0 4px 12px rgba(60, 129, 152, 0.3);
    }
    
    /* Filtros */
    .filter-chip {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        background: rgba(60, 129, 152, 0.1);
        border-radius: 20px;
        border: 1px solid rgba(60, 129, 152, 0.3);
        cursor: pointer;
        transition: all 0.3s;
    }
    .filter-chip:hover {
        background: #bfe084;
        color: #252559;
        transform: scale(1.05);
    }
    .filter-chip.active {
        background: #3c8198;
        color: white;
        border-color: #3c8198;
        box-shadow: 0 2px 8px rgba(60, 129, 152, 0.4);
    }
    .filter-section {
        background: rgba(60, 129, 152, 0.1);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .filter-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #252559;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .toggle-button {
        background: rgba(60, 129, 152, 0.1);
        border: 2px solid rgba(60, 129, 152, 0.3);
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.3s;
        font-size: 0.9rem;
        color: #424e71;
    }
    .toggle-button:hover {
        border-color: #bfe084;
        color: #3c8198;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(191, 224, 132, 0.2);
    }
    .toggle-button.active {
        background: linear-gradient(135deg, #3c8198 0%, #424e71 100%);
        color: white;
        border-color: transparent;
        box-shadow: 0 4px 12px rgba(60, 129, 152, 0.4);
    }
    .filter-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 0.8rem;
        margin: 0.2rem;
        background: rgba(60, 129, 152, 0.1);
        border-radius: 20px;
        font-size: 0.85rem;
        color: #424e71;
        border: 1px solid rgba(60, 129, 152, 0.3);
    }
    .filter-badge.active {
        background: #3c8198;
        color: white;
        border-color: #3c8198;
    }
    /* Tarjetas informativas para validación */
    .validation-card {
        background: rgba(59, 130, 246, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .validation-card h4 {
        margin-top: 0;
        margin-bottom: 0.5rem;
        color: #1d3a8a;
        font-size: 1.1rem;
    }
    .validation-card p {
        margin-bottom: 0.6rem;
        color: #252559;
        line-height: 1.5;
    }
    .validation-card ul {
        padding-left: 1.1rem;
        margin: 0.5rem 0 0;
        color: #1f2937;
    }
    .validation-card li {
        margin-bottom: 0.3rem;
    }
    .validation-badge {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }
    .validation-pill {
        display: block;
        padding: 0.6rem 0.8rem;
        border-radius: 10px;
        background: rgba(191, 224, 132, 0.2);
        color: #1e293b;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .validation-pill.warning {
        background: rgba(254, 243, 199, 0.6);
        color: #92400e;
    }
    .validation-pill.danger {
        background: rgba(254, 226, 226, 0.7);
        color: #991b1b;
    }
    
    /* Animaciones suaves */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Mejoras generales */
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
    }
    
    /* Cards de gráficos */
    .chart-card {
        background: rgba(60, 129, 152, 0.05);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(60, 129, 152, 0.1);
    }
    
    /* Estilos para headers y secciones */
    h1, h2, h3 {
        color: #252559;
    }
    
    /* Separadores */
    .separator {
        height: 2px;
        background: linear-gradient(90deg, transparent, #3c8198, #bfe084, transparent);
        margin: 2rem 0;
        border-radius: 2px;
    }
    
    /* Multiselect dark mode */
    [data-baseweb="select"] {
        background-color: rgba(60, 129, 152, 0.1) !important;
    }
    
    [data-baseweb="tag"] {
        background-color: #3c8198 !important;
        color: white !important;
    }
    
    [data-baseweb="tag"] svg {
        fill: white !important;
    }
    
    /* Selectbox styling */
    [data-baseweb="popover"] {
        background-color: white !important;
        border: 1px solid rgba(60, 129, 152, 0.3) !important;
    }
    
    [role="option"] {
        background-color: transparent !important;
        color: #252559 !important;
    }
    
    [role="option"]:hover {
        background-color: rgba(191, 224, 132, 0.2) !important;
        color: #252559 !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar simplificado
with st.sidebar:
    st.markdown("""
    <div style='margin-bottom: 2rem; margin-top: 1rem;'>
        <div style='font-size: 2rem; font-weight: 700; line-height: 1.2; text-align: left;'>
            <div style='color: #252559;'>OFICIOS</div>
            <div style='color: white;'>BANCARIOS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navegación personalizada sin radio buttons
    st.markdown("""<p style='color: white; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; margin-top: 1rem;'>PREDICCIONES</p>""", unsafe_allow_html=True)
    
    # Usar session state para mantener la selección
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "Oficios"
    
    # Crear botones personalizados para navegación
    if st.button("Oficios", key="nav_oficios", use_container_width=True):
        st.session_state.selected_tab = "Oficios"
    
    if st.button("Demandados", key="nav_demandados", use_container_width=True):
        st.session_state.selected_tab = "Demandados"
    
    if st.button("Validación Histórica", key="nav_validacion", use_container_width=True):
        st.session_state.selected_tab = "Validación Histórica"
    
    if st.button("Métricas de Clasificación", key="nav_metricas", use_container_width=True):
        st.session_state.selected_tab = "Métricas de Clasificación"
    
    selected_tab = st.session_state.selected_tab

# --- Carga optimizada de datos con caché ---
@st.cache_data(show_spinner="Cargando datos...", ttl=600, hash_funcs={type(None): lambda x: None})
def load_csv(name, _file_mtime=None):
    """Carga CSV con optimizaciones avanzadas y detección automática de codificación"""
    # Buscar el archivo usando find_csv_file primero
    csv_path = find_csv_file(name)
    
    # Si no se encuentra, verificar específicamente en AppData en Windows
    if csv_path is None and os.name == 'nt':  # Windows
        appdata = os.getenv('APPDATA')
        if appdata:
            appdata_path = os.path.join(appdata, "DashboardEmbargos", "datos", name)
            if os.path.exists(appdata_path):
                csv_path = appdata_path
    
    # Si aún no se encuentra, usar get_csv_path para mostrar error
    if csv_path is None:
        csv_path = get_csv_path(name, required=True)
        if csv_path is None:
            st.stop()
    
    # Detectar codificación primero (más rápido que probar todas)
    detected_encoding = None
    try:
        import chardet
        with open(csv_path, 'rb') as f:
            raw_data = f.read(10000)  # Leer solo los primeros 10KB para detectar
            result = chardet.detect(raw_data)
            if result and result['encoding']:
                detected_encoding = result['encoding']
    except ImportError:
        # chardet no está instalado, continuar sin detección
        pass
    except:
        pass
    
    # Lista de codificaciones a probar (empezar con la detectada)
    encodings = []
    if detected_encoding:
        encodings.append(detected_encoding)
    encodings.extend(['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8-sig'])
    # Eliminar duplicados manteniendo el orden
    encodings = list(dict.fromkeys(encodings))
    
    df = None
    
    # Definir tipos de datos optimizados según el archivo
    dtype_dict = {}
    if "oficios" in name.lower():
        dtype_dict = {'mes': 'category'}
    elif "demandados" in name.lower():
        dtype_dict = {'mes': 'category'}
    elif "clasificaciones" in name.lower():
        # Especificar tipos para clasificaciones
        # NO especificar dtype para matriz_confusion y clases_matriz (dejar que pandas las detecte automáticamente)
        dtype_dict = {
            'modelo': 'category', 
            'clase': 'category'
            # matriz_confusion y clases_matriz se leerán automáticamente como object (string)
        }
    
    # Intentar leer con diferentes codificaciones
    for encoding in encodings:
        try:
            df = pd.read_csv(
                csv_path, 
                low_memory=False, 
                encoding=encoding,
                dtype=dtype_dict,
                engine='c'  # Parser C más rápido
            )
            # Limpiar nombres de columnas (eliminar espacios y caracteres especiales)
            df.columns = df.columns.str.strip()
            
            # Aplicar tipos solo si las columnas existen (por si dtype no funcionó)
            if "oficios" in name.lower() and 'mes' in df.columns and df['mes'].dtype != 'category':
                df['mes'] = df['mes'].astype('category')
            elif "demandados" in name.lower() and 'mes' in df.columns and df['mes'].dtype != 'category':
                df['mes'] = df['mes'].astype('category')
            elif "clasificaciones" in name.lower():
                if 'modelo' in df.columns and df['modelo'].dtype != 'category':
                    df['modelo'] = df['modelo'].astype('category')
                if 'clase' in df.columns and df['clase'].dtype != 'category':
                    df['clase'] = df['clase'].astype('category')
            return df
        except UnicodeDecodeError:
            continue
        except Exception:
            # Si es otro error, intentar con la siguiente codificación
            continue
    
    # Si ninguna codificación funcionó, intentar con manejo de errores
    if df is None:
        try:
            df = pd.read_csv(
                csv_path, 
                low_memory=False, 
                encoding_errors='replace',
                dtype=dtype_dict,
                engine='c'
            )
            # Limpiar nombres de columnas
            df.columns = df.columns.str.strip()
            # Aplicar tipos después
            if "oficios" in name.lower() and 'mes' in df.columns:
                df['mes'] = df['mes'].astype('category')
            elif "demandados" in name.lower() and 'mes' in df.columns:
                df['mes'] = df['mes'].astype('category')
            elif "clasificaciones" in name.lower():
                if 'modelo' in df.columns:
                    df['modelo'] = df['modelo'].astype('category')
                if 'clase' in df.columns:
                    df['clase'] = df['clase'].astype('category')
            return df
        except Exception as e:
            st.error(f"Error al cargar {name}: {e}")
            st.stop()
            return None
    
    return df

# Cargar datos con spinner
with st.spinner("Cargando datos de predicciones..."):
    try:
        # Obtener timestamps de archivos para invalidar caché si cambian
        import time
        def get_file_mtime(filename):
            try:
                path = find_csv_file(filename)
                if path and os.path.exists(path):
                    return os.path.getmtime(path)
            except:
                pass
            return None
        
        # Cargar archivos de validación histórica
        df_oficios_val = load_csv("predicciones_oficios_validacion.csv", _file_mtime=get_file_mtime("predicciones_oficios_validacion.csv"))
        df_demandados_val = load_csv("predicciones_demandados_validacion.csv", _file_mtime=get_file_mtime("predicciones_demandados_validacion.csv"))
        
        # Cargar archivos de predicciones futuras
        df_oficios_futuro = load_csv("predicciones_oficios_futuro.csv", _file_mtime=get_file_mtime("predicciones_oficios_futuro.csv"))
        df_demandados_futuro = load_csv("predicciones_demandados_futuro.csv", _file_mtime=get_file_mtime("predicciones_demandados_futuro.csv"))
        
        # Cargar métricas de clasificación
        df_metricas = load_csv("resultados_clasificaciones.csv", _file_mtime=get_file_mtime("resultados_clasificaciones.csv"))
        
        # Columnas cargadas correctamente
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

# Renderizar contenido según selección del sidebar
if selected_tab == "Oficios":
    st.markdown("""
    <div class="section-title fade-in">
        Predicciones Futuras - Oficios
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 1rem; color: #424e71; margin-bottom: 1.5rem; padding: 1rem; background: rgba(60, 129, 152, 0.15); border-radius: 10px; border-left: 4px solid #3c8198;'>
        Proyección del <b>número de oficios esperados</b> para los próximos 12 meses, con intervalos de confianza.<br>
        <b>Predicción</b>: Valor más probable basado en patrones históricos<br>
        <b>Intervalo de confianza</b>: Rango donde se espera que caiga el valor real (95% de probabilidad)<br>
        <b>Nivel de confianza</b>: Alta (1-3 meses), Media (4-6 meses), Baja (7-12 meses)
    </div>
    """, unsafe_allow_html=True)
    
    # Validar que las columnas necesarias existan
    required_cols = ['mes', 'pred_oficios', 'limite_inferior', 'limite_superior', 'nivel_confianza']
    missing_cols = [col for col in required_cols if col not in df_oficios_futuro.columns]
    
    if missing_cols:
        st.error(f"El archivo de predicciones futuras no tiene las columnas esperadas.")
        st.info(f"**Columnas requeridas:** {', '.join(required_cols)}")
        st.info(f"**Columnas encontradas:** {', '.join(df_oficios_futuro.columns.tolist())}")
        st.warning("Verifica que el proceso de generación de predicciones se haya completado correctamente.")
        st.stop()
    
    # === KPIs DE PREDICCIONES FUTURAS ===
    st.markdown("### Indicadores Clave de Predicción")
    
    col1, col2, col3 = st.columns(3)
    
    # Próximo mes
    proximo_mes = df_oficios_futuro.iloc[0]
    col1.metric(
        label=f"Próximo Mes ({proximo_mes['mes']})",
        value=f"{int(proximo_mes['pred_oficios'])} oficios",
        delta=f"± {int((proximo_mes['limite_superior'] - proximo_mes['limite_inferior']) / 2)}",
        help=f"Predicción para el próximo mes con nivel de confianza {proximo_mes['nivel_confianza']}"
    )
    
    # Próximos 3 meses
    proximos_3_meses = df_oficios_futuro.head(3)['pred_oficios'].sum()
    col2.metric(
        label="Próximos 3 Meses",
        value=f"{int(proximos_3_meses)} oficios",
        help="Suma de predicciones para los próximos 3 meses (alta confianza)"
    )
    
    # Proyección anual
    proyeccion_anual = df_oficios_futuro['pred_oficios'].sum()
    col3.metric(
        label="Proyección Anual (12 meses)",
        value=f"{int(proyeccion_anual)} oficios",
        help="Suma total de predicciones para los próximos 12 meses"
    )
    
    # === GRÁFICO CON BANDAS DE CONFIANZA ===
    st.markdown("---")
    st.markdown("### Evolución de Predicciones con Intervalos de Confianza")
    
    import plotly.graph_objects as go
    
    fig_futuro = go.Figure()
    
    # Banda de confianza (área sombreada)
    fig_futuro.add_trace(go.Scatter(
        x=df_oficios_futuro['mes'],
        y=df_oficios_futuro['limite_superior'],
        fill=None,
        mode='lines',
        line=dict(color='rgba(68, 68, 68, 0)'),
        showlegend=False,
        name='Límite Superior'
    ))
    
    fig_futuro.add_trace(go.Scatter(
        x=df_oficios_futuro['mes'],
        y=df_oficios_futuro['limite_inferior'],
        fill='tonexty',
        mode='lines',
        line=dict(color='rgba(68, 68, 68, 0)'),
        fillcolor='rgba(60, 129, 152, 0.2)',
        name='Intervalo de Confianza',
        showlegend=True
    ))
    
    # Línea de predicción
    fig_futuro.add_trace(go.Scatter(
        x=df_oficios_futuro['mes'],
        y=df_oficios_futuro['pred_oficios'],
        mode='lines+markers',
        name='Predicción',
        line=dict(color='#3c8198', width=3),
        marker=dict(size=8, color='#3c8198')
    ))
    
    fig_futuro.update_layout(
        title="Predicciones Futuras de Oficios (12 Meses)",
        xaxis_title="Mes",
        yaxis_title="Cantidad de Oficios",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_futuro, use_container_width=True)
    
    # === TABLA DE PREDICCIONES ===
    st.markdown("---")
    st.markdown("### Detalle de Predicciones Mensuales")
    
    # Formatear dataframe para visualización)
    df_display = df_oficios_futuro.copy()
    df_display['pred_oficios'] = df_display['pred_oficios'].astype(int)
    df_display['limite_inferior'] = df_display['limite_inferior'].astype(int)
    df_display['limite_superior'] = df_display['limite_superior'].astype(int)
    df_display['intervalo'] = df_display.apply(
        lambda row: f"[{row['limite_inferior']} - {row['limite_superior']}]", 
        axis=1
    )
    
    # Reordenar columnas
    df_display = df_display[['mes', 'pred_oficios', 'intervalo', 'nivel_confianza', 'horizonte_meses']]
    df_display.columns = ['Mes', 'Predicción', 'Intervalo 95%', 'Confianza', 'Horizonte (meses)']
    
    # Aplicar estilo con colores según nivel de confianza
    def color_confianza(val):
        if val == 'Alta':
            return 'background-color: #d1fae5; color: #065f46'
        elif val == 'Media':
            return 'background-color: #fef3c7; color: #92400e'
        else:
            return 'background-color: #fee2e2; color: #991b1b'
    
    styled_df = df_display.style.map(
        color_confianza, 
        subset=['Confianza']
    ).background_gradient(
        subset=['Predicción'],
        cmap='Blues'
    )
    
    st.dataframe(styled_df, use_container_width=True, height=450)
    
    # === INTERPRETACIÓN Y RECOMENDACIONES ===
    st.markdown("---")
    st.markdown("### Interpretación y Recomendaciones")
    
    # Calcular tendencia
    tendencia_3m = proximos_3_meses / 3
    tendencia_9_12m = df_oficios_futuro.tail(4)['pred_oficios'].mean()
    
    col_int1, col_int2 = st.columns(2)
    
    with col_int1:
        st.markdown("<h4 style='color: #3c8198;'>Análisis de Tendencia</h4>", unsafe_allow_html=True)
        
        if tendencia_9_12m > tendencia_3m:
            st.markdown(f"**Tendencia Creciente**: Se espera un aumento gradual de {tendencia_3m:.0f} oficios/mes (corto plazo) a {tendencia_9_12m:.0f} oficios/mes (largo plazo).")
        elif tendencia_9_12m < tendencia_3m:
            st.markdown(f"**Tendencia Decreciente**: Se espera una disminución de {tendencia_3m:.0f} oficios/mes (corto plazo) a {tendencia_9_12m:.0f} oficios/mes (largo plazo).")
        else:
            st.markdown(f"**Tendencia Estable**: Se espera mantener aproximadamente {tendencia_3m:.0f} oficios/mes durante los próximos 12 meses.")
    
    with col_int2:
        st.markdown("<h4 style='color: #bfe084;'>Recomendaciones</h4>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <b>Planificación de recursos</b>: Considerar {int(proximo_mes['pred_oficios'])} oficios para el próximo mes<br>
        <b>Presupuesto trimestral</b>: Preparar capacidad para {int(proximos_3_meses)} oficios<br>
        <b>Revisión mensual</b>: Actualizar predicciones con datos reales para mejorar precisión<br>
        <b>Alertas</b>: Monitorear si valores reales caen fuera del intervalo de confianza
        """, unsafe_allow_html=True)
    
    # Descarga de datos
    st.markdown("---")
    st.download_button(
        "Descargar Predicciones Futuras (CSV)", 
        df_oficios_futuro.to_csv(index=False).encode("utf-8"),
        file_name="predicciones_oficios_futuro.csv",
        mime="text/csv"
    )

# 2. PREDICCIONES FUTURAS DE DEMANDADOS (12 meses adelante)
elif selected_tab == "Demandados":
    st.markdown("""
    <div class="section-title fade-in">
        Predicciones Futuras - Demandados
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 1rem; color: #424e71; margin-bottom: 1.5rem; padding: 1rem; background: rgba(191, 224, 132, 0.15); border-radius: 10px; border-left: 4px solid #bfe084;'>
        Proyección del <b>número de demandados únicos esperados</b> para los próximos 12 meses, con intervalos de confianza.<br>
        <b>Predicción</b>: Valor más probable basado en patrones históricos<br>
        <b>Intervalo de confianza</b>: Rango donde se espera que caiga el valor real (95% de probabilidad)<br>
        <b>Nivel de confianza</b>: Alta (1-3 meses), Media (4-6 meses), Baja (7-12 meses)
    </div>
    """, unsafe_allow_html=True)
    
    # Validar que las columnas necesarias existan
    required_cols = ['mes', 'pred_demandados', 'limite_inferior', 'limite_superior', 'nivel_confianza']
    missing_cols = [col for col in required_cols if col not in df_demandados_futuro.columns]
    
    if missing_cols:
        st.error(f"El archivo de predicciones futuras no tiene las columnas esperadas.")
        st.info(f"**Columnas requeridas:** {', '.join(required_cols)}")
        st.info(f"**Columnas encontradas:** {', '.join(df_demandados_futuro.columns.tolist())}")
        st.warning("Verifica que el proceso de generación de predicciones se haya completado correctamente.")
        st.stop()
    
    # === KPIs DE PREDICCIONES FUTURAS ===
    st.markdown("### Indicadores Clave de Predicción")
    
    col1, col2, col3 = st.columns(3)
    
    # Próximo mes
    proximo_mes_dem = df_demandados_futuro.iloc[0]
    col1.metric(
        label=f"Próximo Mes ({proximo_mes_dem['mes']})",
        value=f"{int(proximo_mes_dem['pred_demandados'])} demandados",
        delta=f"± {int((proximo_mes_dem['limite_superior'] - proximo_mes_dem['limite_inferior']) / 2)}",
        help=f"Predicción para el próximo mes con nivel de confianza {proximo_mes_dem['nivel_confianza']}"
    )
    
    # Próximos 3 meses
    proximos_3_meses_dem = df_demandados_futuro.head(3)['pred_demandados'].sum()
    col2.metric(
        label="Próximos 3 Meses",
        value=f"{int(proximos_3_meses_dem)} demandados",
        help="Suma de predicciones para los próximos 3 meses (alta confianza)"
    )
    
    # Proyección anual
    proyeccion_anual_dem = df_demandados_futuro['pred_demandados'].sum()
    col3.metric(
        label="Proyección Anual (12 meses)",
        value=f"{int(proyeccion_anual_dem)} demandados",
        help="Suma total de predicciones para los próximos 12 meses"
    )
    
    # === GRÁFICO CON BANDAS DE CONFIANZA ===
    st.markdown("---")
    st.markdown("### Evolución de Predicciones con Intervalos de Confianza")
    
    import plotly.graph_objects as go
    
    fig_futuro_dem = go.Figure()
    
    # Banda de confianza (área sombreada)
    fig_futuro_dem.add_trace(go.Scatter(
        x=df_demandados_futuro['mes'],
        y=df_demandados_futuro['limite_superior'],
        fill=None,
        mode='lines',
        line=dict(color='rgba(68, 68, 68, 0)'),
        showlegend=False,
        name='Límite Superior'
    ))
    
    fig_futuro_dem.add_trace(go.Scatter(
        x=df_demandados_futuro['mes'],
        y=df_demandados_futuro['limite_inferior'],
        fill='tonexty',
        mode='lines',
        line=dict(color='rgba(68, 68, 68, 0)'),
        fillcolor='rgba(191, 224, 132, 0.2)',
        name='Intervalo de Confianza',
        showlegend=True
    ))
    
    # Línea de predicción
    fig_futuro_dem.add_trace(go.Scatter(
        x=df_demandados_futuro['mes'],
        y=df_demandados_futuro['pred_demandados'],
        mode='lines+markers',
        name='Predicción',
        line=dict(color='#bfe084', width=3),
        marker=dict(size=8, color='#bfe084')
    ))
    
    fig_futuro_dem.update_layout(
        title="Predicciones Futuras de Demandados (12 Meses)",
        xaxis_title="Mes",
        yaxis_title="Cantidad de Demandados",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_futuro_dem, use_container_width=True)
    
    # === TABLA DE PREDICCIONES ===
    st.markdown("---")
    st.markdown("### Detalle de Predicciones Mensuales")
    
    # Formatear dataframe para visualización
    df_display_dem = df_demandados_futuro.copy()
    df_display_dem['pred_demandados'] = df_display_dem['pred_demandados'].astype(int)
    df_display_dem['limite_inferior'] = df_display_dem['limite_inferior'].astype(int)
    df_display_dem['limite_superior'] = df_display_dem['limite_superior'].astype(int)
    df_display_dem['intervalo'] = df_display_dem.apply(
        lambda row: f"[{row['limite_inferior']} - {row['limite_superior']}]", 
        axis=1
    )
    
    # Reordenar columnas
    df_display_dem = df_display_dem[['mes', 'pred_demandados', 'intervalo', 'nivel_confianza', 'horizonte_meses']]
    df_display_dem.columns = ['Mes', 'Predicción', 'Intervalo 95%', 'Confianza', 'Horizonte (meses)']
    
    # Aplicar estilo con colores según nivel de confianza
    def color_confianza_dem(val):
        if val == 'Alta':
            return 'background-color: #d1fae5; color: #065f46'
        elif val == 'Media':
            return 'background-color: #fef3c7; color: #92400e'
        else:
            return 'background-color: #fee2e2; color: #991b1b'
    
    styled_df_dem = df_display_dem.style.map(
        color_confianza_dem, 
        subset=['Confianza']
    ).background_gradient(
        subset=['Predicción'],
        cmap='Reds'
    )
    
    st.dataframe(styled_df_dem, use_container_width=True, height=450)
    
    # === INTERPRETACIÓN Y RECOMENDACIONES ===
    st.markdown("---")
    st.markdown("### Interpretación y Recomendaciones")
    
    # Calcular tendencia
    tendencia_3m_dem = proximos_3_meses_dem / 3
    tendencia_9_12m_dem = df_demandados_futuro.tail(4)['pred_demandados'].mean()
    
    col_int1, col_int2 = st.columns(2)
    
    with col_int1:
        st.markdown("<h4 style='color: #3c8198;'>Análisis de Tendencia</h4>", unsafe_allow_html=True)
        
        if tendencia_9_12m_dem > tendencia_3m_dem:
            st.markdown(f"**Tendencia Creciente**: Se espera un aumento gradual de {tendencia_3m_dem:.0f} demandados/mes (corto plazo) a {tendencia_9_12m_dem:.0f} demandados/mes (largo plazo).")
        elif tendencia_9_12m_dem < tendencia_3m_dem:
            st.markdown(f"**Tendencia Decreciente**: Se espera una disminución de {tendencia_3m_dem:.0f} demandados/mes (corto plazo) a {tendencia_9_12m_dem:.0f} demandados/mes (largo plazo).")
        else:
            st.markdown(f"**Tendencia Estable**: Se espera mantener aproximadamente {tendencia_3m_dem:.0f} demandados/mes durante los próximos 12 meses.")
    
    with col_int2:
        st.markdown("<h4 style='color: #bfe084;'>Recomendaciones</h4>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <b>Gestión de casos</b>: Preparar capacidad para {int(proximo_mes_dem['pred_demandados'])} demandados el próximo mes<br>
        <b>Recursos legales</b>: Planificar atención para {int(proximos_3_meses_dem)} demandados en 3 meses<br>
        <b>Revisión mensual</b>: Actualizar predicciones con datos reales para mejorar precisión<br>
        <b>Alertas</b>: Monitorear si valores reales caen fuera del intervalo de confianza
        """, unsafe_allow_html=True)
    
    # Descarga de datos
    st.markdown("---")
    st.download_button(
        "Descargar Predicciones Futuras (CSV)", 
        df_demandados_futuro.to_csv(index=False).encode("utf-8"),
        file_name="predicciones_demandados_futuro.csv",
        mime="text/csv"
    )

# 3. VALIDACIÓN HISTÓRICA DEL MODELO
elif selected_tab == "Validación Histórica":
    st.markdown("""
    <div class="section-title fade-in">
        Validación Histórica del Modelo
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 1rem; color: #424e71; margin-bottom: 1.5rem; padding: 1rem; background: rgba(66, 78, 113, 0.15); border-radius: 10px; border-left: 4px solid #424e71;'>
        Evaluación del <b>rendimiento del modelo</b> comparando predicciones contra valores reales del último año.<br>
        Esta sección muestra qué tan bien el modelo predice valores conocidos, lo cual indica su confiabilidad para predicciones futuras.
    </div>
    """, unsafe_allow_html=True)
    
    # === OFICIOS: VALIDACIÓN HISTÓRICA ===
    st.markdown("## Oficios por Mes - Validación Histórica")
    
    # Validar columnas
    if 'mes' in df_oficios_val.columns and 'real_oficios' in df_oficios_val.columns and 'pred_oficios' in df_oficios_val.columns:
        # Gráfico comparativo
        fig_val_oficios = px.line(
            df_oficios_val,
            x="mes",
            y=["real_oficios", "pred_oficios"],
            markers=True,
            labels={"value": "Cantidad de oficios", "variable": "Serie"},
            title="Oficios: Real vs Predicción (Año de Validación)",
            color_discrete_sequence=['#424e71', '#3c8198']
        )
        fig_val_oficios.update_traces(line=dict(width=3))
        fig_val_oficios.update_layout(height=400)
        st.plotly_chart(fig_val_oficios, use_container_width=True)
        
        # Métricas de error
        col1, col2, col3 = st.columns(3)
        
        mae_oficios = (df_oficios_val['real_oficios'] - df_oficios_val['pred_oficios']).abs().mean()
        col1.metric("MAE", f"{mae_oficios:.2f}", help="Error Absoluto Medio")
        
        rmse_oficios = np.sqrt(((df_oficios_val['real_oficios'] - df_oficios_val['pred_oficios'])**2).mean())
        col2.metric("RMSE", f"{rmse_oficios:.2f}", help="Error Cuadrático Medio")
        
        mape_oficios = (100 * (df_oficios_val['real_oficios'] - df_oficios_val['pred_oficios']).abs() / df_oficios_val['real_oficios'].replace(0, np.nan)).mean()
        col3.metric("MAPE", f"{mape_oficios:.2f}%", help="Error Porcentual Medio")
        
        # Interpretación
        if mape_oficios < 10:
            st.success(f"**Excelente precisión**: El modelo tiene un error promedio de {mape_oficios:.2f}%")
        elif mape_oficios < 20:
            st.info(f"**Precisión aceptable**: El modelo tiene un error promedio de {mape_oficios:.2f}%")
        else:
            st.warning(f"**Precisión mejorable**: El modelo tiene un error promedio de {mape_oficios:.2f}%")
        
        # Tabla de datos
        st.markdown("### Datos de Validación - Oficios")
        st.dataframe(df_oficios_val, use_container_width=True, height=300)
    else:
        st.warning("El archivo de validación de oficios no tiene la estructura esperada")
    
    st.markdown("---")
    
    # === DEMANDADOS: VALIDACIÓN HISTÓRICA ===
    st.markdown("## Demandados por Mes - Validación Histórica")
    
    # Validar columnas
    if 'mes' in df_demandados_val.columns and 'real_demandados' in df_demandados_val.columns and 'pred_demandados' in df_demandados_val.columns:
        # Gráfico comparativo
        fig_val_dem = px.line(
            df_demandados_val,
            x="mes",
            y=["real_demandados", "pred_demandados"],
            markers=True,
            labels={"value": "Cantidad de demandados", "variable": "Serie"},
            title="Demandados: Real vs Predicción (Año de Validación)",
            color_discrete_sequence=['#424e71', '#bfe084']
        )
        fig_val_dem.update_traces(line=dict(width=3))
        fig_val_dem.update_layout(height=400)
        st.plotly_chart(fig_val_dem, use_container_width=True)
        
        # Métricas de error
        col1, col2, col3 = st.columns(3)
        
        mae_dem = (df_demandados_val['real_demandados'] - df_demandados_val['pred_demandados']).abs().mean()
        col1.metric("MAE", f"{mae_dem:.2f}", help="Error Absoluto Medio")
        
        rmse_dem = np.sqrt(((df_demandados_val['real_demandados'] - df_demandados_val['pred_demandados'])**2).mean())
        col2.metric("RMSE", f"{rmse_dem:.2f}", help="Error Cuadrático Medio")
        
        mape_dem = (100 * (df_demandados_val['real_demandados'] - df_demandados_val['pred_demandados']).abs() / df_demandados_val['real_demandados'].replace(0, np.nan)).mean()
        col3.metric("MAPE", f"{mape_dem:.2f}%", help="Error Porcentual Medio")
        
        # Interpretación
        if mape_dem < 10:
            st.success(f"**Excelente precisión**: El modelo tiene un error promedio de {mape_dem:.2f}%")
        elif mape_dem < 20:
            st.info(f"**Precisión aceptable**: El modelo tiene un error promedio de {mape_dem:.2f}%")
        else:
            st.warning(f"**Precisión mejorable**: El modelo tiene un error promedio de {mape_dem:.2f}%")
        
        # Tabla de datos
        st.markdown("### Datos de Validación - Demandados")
        st.dataframe(df_demandados_val, use_container_width=True, height=300)
    else:
        st.warning("El archivo de validación de demandados no tiene la estructura esperada")
    
    st.markdown("---")
    
    # === INFORMACIÓN SOBRE VALIDACIÓN ===
    st.markdown("### Sobre la Validación del Modelo")
    
    info_col, metrics_col = st.columns([2, 1.3])
    
    with info_col:
        st.markdown("""
        <div class='validation-card'>
            <h4>¿Qué es la validación histórica?</h4>
            <p>El modelo se entrena con datos de años anteriores y se evalúa prediciendo el último año completo (del cual ya conocemos los valores reales).</p>
            <p>Así podemos medir su precisión en datos conocidos antes de confiar en las predicciones futuras.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_col:
        st.markdown("""
        <div class='validation-card'>
            <h4>Métricas utilizadas</h4>
            <ul>
                <li><strong>MAE (Error Absoluto Medio)</strong>: Promedio de la diferencia absoluta entre real y predicción.</li>
                <li><strong>RMSE (Error Cuadrático Medio)</strong>: Penaliza más los errores grandes.</li>
                <li><strong>MAPE (Error Porcentual Medio)</strong>: Error expresado como porcentaje del valor real.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class='validation-card'>
        <h4>Interpretación del MAPE</h4>
        <div class='validation-badge'>
            <span class='validation-pill'>MAPE &lt; 10%: Excelente precisión</span>
            <span class='validation-pill warning'>MAPE 10-20%: Precisión aceptable</span>
            <span class='validation-pill danger'>MAPE &gt; 20%: El modelo necesita mejoras</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 4. Métricas de Clasificación (optimizado)
elif selected_tab == "Métricas de Clasificación":
    st.markdown("""
    <div class="section-title fade-in">
        Resultados y Métricas de Clasificación
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 1rem; color: #424e71; margin-bottom: 1.5rem; padding: 1rem; background: rgba(66, 78, 113, 0.15); border-radius: 10px; border-left: 4px solid #424e71;'>
        Consulta la precisión, recall y F1-score de cada modelo, desglosados por clase y tipo de predicción.<br>
        Filtra y ordena la tabla según tu necesidad.
    </div>
    """, unsafe_allow_html=True)
    
    # Validar que las columnas necesarias existan
    if 'modelo' not in df_metricas.columns or 'clase' not in df_metricas.columns:
        st.error(f"El archivo CSV no tiene las columnas esperadas.")
        st.info(f"**Columnas requeridas:** modelo, clase")
        st.info(f"**Columnas encontradas:** {', '.join(df_metricas.columns.tolist()[:10])}")
        st.warning("Verifica que el archivo CSV tenga el formato correcto.")
        st.dataframe(df_metricas.head(), use_container_width=True)
        st.stop()
    
    # Filtros optimizados con estilo profesional
    st.markdown("""
    <div style='background: rgba(60, 129, 152, 0.15); 
                padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);'>
        <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;'>
            <span style='font-weight: 600; color: #252559; font-size: 1.1rem;'>Filtros de Búsqueda</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    @st.cache_data(show_spinner=False)
    def get_unique_models(df):
        """Obtiene modelos únicos"""
        if 'modelo' not in df.columns:
            return []
        return df["modelo"].unique().tolist()
    
    @st.cache_data(show_spinner=False)
    def get_unique_clases(df):
        """Obtiene clases únicas"""
        if 'clase' not in df.columns:
            return []
        return sorted(df["clase"].unique().tolist())
    
    modelos = get_unique_models(df_metricas)
    clases = get_unique_clases(df_metricas)
    
    if not modelos or not clases:
        st.error("No se encontraron modelos o clases en el archivo CSV.")
        st.dataframe(df_metricas.head(), use_container_width=True)
        st.stop()
    
    with col1:
        st.markdown("""
        <div style='margin-bottom: 0.5rem;'>
            <span style='font-weight: 600; color: #1e3a8a;'>Modelo</span>
        </div>
        """, unsafe_allow_html=True)
        modelo_sel = st.multiselect("", modelos, default=modelos, label_visibility="collapsed")
    
    with col2:
        st.markdown("""
        <div style='margin-bottom: 0.5rem;'>
            <span style='font-weight: 600; color: #1e3a8a;'>Clase</span>
        </div>
        """, unsafe_allow_html=True)
        clase_sel = st.multiselect("", clases, default=clases, label_visibility="collapsed")
    
    # Aplicar filtros de forma optimizada
    @st.cache_data(show_spinner=False)
    def filter_metricas(df, modelos_sel, clases_sel):
        """Filtra métricas de forma eficiente preservando todas las columnas"""
        if 'modelo' not in df.columns or 'clase' not in df.columns:
            return df.copy()
        # Filtrar filas pero mantener TODAS las columnas (incluyendo matriz_confusion y clases_matriz)
        mask = df["modelo"].isin(modelos_sel) & df["clase"].isin(clases_sel)
        return df[mask].copy()
    
    df_filt = filter_metricas(df_metricas, modelo_sel, clase_sel)
    
    # Tabla con paginación (mostrar solo columnas relevantes, pero mantener todas en df_filt)
    page_size_metricas = st.selectbox("Registros por página", [50, 100, 200, 500], index=1, key="metricas_page")
    total_pages_metricas = (len(df_filt) // page_size_metricas) + (1 if len(df_filt) % page_size_metricas > 0 else 0)
    
    # Columnas a mostrar en la tabla (sin matriz_confusion y clases_matriz para mejor legibilidad)
    display_cols = [col for col in df_filt.columns if col not in ['matriz_confusion', 'clases_matriz']]
    
    if total_pages_metricas > 1:
        page_metricas = st.number_input("Página", min_value=1, max_value=total_pages_metricas, value=1, key="metricas_page_num")
        start_idx = (page_metricas - 1) * page_size_metricas
        end_idx = start_idx + page_size_metricas
        df_filt_display = df_filt[display_cols].iloc[start_idx:end_idx]
        st.info(f"Mostrando registros {start_idx+1} a {min(end_idx, len(df_filt))} de {len(df_filt)}")
    else:
        df_filt_display = df_filt[display_cols]
    
    st.dataframe(df_filt_display, use_container_width=True, height=400)
    
    st.download_button(
        "Descargar métricas de clasificación", 
        df_metricas.to_csv(index=False).encode("utf-8"),
        file_name="resultados_clasificaciones.csv",
        mime="text/csv"
    )
    
    # === MATRICES DE CONFUSIÓN ===
    st.markdown("---")
    st.markdown("### Matrices de Confusión por Modelo")
    st.markdown("""
    <div style='background: rgba(60, 129, 152, 0.15); padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #3c8198; color: #252559;'>
        Las <b>matrices de confusión</b> muestran cómo se desempeña cada clasificador:<br>
        <b>Diagonal principal</b> = predicciones correctas (cuanto más oscuro, mejor)<br>
        <b>Fuera de diagonal</b> = confusiones del modelo (qué clases se confunden entre sí)<br>
        <b>Valores altos fuera de diagonal</b> = el modelo confunde esas clases frecuentemente
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar si hay datos de matrices de confusión
    if 'matriz_confusion' not in df_filt.columns or 'clases_matriz' not in df_filt.columns:
        st.warning("""
        **Matrices de confusión no disponibles**: Los archivos CSV actuales no contienen las matrices de confusión.
        
        **Para generar las matrices:**
        1. Cierra este dashboard
        2. En el launcher, haz clic en el botón **Recalcular Archivos**
        3. Espera a que termine el proceso (puede tardar varios minutos)
        4. Vuelve a abrir este dashboard
        
        Los archivos actualizados incluirán automáticamente las matrices de confusión.
        """)
    else:
        # Agrupar por modelo (cada modelo tiene una sola fila con su matriz)
        modelos_con_matriz = []
        for modelo in df_filt['modelo'].unique():
            df_modelo = df_filt[df_filt['modelo'] == modelo]
            # Tomar la primera fila (todas tienen la misma matriz para ese modelo)
            primera_fila = df_modelo.iloc[0]
            
            if pd.notna(primera_fila['matriz_confusion']) and pd.notna(primera_fila['clases_matriz']):
                try:
                    # Deserializar JSON
                    cm = np.array(json.loads(primera_fila['matriz_confusion']))
                    clases = json.loads(primera_fila['clases_matriz'])
                    modelos_con_matriz.append((modelo, cm, clases))
                except Exception as e:
                    st.warning(f"Error al cargar matriz de confusión para {modelo}: {e}")
        
        if not modelos_con_matriz:
            st.info("No hay matrices de confusión disponibles para los modelos seleccionados.")
        else:
            for modelo, cm, clases in modelos_con_matriz:
                st.markdown(f"#### Modelo: {modelo}")
                
                # Crear visualización de matriz de confusión
                fig_cm = px.imshow(
                    cm,
                    x=clases,
                    y=clases,
                    text_auto=True,
                    color_continuous_scale=[[0, '#ffffff'], [0.5, '#bfe084'], [1, '#3c8198']],
                    title=f"Matriz de Confusión: {modelo}",
                    labels=dict(x="Predicción del Modelo", y="Valor Real", color="Cantidad")
                )
                
                fig_cm.update_layout(
                    xaxis_title="<b>Predicción</b>",
                    yaxis_title="<b>Valor Real</b>",
                    height=500,
                    font=dict(size=11)
                )
                
                # Agregar anotación explicativa
                fig_cm.add_annotation(
                    x=0.5, y=-0.15,
                    xref="paper", yref="paper",
                    text="💡 Diagonal = predicciones correctas | Fuera de diagonal = errores",
                    showarrow=False,
                    font=dict(size=11, color="gray"),
                    xanchor="center"
                )
                
                st.plotly_chart(fig_cm, use_container_width=True)
                
                # === ANÁLISIS AUTOMÁTICO ===
                col_a1, col_a2 = st.columns(2)
                
                # Calcular accuracy
                diagonal_sum = cm.diagonal().sum()
                total = cm.sum()
                accuracy = diagonal_sum / total if total > 0 else 0
                
                col_a1.metric(
                    "Precisión Global (Accuracy)",
                    f"{accuracy:.2%}",
                    help="Porcentaje de predicciones correctas sobre el total"
                )
                
                # Identificar mayor confusión
                cm_copy = cm.copy()
                np.fill_diagonal(cm_copy, 0)  # Ignorar diagonal
                
                if cm_copy.max() > 0:
                    max_confusion_idx = np.unravel_index(cm_copy.argmax(), cm_copy.shape)
                    max_confusion_val = cm_copy[max_confusion_idx]
                    clase_real = clases[max_confusion_idx[0]]
                    clase_pred = clases[max_confusion_idx[1]]
                    
                    col_a2.metric(
                        "Mayor Confusión Detectada",
                        f"{max_confusion_val} casos",
                        delta=f"{clase_real} → {clase_pred}",
                        delta_color="off",
                        help=f"El modelo confundió '{clase_real}' con '{clase_pred}' en {max_confusion_val} casos"
                    )
                    
                    st.warning(
                        f"**Patrón de confusión identificado:** El modelo confunde frecuentemente "
                        f"**'{clase_real}'** con **'{clase_pred}'** ({max_confusion_val} casos). "
                        f"Esto sugiere que estas clases tienen características similares o necesitan features adicionales para diferenciarlas."
                    )
                else:
                    col_a2.metric(
                        "Confusiones",
                        "Ninguna",
                        help="No hay confusiones significativas"
                    )
                    st.success("**Excelente**: El modelo no presenta confusiones significativas entre clases.")
                
                # Interpretación de accuracy
                if accuracy > 0.9:
                    st.success(f"**Excelente rendimiento**: El modelo tiene una precisión de {accuracy:.1%}, lo que indica predicciones muy confiables.")
                elif accuracy > 0.75:
                    st.info(f"**Buen rendimiento**: El modelo tiene una precisión de {accuracy:.1%}, dentro del rango aceptable para este tipo de clasificación.")
                elif accuracy > 0.6:
                    st.warning(f"**Rendimiento moderado**: El modelo tiene una precisión de {accuracy:.1%}. Considerar mejoras en features o reentrenamiento.")
                else:
                    st.error(f"**Rendimiento bajo**: El modelo tiene una precisión de {accuracy:.1%}. Se recomienda revisar los datos y el modelo.")
                
                st.markdown("---")
    
    # Resúmenes visuales optimizados
    st.markdown("---")
    if st.checkbox("Mostrar resumen gráfico (F1 por modelo)", value=True):
        # Limitar datos para el gráfico si hay muchos
        df_filt_chart = df_filt.copy()
        if len(df_filt_chart) > 50:
            # Agrupar por modelo y clase, tomar promedio de F1
            df_filt_chart = df_filt_chart.groupby(['modelo', 'clase'], observed=True)['f1'].mean().reset_index()
            st.info("Mostrando promedio de F1 agrupado por modelo y clase para mejor rendimiento")
        
        @st.cache_data(show_spinner=False)
        def create_metricas_chart(df):
            """Crea el gráfico de métricas de forma optimizada"""
            fig = px.bar(
                df,
                x="clase",
                y="f1",
                color="modelo",
                barmode="group",
                title="F1-score por modelo y clase",
                labels={"f1": "F1-score", "clase": "Clase"},
                color_discrete_sequence=['#3c8198', '#bfe084', '#424e71', '#252559']
            )
            return fig
        
        fig3 = create_metricas_chart(df_filt_chart)
        st.plotly_chart(fig3, width='stretch')

# Separador visual mejorado
st.markdown("""
<div class="separator"></div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; padding: 1rem; color: #64748b; font-size: 0.9rem;'>
    Desarrollado por Faber Ospina
</div>
""", unsafe_allow_html=True)
