import streamlit as st
import pandas as pd
import plotly.express as px
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
    st.warning(f"⚠️ No se pudo importar utils_csv: {e}")
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
            st.error(f"❌ No se encontró el archivo: {filename}")
            st.info(f"💡 Coloca el archivo '{filename}' en la misma carpeta del programa o en una subcarpeta 'datos'")
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
    page_title="Dashboard de Predicciones y Métricas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === ESTILOS CSS PERSONALIZADOS (igual que dashboard de embargos) ===
st.markdown("""
<style>
    /* Header principal con animación */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(30, 58, 138, 0.3);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    .main-header h1 {
        position: relative;
        z-index: 1;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .main-header p {
        position: relative;
        z-index: 1;
        font-size: 1.2rem;
        opacity: 0.95;
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
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
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
    
    /* Métricas con gradientes - Paleta profesional azul/gris */
    .metric-card-1 { border-left-color: #1e3a8a; }
    .metric-card-2 { border-left-color: #3b82f6; }
    .metric-card-3 { border-left-color: #60a5fa; }
    .metric-card-4 { border-left-color: #93c5fd; }
    .metric-card-5 { border-left-color: #64748b; }
    
    /* Styling para st.metric */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: bold !important;
        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #4a5568 !important;
        font-weight: 600 !important;
    }
    
    /* Secciones de contenido */
    .content-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border: 1px solid #e2e8f0;
    }
    .section-title {
        font-size: 1.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid;
        border-image: linear-gradient(90deg, #1e3a8a, #3b82f6) 1;
    }
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        color: white;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
    }
    
    /* Filtros */
    .filter-chip {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        background: #f0f2f6;
        border-radius: 20px;
        border: 1px solid #d1d5db;
        cursor: pointer;
        transition: all 0.3s;
    }
    .filter-chip:hover {
        background: #3b82f6;
        color: white;
        transform: scale(1.05);
    }
    .filter-chip.active {
        background: #1e3a8a;
        color: white;
        border-color: #1e3a8a;
        box-shadow: 0 2px 8px rgba(30, 58, 138, 0.4);
    }
    .filter-section {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .filter-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #2d3748;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .toggle-button {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: all 0.3s;
        font-size: 0.9rem;
        color: #4a5568;
    }
    .toggle-button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.2);
    }
    .toggle-button.active {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border-color: transparent;
        box-shadow: 0 4px 12px rgba(30, 58, 138, 0.4);
    }
    .filter-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 0.8rem;
        margin: 0.2rem;
        background: #edf2f7;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #2d3748;
        border: 1px solid #cbd5e0;
    }
    .filter-badge.active {
        background: #1e3a8a;
        color: white;
        border-color: #1e3a8a;
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
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
    }
    
    /* Estilos para headers y secciones */
    h1, h2, h3 {
        color: #2d3748;
    }
    
    /* Separadores */
    .separator {
        height: 2px;
        background: linear-gradient(90deg, transparent, #1e3a8a, #3b82f6, transparent);
        margin: 2rem 0;
        border-radius: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Header personalizado con estilo profesional
st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard de Predicción y Evaluación</h1>
    <p>Análisis de predicciones, desempeño y métricas de modelos sobre embargos bancarios</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='font-size: 1.1rem; color: #4a5568; margin-bottom: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 10px; border-left: 4px solid #1e3a8a;'>
    Bienvenido al dashboard interactivo para el análisis de <b>predicciones, desempeño y métricas</b> de modelos sobre embargos bancarios.<br>
    Navega entre las pestañas, explora tendencias, compara valores reales vs predichos y descarga los resultados.
</div>
""", unsafe_allow_html=True)

# --- Carga optimizada de datos con caché ---
@st.cache_data(show_spinner="Cargando datos...", ttl=3600)
def load_csv(name):
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
        dtype_dict = {'modelo': 'category', 'clase': 'category'}
    
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
        df_oficios = load_csv("predicciones_oficios_por_mes.csv")
        df_demandados = load_csv("predicciones_demandados_por_mes.csv")
        df_metricas = load_csv("resultados_clasificaciones.csv")
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs([
    "📅 Predicción de Oficios", 
    "📅 Predicción de Demandados",
    "📊 Métricas de Clasificación"
])

# 1. Predicción de Oficios por mes (optimizado)
with tab1:
    st.markdown("""
    <div class="section-title fade-in">
        📅 Oficios por mes: Real vs Predicción
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 1rem; color: #4a5568; margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
        Visualiza la evolución mensual del <b>total de oficios</b>. Compara los valores reales vs. la predicción del modelo.
    </div>
    """, unsafe_allow_html=True)
    
    # Validar que las columnas necesarias existan
    required_cols = ['mes', 'real_oficios', 'pred_oficios']
    missing_cols = [col for col in required_cols if col not in df_oficios.columns]
    
    if missing_cols:
        st.error(f"❌ El archivo CSV no tiene las columnas esperadas.")
        st.info(f"**Columnas requeridas:** {', '.join(required_cols)}")
        st.info(f"**Columnas encontradas:** {', '.join(df_oficios.columns.tolist()[:10])}")
        st.warning("💡 Verifica que el archivo CSV tenga el formato correcto.")
        st.dataframe(df_oficios.head(), use_container_width=True)
        st.stop()
    
    # Limitar datos si hay muchos meses para mejor rendimiento
    df_oficios_display = df_oficios.copy()
    if len(df_oficios_display) > 100:
        st.info(f"⚠️ Mostrando muestra de {min(100, len(df_oficios_display))} meses de {len(df_oficios_display)} totales para mejor rendimiento")
        df_oficios_display = df_oficios_display.head(100)
    
    # Gráfico optimizado
    @st.cache_data(show_spinner=False)
    def create_oficios_chart(df):
        """Crea el gráfico de oficios de forma optimizada"""
        # Validar columnas antes de graficar
        if 'mes' not in df.columns or 'real_oficios' not in df.columns or 'pred_oficios' not in df.columns:
            return None
        
        fig = px.line(
            df,
            x="mes",
            y=["real_oficios", "pred_oficios"],
            markers=True,
            labels={"value": "Cantidad de oficios", "variable": "Serie"},
            title="Oficios por mes: Real vs Predicción"
        )
        fig.update_traces(line=dict(width=3))
        return fig
    
    fig1 = create_oficios_chart(df_oficios_display)
    if fig1:
        st.plotly_chart(fig1, width='stretch')
    else:
        st.error("No se pudo crear el gráfico. Verifica que el CSV tenga las columnas correctas.")
    
    # Tabla con paginación
    page_size_oficios = st.selectbox("Registros por página", [50, 100, 200], index=1, key="oficios_page")
    total_pages_oficios = (len(df_oficios) // page_size_oficios) + (1 if len(df_oficios) % page_size_oficios > 0 else 0)
    
    if total_pages_oficios > 1:
        page_oficios = st.number_input("Página", min_value=1, max_value=total_pages_oficios, value=1, key="oficios_page_num")
        start_idx = (page_oficios - 1) * page_size_oficios
        end_idx = start_idx + page_size_oficios
        df_oficios_display_table = df_oficios.iloc[start_idx:end_idx]
        st.info(f"Mostrando registros {start_idx+1} a {min(end_idx, len(df_oficios))} de {len(df_oficios)}")
    else:
        df_oficios_display_table = df_oficios
    
    st.dataframe(df_oficios_display_table, use_container_width=True, height=300)
    
    st.download_button(
        "⬇️ Descargar CSV de predicción de oficios", 
        df_oficios.to_csv(index=False).encode("utf-8"),
        file_name="predicciones_oficios_por_mes.csv",
        mime="text/csv"
    )

# 2. Predicción de demandados únicos (optimizado)
with tab2:
    st.markdown("""
    <div class="section-title fade-in">
        📅 Demandados únicos por mes: Real vs Predicción
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 1rem; color: #4a5568; margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
        Visualiza la evolución mensual del <b>número de demandados únicos</b>. Compara el valor real vs. la predicción.
    </div>
    """, unsafe_allow_html=True)
    
    # Validar que las columnas necesarias existan
    required_cols = ['mes', 'real_demandados', 'pred_demandados']
    missing_cols = [col for col in required_cols if col not in df_demandados.columns]
    
    if missing_cols:
        st.error(f"❌ El archivo CSV no tiene las columnas esperadas.")
        st.info(f"**Columnas requeridas:** {', '.join(required_cols)}")
        st.info(f"**Columnas encontradas:** {', '.join(df_demandados.columns.tolist()[:10])}")
        st.warning("💡 Verifica que el archivo CSV tenga el formato correcto.")
        st.dataframe(df_demandados.head(), use_container_width=True)
        st.stop()
    
    # Limitar datos si hay muchos meses
    df_demandados_display = df_demandados.copy()
    if len(df_demandados_display) > 100:
        st.info(f"⚠️ Mostrando muestra de {min(100, len(df_demandados_display))} meses de {len(df_demandados_display)} totales para mejor rendimiento")
        df_demandados_display = df_demandados_display.head(100)
    
    # Gráfico optimizado
    @st.cache_data(show_spinner=False)
    def create_demandados_chart(df):
        """Crea el gráfico de demandados de forma optimizada"""
        # Validar columnas antes de graficar
        if 'mes' not in df.columns or 'real_demandados' not in df.columns or 'pred_demandados' not in df.columns:
            return None
        
        fig = px.line(
            df,
            x="mes",
            y=["real_demandados", "pred_demandados"],
            markers=True,
            labels={"value": "Cantidad de demandados", "variable": "Serie"},
            title="Demandados únicos por mes: Real vs Predicción"
        )
        fig.update_traces(line=dict(width=3))
        return fig
    
    fig2 = create_demandados_chart(df_demandados_display)
    if fig2:
        st.plotly_chart(fig2, width='stretch')
    else:
        st.error("No se pudo crear el gráfico. Verifica que el CSV tenga las columnas correctas.")
    
    # Tabla con paginación
    page_size_demandados = st.selectbox("Registros por página", [50, 100, 200], index=1, key="demandados_page")
    total_pages_demandados = (len(df_demandados) // page_size_demandados) + (1 if len(df_demandados) % page_size_demandados > 0 else 0)
    
    if total_pages_demandados > 1:
        page_demandados = st.number_input("Página", min_value=1, max_value=total_pages_demandados, value=1, key="demandados_page_num")
        start_idx = (page_demandados - 1) * page_size_demandados
        end_idx = start_idx + page_size_demandados
        df_demandados_display_table = df_demandados.iloc[start_idx:end_idx]
        st.info(f"Mostrando registros {start_idx+1} a {min(end_idx, len(df_demandados))} de {len(df_demandados)}")
    else:
        df_demandados_display_table = df_demandados
    
    st.dataframe(df_demandados_display_table, use_container_width=True, height=300)
    
    st.download_button(
        "⬇️ Descargar CSV de predicción de demandados", 
        df_demandados.to_csv(index=False).encode("utf-8"),
        file_name="predicciones_demandados_por_mes.csv",
        mime="text/csv"
    )

# 3. Métricas de Clasificación (optimizado)
with tab3:
    st.markdown("""
    <div class="section-title fade-in">
        📊 Resultados y métricas de clasificación
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 1rem; color: #4a5568; margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
        Consulta la precisión, recall y F1-score de cada modelo, desglosados por clase y tipo de predicción.<br>
        Filtra y ordena la tabla según tu necesidad.
    </div>
    """, unsafe_allow_html=True)
    
    # Validar que las columnas necesarias existan
    if 'modelo' not in df_metricas.columns or 'clase' not in df_metricas.columns:
        st.error(f"❌ El archivo CSV no tiene las columnas esperadas.")
        st.info(f"**Columnas requeridas:** modelo, clase")
        st.info(f"**Columnas encontradas:** {', '.join(df_metricas.columns.tolist()[:10])}")
        st.warning("💡 Verifica que el archivo CSV tenga el formato correcto.")
        st.dataframe(df_metricas.head(), use_container_width=True)
        st.stop()
    
    # Filtros optimizados con estilo profesional
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f5f7fa 0%, #e2e8f0 100%); 
                padding: 1.5rem; border-radius: 15px; margin-bottom: 1.5rem; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);'>
        <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;'>
            <span style='font-size: 1.3rem;'>🔍</span>
            <span style='font-weight: 600; color: #2d3748; font-size: 1.1rem;'>Filtros de Búsqueda</span>
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
        st.error("❌ No se encontraron modelos o clases en el archivo CSV.")
        st.dataframe(df_metricas.head(), use_container_width=True)
        st.stop()
    
    with col1:
        st.markdown("""
        <div style='margin-bottom: 0.5rem;'>
            <span style='font-weight: 600; color: #1e3a8a;'>📊 Modelo</span>
        </div>
        """, unsafe_allow_html=True)
        modelo_sel = st.multiselect("", modelos, default=modelos, label_visibility="collapsed")
    
    with col2:
        st.markdown("""
        <div style='margin-bottom: 0.5rem;'>
            <span style='font-weight: 600; color: #1e3a8a;'>🏷️ Clase</span>
        </div>
        """, unsafe_allow_html=True)
        clase_sel = st.multiselect("", clases, default=clases, label_visibility="collapsed")
    
    # Aplicar filtros de forma optimizada
    @st.cache_data(show_spinner=False)
    def filter_metricas(df, modelos_sel, clases_sel):
        """Filtra métricas de forma eficiente"""
        if 'modelo' not in df.columns or 'clase' not in df.columns:
            return df.copy()
        return df[
            df["modelo"].isin(modelos_sel) & df["clase"].isin(clases_sel)
        ].copy()
    
    df_filt = filter_metricas(df_metricas, modelo_sel, clase_sel)
    
    # Tabla con paginación
    page_size_metricas = st.selectbox("Registros por página", [50, 100, 200, 500], index=1, key="metricas_page")
    total_pages_metricas = (len(df_filt) // page_size_metricas) + (1 if len(df_filt) % page_size_metricas > 0 else 0)
    
    if total_pages_metricas > 1:
        page_metricas = st.number_input("Página", min_value=1, max_value=total_pages_metricas, value=1, key="metricas_page_num")
        start_idx = (page_metricas - 1) * page_size_metricas
        end_idx = start_idx + page_size_metricas
        df_filt_display = df_filt.iloc[start_idx:end_idx]
        st.info(f"Mostrando registros {start_idx+1} a {min(end_idx, len(df_filt))} de {len(df_filt)}")
    else:
        df_filt_display = df_filt
    
    st.dataframe(df_filt_display, use_container_width=True, height=400)
    
    st.download_button(
        "⬇️ Descargar métricas de clasificación", 
        df_metricas.to_csv(index=False).encode("utf-8"),
        file_name="resultados_clasificaciones.csv",
        mime="text/csv"
    )
    
    # Resúmenes visuales optimizados
    if st.checkbox("Mostrar resumen gráfico (F1 por modelo)", value=True):
        # Limitar datos para el gráfico si hay muchos
        df_filt_chart = df_filt.copy()
        if len(df_filt_chart) > 50:
            # Agrupar por modelo y clase, tomar promedio de F1
            df_filt_chart = df_filt_chart.groupby(['modelo', 'clase'], observed=True)['f1'].mean().reset_index()
            st.info("⚠️ Mostrando promedio de F1 agrupado por modelo y clase para mejor rendimiento")
        
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
                labels={"f1": "F1-score", "clase": "Clase"}
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
