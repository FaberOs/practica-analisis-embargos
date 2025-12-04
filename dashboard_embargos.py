"""
Dashboard de Embargos - Versión 2.0
Diseño completamente nuevo y moderno con enfoque visual
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

try:
    import openpyxl
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

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
            os.getcwd(),
        ]
        for path in search_paths:
            if path:
                file_path = os.path.join(path, filename)
                if os.path.exists(file_path):
                    return file_path
        if required:
            st.error(f"❌ No se encontró el archivo: {filename}")
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

# Importar estilos centralizados
try:
    from dashboard_styles import get_dashboard_styles, get_sidebar_header
except ImportError:
    # Fallback si no se puede importar
    def get_dashboard_styles():
        return "<style></style>"
    def get_sidebar_header(title_line1, title_line2):
        return f"<div><h1>{title_line1} {title_line2}</h1></div>"

# Configuración de página
st.set_page_config(
    page_title="Oficios Bancarios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === ESTILOS CSS PERSONALIZADOS ===
st.markdown(get_dashboard_styles(), unsafe_allow_html=True)

# === CARGA DE DATOS OPTIMIZADA ===
@st.cache_data(show_spinner="Cargando datos...", ttl=86400)
def load_data() -> pd.DataFrame:
    """Carga los datos del CSV con optimizaciones de rendimiento"""
    try:
        # Intentar obtener la ruta del archivo
        from utils_csv import find_csv_file, get_data_path, get_base_path
        
        # Buscar el archivo
        csv_path = find_csv_file("embargos_consolidado_mensual.csv")
        
        if csv_path is None:
            # Obtener las rutas de búsqueda para el mensaje de error
            data_path = get_data_path()
            base_path = get_base_path()
            
            # Verificar si el archivo existe en AppData
            appdata_path = None
            if os.name == 'nt':  # Windows
                appdata = os.getenv('APPDATA')
                if appdata:
                    appdata_path = os.path.join(appdata, "DashboardEmbargos", "datos", "embargos_consolidado_mensual.csv")
                    if os.path.exists(appdata_path):
                        csv_path = appdata_path
                        st.success(f"Archivo encontrado en: {appdata_path}")
        
        if csv_path is None:
                # Preparar rutas para el mensaje (evitar backslashes en f-string)
                default_path = 'AppData\\Roaming\\DashboardEmbargos\\datos' if os.name == 'nt' else 'datos'
                data_path_display = data_path if data_path else default_path
                base_datos_path = os.path.join(base_path, 'datos')
                
                # Mostrar mensaje de error con información detallada
                error_msg = f"""
                **❌ No se encontró el archivo: embargos_consolidado_mensual.csv**
                
                **📁 Ubicaciones buscadas:**
                - {data_path_display}
                - {base_path}
                - {base_datos_path}
                """
                if appdata_path:
                    appdata_dir = os.path.dirname(appdata_path)
                    error_msg += f"\n- {appdata_dir}"
                
                error_msg += f"""
                
                **Solución:**
                
                1. **Verifica que el archivo existe en:** {data_path_display}
                2. **Si acabas de procesar los CSV:** Cierra y vuelve a abrir el dashboard
                3. **Si el archivo no existe:** Ejecuta el procesamiento desde el launcher
                """
                st.error(error_msg)
                return pd.DataFrame()
        
        # Si encontramos el archivo, usar get_csv_path para validación adicional
        csv_path = get_csv_path("embargos_consolidado_mensual.csv", required=True)
    except FileNotFoundError as e:
        # Mostrar mensaje más amigable en Streamlit
        st.error(f"""
        **❌ No se encontró el archivo: embargos_consolidado_mensual.csv**
        
        **Error:** {str(e)}
        
        **💡 Solución:**
        
        1. **Si acabas de seleccionar el CSV original de la BD:**
           - El procesamiento debería ejecutarse automáticamente
           - Si no se ejecutó, cierra este dashboard y vuelve a intentar desde el launcher
           - Asegúrate de haber seleccionado el CSV original antes de iniciar el dashboard
        
        2. **Si el procesamiento falló:**
           - Revisa la ventana de progreso del launcher para ver los errores
           - Verifica que el CSV original tenga el formato correcto
           - Haz clic en "¿Cómo generar/obtener los CSV?" para más información
        """)
        return pd.DataFrame()
    
    if csv_path is None:
        return pd.DataFrame()
    
    try:
        import chardet
        with open(csv_path, 'rb') as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            encoding = result['encoding'] if result else 'utf-8'
    except:
        encoding = 'utf-8'
    
    encodings = [encoding, 'utf-8', 'latin-1', 'cp1252']
    df = None
    
    # Optimizar tipos de datos desde el inicio
    dtype_dict = {
        'entidad_bancaria': 'category',
        'ciudad': 'category',
        'entidad_remitente': 'category',
        'tipo_documento': 'category',
        'estado_embargo': 'category',
        'tipo_embargo': 'category',
        'mes': 'category',
        'funcionario': 'category',
        'estado_demandado': 'category',
        'tipo_carta': 'category'
    }
    
    for enc in encodings:
        try:
            df = pd.read_csv(
                csv_path, 
                encoding=enc, 
                low_memory=False,
                dtype=dtype_dict,
                engine='c'  # Usar engine C para mejor rendimiento
            )
            break
        except:
            continue
    
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Limpieza optimizada con operaciones vectorizadas
    if 'montoaembargar' in df.columns:
        df['montoaembargar'] = pd.to_numeric(df['montoaembargar'], errors='coerce', downcast='float')
        df['montoaembargar'] = df['montoaembargar'].fillna(0).astype('float32')
    
    if 'es_cliente' in df.columns:
        # Procesar es_cliente igual que la versión anterior: primero intentar numérico
        # Si ya es numérico o se puede convertir, usarlo directamente
        try:
            # Intentar convertir a numérico primero (como versión anterior)
            df['es_cliente'] = pd.to_numeric(df['es_cliente'], errors='coerce').fillna(0)
            # Si los valores son mayores que 1, normalizar a 0 o 1
            df['es_cliente'] = (df['es_cliente'] > 0).astype('int8')
        except:
            # Si falla la conversión numérica, usar búsqueda en strings
            df['es_cliente'] = df['es_cliente'].astype(str).str.upper().str.strip()
            df['es_cliente'] = (df['es_cliente'].str.contains('SI|CLIENTE|1', case=False, na=False)).astype('int8')
    
    # Optimizar categorías
    for col in df.select_dtypes(include=['category']).columns:
        df[col] = df[col].cat.remove_unused_categories()
    
    # Excluir registros con NaN SOLO en columnas fundamentales
    # Las columnas no relevantes (correo, direccion, fecha_banco, etc.) pueden tener NaN
    # sin afectar el análisis del dashboard
    columnas_fundamentales = [
        # Columnas de filtrado críticas
        'entidad_bancaria',  # Filtro principal, gráfico Top 10
        'ciudad',            # Filtro principal, gráfico Top 10, análisis geográfico
        'estado_embargo',    # Filtro principal, gráfico de distribución
        'tipo_embargo',      # Filtro principal, gráfico, proporciones Judicial/Coactivo
        'mes',               # Filtro principal, evolución temporal, proporciones mensuales
        # Columnas de métricas y cálculos críticas
        'montoaembargar',    # Métricas principales (total, promedio), estadísticas
        'es_cliente',        # Métricas de porcentaje de clientes
        # Columnas de rankings y visualizaciones importantes
        'funcionario',       # Gráfico Top 10 Funcionarios
        'entidad_remitente', # Gráfico Top 10 Entidades Remitentes
        'tipo_documento'     # Análisis detallado, distribución de documentos
    ]
    
    # Filtrar solo las columnas fundamentales que existen en el DataFrame
    columnas_fundamentales_validas = [col for col in columnas_fundamentales if col in df.columns]
    
    if columnas_fundamentales_validas:
        # Excluir registros que tengan NaN en cualquiera de las columnas fundamentales
        # Las columnas no relevantes (correo, direccion, referencia, etc.) pueden tener NaN
        # sin que esto afecte el análisis del dashboard
        df = df.dropna(subset=columnas_fundamentales_validas)
    
    return df

# === FUNCIONES DE ANÁLISIS OPTIMIZADAS ===
@st.cache_data(show_spinner=False)
def calculate_metrics(df: pd.DataFrame) -> Dict:
    """Calcula métricas principales de forma optimizada"""
    if df.empty:
        return {}
    
    total = len(df)
    
    # Operaciones vectorizadas optimizadas
    monto_total = 0.0
    monto_promedio = 0.0
    if 'montoaembargar' in df.columns:
        monto_total = float(df['montoaembargar'].sum())
        monto_promedio = float(df['montoaembargar'].mean())
    
    activos = 0
    if 'estado_embargo' in df.columns:
        # Buscar exactamente 'Activo' (como en versión anterior: df_filt[df_filt['estado_embargo']=='Activo'])
        # Convertir a string y normalizar para comparación
        estado_str = df['estado_embargo'].astype(str).str.strip()
        # Buscar 'Activo' exacto (mayúscula inicial) - igual que versión anterior
        # También buscar variaciones por si acaso
        mask_activo = (estado_str == 'Activo') | (estado_str.str.contains('^activo$', case=False, na=False, regex=True))
        activos = int(mask_activo.sum())
    
    clientes = 0
    if 'es_cliente' in df.columns:
        if df['es_cliente'].dtype in ['int8', 'int16', 'int32', 'int64', 'float32', 'float64']:
            clientes = int(df['es_cliente'].sum())
        else:
            clientes = int((df['es_cliente'].astype(str).str.contains('SI|CLIENTE', case=False, na=False)).sum())
    
    # Calcular métricas adicionales de oficios
    promedio_oficios_mes = 0.0
    if 'mes' in df.columns and total > 0:
        meses_unicos = df['mes'].nunique()
        if meses_unicos > 0:
            promedio_oficios_mes = total / meses_unicos
    
    # Embargos judiciales
    embargos_judiciales = 0
    embargos_coactivos = 0
    if 'tipo_embargo' in df.columns:
        tipo_series = df['tipo_embargo'].astype(str).str.upper()
        embargos_judiciales = int(tipo_series.str.contains('JUDICIAL', na=False).sum())
        embargos_coactivos = int(tipo_series.str.contains('COACTIVO', na=False).sum())
    
    return {
        'total': total,
        'total_oficios': total,  # Los registros son los oficios
        'monto_total': monto_total,
        'monto_promedio': monto_promedio,
        'activos': activos,
        'clientes': clientes,
        'porcentaje_clientes': (clientes / total * 100) if total > 0 else 0.0,
        'promedio_oficios_mes': promedio_oficios_mes,
        'embargos_judiciales': embargos_judiciales,
        'embargos_coactivos': embargos_coactivos
    }


def normalize_tipo_documento_series(series: Optional[pd.Series]) -> pd.Series:
    """Normaliza los valores de tipo_documento a categorías principales."""
    if series is None or series.empty:
        if series is None:
            return pd.Series(dtype='object')
        return pd.Series(index=series.index, dtype='object')
    doc_series = series.astype(str).str.upper().str.strip()
    normalized = pd.Series('Embargo', index=series.index, dtype='object')
    mask_desembargo = doc_series.str.contains('DESEM|LEVANT', case=False, na=False)
    mask_requerimiento = doc_series.str.contains('REQUER', case=False, na=False)
    mask_no_procesable = doc_series.str.contains('NO', case=False, na=False) & doc_series.str.contains('PROCES', case=False, na=False)
    normalized[mask_desembargo] = 'Desembargo'
    normalized[mask_requerimiento] = 'Requerimiento'
    normalized[mask_no_procesable] = 'No procesable'
    return normalized

# === FUNCIÓN DE FILTRADO OPTIMIZADA (NUNCA SE CONGELA) ===
@st.cache_data(show_spinner=False, max_entries=100)
def apply_filters_fast(df: pd.DataFrame, filtros: Dict, search_term: str = "") -> pd.DataFrame:
    """Aplica filtros de forma ultra-rápida - GARANTIZA que nunca se congela"""
    if df.empty:
        return pd.DataFrame()
    
    try:
        mask = pd.Series(True, index=df.index)
        if filtros.get('banco') and isinstance(filtros['banco'], list) and len(filtros['banco']) > 0:
            if 'entidad_bancaria' in df.columns:
                bancos_sel = [str(b).strip().upper() for b in filtros['banco']]
                bancos_df = df['entidad_bancaria'].astype(str).str.strip().str.upper()
                mask &= bancos_df.isin(bancos_sel)
        
        if filtros.get('ciudad') and isinstance(filtros['ciudad'], list) and len(filtros['ciudad']) > 0:
            if 'ciudad' in df.columns:
                mask &= df['ciudad'].isin(filtros['ciudad'])
        
        if filtros.get('estado') and isinstance(filtros['estado'], list) and len(filtros['estado']) > 0:
            if 'estado_embargo' in df.columns:
                estados_permitidos_map = {
                    'CONFIRMADO': ['CONFIRMADO', 'CONFIRMADOS', 'Confirmado', 'Confirmados', 'confirmado', 'confirmados'],
                    'PROCESADO': ['PROCESADO', 'PROCESADOS', 'Procesado', 'Procesados', 'procesado', 'procesados'],
                    'SIN_CONFIRMAR': ['SIN_CONFIRMAR', 'SIN CONFIRMAR', 'SINCONFIRMAR', 'Sin confirmar', 'Sin Confirmar', 'SIN_CONFIRMADO', 'SIN CONFIRMADO'],
                    'PROCESADO_CON_ERRORES': ['PROCESADO_CON_ERRORES', 'PROCESADO CON ERRORES', 'PROCESADOCONERRORES',
                                             'PROCESADO_CON_ERROR', 'PROCESADO CON ERROR', 'Procesado con error', 
                                             'Procesado con errores', 'CON_ERROR', 'CON_ERRORES', 'CON ERROR', 'CON ERRORES']
                }
                
                estados_df = df['estado_embargo'].astype(str).str.strip().str.upper().str.replace(' ', '_').str.replace('-', '_').str.rstrip('_')
                mask_estado = pd.Series(False, index=df.index)
                for estado_seleccionado in filtros['estado']:
                    if estado_seleccionado in estados_permitidos_map:
                        variaciones = [v.upper().replace(' ', '_').replace('-', '_').rstrip('_') for v in estados_permitidos_map[estado_seleccionado]]
                        mask_estado |= estados_df.isin(variaciones)
                
                mask &= mask_estado
        
        if filtros.get('tipo') and isinstance(filtros['tipo'], list) and len(filtros['tipo']) > 0:
            if 'tipo_embargo' in df.columns:
                tipo_embargo_map = {
                    'JUDICIAL': ['JUDICIAL', 'Judicial', 'judicial', 'JUDICIALES', 'Judiciales'],
                    'COACTIVO': ['COACTIVO', 'Coactivo', 'coactivo', 'COACTIVOS', 'Coactivos']
                }
                
                tipos_df = df['tipo_embargo'].astype(str).str.strip().str.upper().str.replace(' ', '_').str.rstrip('_')
                mask_tipo = pd.Series(False, index=df.index)
                for tipo_seleccionado in filtros['tipo']:
                    if tipo_seleccionado in tipo_embargo_map:
                        variaciones = [v.upper().replace(' ', '_').rstrip('_') for v in tipo_embargo_map[tipo_seleccionado]]
                        mask_tipo |= tipos_df.isin(variaciones)
                
                mask &= mask_tipo

        if filtros.get('tipo_documento') and isinstance(filtros['tipo_documento'], list) and len(filtros['tipo_documento']) > 0:
            if 'tipo_documento' in df.columns:
                doc_normalizado = normalize_tipo_documento_series(df['tipo_documento'])
                mask &= doc_normalizado.isin(filtros['tipo_documento'])
        
        if filtros.get('mes') and isinstance(filtros['mes'], list) and len(filtros['mes']) > 0:
            if 'mes' in df.columns:
                mes_list = [str(x) for x in filtros['mes']]
                mask &= df['mes'].astype(str).isin(mes_list)
        
        df_filt = df.loc[mask].copy()
        
        if search_term and len(search_term) > 2:
            search_cols = ['entidad_bancaria', 'ciudad', 'entidad_remitente', 'nombres', 'identificacion']
            search_cols = [col for col in search_cols if col in df_filt.columns]
            
            if search_cols:
                search_mask = pd.Series(False, index=df_filt.index)
                for col in search_cols:
                    try:
                        search_mask |= df_filt[col].astype(str).str.contains(search_term, case=False, na=False, regex=False)
                    except:
                        continue
                df_filt = df_filt.loc[search_mask]
        
        return df_filt
    except Exception as e:
        # Si hay cualquier error, retornar DataFrame vacío en lugar de congelar
        # Esto previene que la aplicación se congele cuando se eliminan filtros
        return pd.DataFrame()

# === INTERFAZ PRINCIPAL ===
def main():
    # Sidebar con título y navegación
    with st.sidebar:
        st.markdown(get_sidebar_header("OFICIOS", "BANCARIOS"), unsafe_allow_html=True)
        st.markdown("""<p style='color: white; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.5rem; margin-top: 1rem;'>ANÁLISIS DE EMBARGOS</p>""", unsafe_allow_html=True)
        
        # Navegación personalizada sin radio buttons
        if 'selected_tab' not in st.session_state:
            st.session_state.selected_tab = "Dashboard Principal"
        
        # Crear botones personalizados para navegación
        if st.button("Dashboard Principal", key="nav_dashboard", use_container_width=True):
            st.session_state.selected_tab = "Dashboard Principal"
        
        if st.button("Tendencias y Rankings", key="nav_tendencias", use_container_width=True):
            st.session_state.selected_tab = "Tendencias y Rankings"
        
        if st.button("Análisis Geográfico", key="nav_geografico", use_container_width=True):
            st.session_state.selected_tab = "Análisis Geográfico"
        
        if st.button("Análisis Detallado", key="nav_detallado", use_container_width=True):
            st.session_state.selected_tab = "Análisis Detallado"
        
        if st.button("Exportación", key="nav_exportacion", use_container_width=True):
            st.session_state.selected_tab = "Exportación"
        
        st.markdown("---")
        
        if st.button("Recargar Datos", use_container_width=True, help="Fuerza la recarga de datos desde el CSV, limpiando el cache"):
            # Limpiar cache de datos
            load_data.clear()
            apply_filters_fast.clear()
            calculate_metrics.clear()
            st.rerun()
        
        selected_tab = st.session_state.selected_tab
    
    # Inicializar filtros vacíos PRIMERO (sin esperar datos)
    # Esto permite que la interfaz se muestre inmediatamente
    for key in ['filtro_banco', 'filtro_ciudad', 'filtro_estado', 'filtro_tipo', 'filtro_mes', 'filtro_tipo_documento']:
        if key not in st.session_state:
            st.session_state[key] = []
    
    # Cargar datos de forma lazy (después de mostrar interfaz)
    # NO bloquear la interfaz - cargar en background
    try:
        df = load_data()
    except:
        df = pd.DataFrame()
    
    if df.empty:
        # Crear DataFrame vacío para que la interfaz funcione sin bloquear
        df = pd.DataFrame()
    
    # Obtener opciones únicas (cacheado) - solo si hay datos
    @st.cache_data(show_spinner=False, ttl=86400)
    def get_options_cached(df: pd.DataFrame, col: str) -> List:
        """Obtiene opciones únicas de forma cacheada"""
        if df.empty or col not in df.columns:
            return []
        try:
            return sorted([str(x) for x in df[col].dropna().unique() if str(x).strip()])
        except:
            return []
    
    def get_options(col):
        if df.empty:
            return []
        return get_options_cached(df, col)
    
    # === FUNCIÓN: FILTROS MULTISELECT PROFESIONALES ===
    def create_multiselect_filter(title, options, key_prefix, container=None):
        """Crea filtros multiselect profesionales sin emojis"""
        # Inicializar session_state SOLO si no existe (antes de crear el widget)
        if key_prefix not in st.session_state:
            st.session_state[key_prefix] = []
        
        # Usar el container proporcionado o st por defecto
        target = container if container else st
        
        if not options:
            return st.session_state.get(key_prefix, [])
        
        # Crear multiselect - Streamlit maneja automáticamente el session_state
        # NO usar default, dejar que Streamlit lo maneje con la key
        selected = target.multiselect(
            title,
            options=options,
            key=key_prefix,
            placeholder="Selecciona opciones..."
        )
        
        # NO modificar session_state aquí - el widget ya lo hace automáticamente
        # Solo retornar el valor seleccionado
        return selected
    
    # === SECCIÓN DE FILTROS ===
    st.markdown("### Filtros de Búsqueda", unsafe_allow_html=True)
    
    # Eliminamos la búsqueda global para simplificar la experiencia de filtros
    search_term = ""
    
    # Filtros en columnas
    filtros = {}
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f4, col_f5, col_f6, col_f7 = st.columns(4)
    
    with col_f1:
        if not df.empty and 'entidad_bancaria' in df.columns:
            # Obtener opciones de bancos y filtrar valores no bancarios
            bancos_raw = get_options('entidad_bancaria')
            bancos_permitidos = ['FALABELLA', 'COLPATRIA', 'COOPCENTRAL', 'SANTANDER']
            bancos = []
            for banco in bancos_raw:
                banco_norm = str(banco).strip().upper()
                if banco_norm in bancos_permitidos and banco not in bancos:
                    bancos.append(banco)
            # Mantener el orden definido por negocios
            bancos_ordenados = []
            for permitido in bancos_permitidos:
                for banco in bancos:
                    if str(banco).strip().upper() == permitido:
                        bancos_ordenados.append(banco)
                        break
            bancos = bancos_ordenados
            filtros['banco'] = create_multiselect_filter("Entidad Bancaria", bancos, 'filtro_banco', st)
        else:
            filtros['banco'] = []
    
    with col_f2:
        if not df.empty and 'ciudad' in df.columns:
            ciudades = get_options('ciudad')
            filtros['ciudad'] = create_multiselect_filter("Ciudad", ciudades, 'filtro_ciudad', st)
        else:
            filtros['ciudad'] = []
    
    with col_f3:
        if not df.empty and 'estado_embargo' in df.columns:
            estados_raw = get_options('estado_embargo')
            
            estados_permitidos_map = {
                'CONFIRMADO': ['CONFIRMADO', 'CONFIRMADOS', 'Confirmado', 'Confirmados', 'confirmado', 'confirmados'],
                'PROCESADO': ['PROCESADO', 'PROCESADOS', 'Procesado', 'Procesados', 'procesado', 'procesados'],
                'SIN_CONFIRMAR': ['SIN_CONFIRMAR', 'SIN CONFIRMAR', 'SINCONFIRMAR', 'Sin confirmar', 'Sin Confirmar', 'SIN_CONFIRMADO', 'SIN CONFIRMADO'],
                'PROCESADO_CON_ERRORES': ['PROCESADO_CON_ERRORES', 'PROCESADO CON ERRORES', 'PROCESADOCONERRORES',
                                         'PROCESADO_CON_ERROR', 'PROCESADO CON ERROR', 'Procesado con error', 
                                         'Procesado con errores', 'CON_ERROR', 'CON_ERRORES', 'CON ERROR', 'CON ERRORES']
            }
            
            estados_filtrados = []
            estados_normalizados_set = set()
            
            for estado_estandar, variaciones in estados_permitidos_map.items():
                for estado_raw in estados_raw:
                    estado_str = str(estado_raw).strip().upper().replace(' ', '_').replace('-', '_').rstrip('_')
                    variaciones_normalizadas = [v.upper().replace(' ', '_').replace('-', '_').rstrip('_') for v in variaciones]
                    
                    if estado_str in variaciones_normalizadas and estado_estandar not in estados_normalizados_set:
                        estados_filtrados.append(estado_estandar)
                        estados_normalizados_set.add(estado_estandar)
                        break
            
            estados_orden = ['CONFIRMADO', 'PROCESADO', 'SIN_CONFIRMAR', 'PROCESADO_CON_ERRORES']
            estados_filtrados = [e for e in estados_orden if e in estados_filtrados]
            
            filtros['estado'] = create_multiselect_filter("Estado", estados_filtrados, 'filtro_estado', st)
        else:
            filtros['estado'] = []
    
    with col_f4:
        if not df.empty and 'tipo_embargo' in df.columns:
            tipos_raw = get_options('tipo_embargo')
            
            tipo_embargo_map = {
                'JUDICIAL': ['JUDICIAL', 'Judicial', 'judicial', 'JUDICIALES', 'Judiciales'],
                'COACTIVO': ['COACTIVO', 'Coactivo', 'coactivo', 'COACTIVOS', 'Coactivos']
            }
            
            tipos_filtrados = []
            tipos_normalizados_set = set()
            
            for tipo_estandar, variaciones in tipo_embargo_map.items():
                for tipo_raw in tipos_raw:
                    tipo_str = str(tipo_raw).strip().upper().replace(' ', '_').rstrip('_')
                    variaciones_normalizadas = [v.upper().replace(' ', '_').rstrip('_') for v in variaciones]
                    
                    if tipo_str in variaciones_normalizadas and tipo_estandar not in tipos_normalizados_set:
                        tipos_filtrados.append(tipo_estandar)
                        tipos_normalizados_set.add(tipo_estandar)
                        break
            
            tipos_orden = ['JUDICIAL', 'COACTIVO']
            tipos_filtrados = [t for t in tipos_orden if t in tipos_filtrados]
            
            filtros['tipo'] = create_multiselect_filter("Tipo de Embargo", tipos_filtrados, 'filtro_tipo', st)
        else:
            filtros['tipo'] = []
    
    with col_f5:
        if not df.empty and 'mes' in df.columns:
            meses = get_options('mes')
            if meses:
                try:
                    meses_ordenados = sorted(meses, key=lambda x: pd.to_datetime(x, format='%Y-%m', errors='coerce'))
                    meses_ordenados = [m for m in meses_ordenados if pd.notna(pd.to_datetime(m, format='%Y-%m', errors='coerce'))]
                    if not meses_ordenados:
                        meses_ordenados = meses
                except:
                    meses_ordenados = meses
                filtros['mes'] = create_multiselect_filter("Mes", meses_ordenados, 'filtro_mes', st)
            else:
                filtros['mes'] = []
        else:
            filtros['mes'] = []
    
    with col_f6:
        if not df.empty and 'tipo_documento' in df.columns:
            doc_map = normalize_tipo_documento_series(df['tipo_documento'])
            doc_options = ['Embargo', 'Desembargo', 'Requerimiento', 'No procesable']
            opciones_disponibles = [opt for opt in doc_options if opt in doc_map.unique().tolist()]
            filtros['tipo_documento'] = create_multiselect_filter("Tipo de Documento", opciones_disponibles, 'filtro_tipo_documento', st)
        else:
            filtros['tipo_documento'] = []

    with col_f7:
        st.markdown("<br>", unsafe_allow_html=True)  # Espacio para alineación con botones
        if st.button("Resetear Filtros", use_container_width=True, type="secondary"):
            for key in ['filtro_banco', 'filtro_ciudad', 'filtro_estado', 'filtro_tipo', 'filtro_mes', 'filtro_tipo_documento']:
                if key in st.session_state:
                    st.session_state[key] = []
            st.rerun()
        
        total_filtros = sum(len(v) for v in filtros.values()) + (1 if search_term else 0)
        if total_filtros > 0:
            st.info(f"Filtros activos: {total_filtros}")
    
    # === APLICAR FILTROS OPTIMIZADO (LAZY - NUNCA SE CONGELA) ===
    # Aplicar filtros de forma segura - nunca congelar
    try:
        if not df.empty:
            # Aplicar filtros de forma optimizada
            # Asegurar que todos los filtros sean listas válidas antes de aplicar
            filtros_safe = {}
            for key, value in filtros.items():
                if isinstance(value, list):
                    filtros_safe[key] = value
                else:
                    filtros_safe[key] = []
            
            df_filt = apply_filters_fast(df, filtros_safe, search_term)
        else:
            df_filt = pd.DataFrame()
    except Exception as e:
        # Si hay error, retornar DataFrame vacío en lugar de congelar
        st.warning(f"Error al aplicar filtros: {str(e)}")
        df_filt = pd.DataFrame()
    
    # === MÉTRICAS PRINCIPALES MEJORADAS (LAZY) ===
    # Solo calcular si hay datos
    if not df_filt.empty:
        metrics = calculate_metrics(df_filt)
        # Mostrar mensaje informativo sobre registros encontrados
        total_registros = len(df_filt)
        st.success(f"Se encontraron **{total_registros:,}** registros para los filtros actuales.")
    else:
        metrics = {
            'total': 0,
            'total_oficios': 0,
            'monto_total': 0,
            'monto_promedio': 0,
            'activos': 0,
            'clientes': 0,
            'porcentaje_clientes': 0.0,
            'promedio_oficios_mes': 0.0,
            'embargos_judiciales': 0,
            'embargos_coactivos': 0
        }
        st.warning("No se encontraron registros para los filtros actuales.")
    
    if metrics:
        # Header de métricas
        st.markdown("### Resumen Ejecutivo")
        
        # Primera fila de métricas (4 columnas)
        col1, col2, col3, col4 = st.columns(4)
        
        # Segunda fila de métricas (4 columnas)
        col5, col6, col7, col8 = st.columns(4)
        
        # Paleta de colores nueva (#bfe084, #3c8198, #424e71, #252559)
        color_palette = [
            "linear-gradient(135deg, #3c8198 0%, #424e71 100%)",  # Azul a azul oscuro
            "linear-gradient(135deg, #bfe084 0%, #3c8198 100%)",  # Verde a azul
            "linear-gradient(135deg, #424e71 0%, #252559 100%)",  # Azul oscuro a muy oscuro
            "linear-gradient(135deg, #3c8198 0%, #bfe084 100%)",  # Azul a verde
            "linear-gradient(135deg, #252559 0%, #424e71 100%)",  # Muy oscuro a azul oscuro
            "linear-gradient(135deg, #bfe084 0%, #424e71 100%)",  # Verde a azul oscuro
            "linear-gradient(135deg, #3c8198 0%, #252559 100%)",  # Azul a muy oscuro
            "linear-gradient(135deg, #424e71 0%, #3c8198 100%)"   # Azul oscuro a azul
        ]
        
        # Configuración de métricas sin emojis - Primera fila
        metric_configs_row1 = [
            {
                "label": "Total de oficios",
                "value": f"{metrics.get('total_oficios', metrics['total']):,}",
                "color": "#3c8198",
                "bg": color_palette[0]
            },
            {
                "label": "Monto total embargado",
                "value": f"${metrics['monto_total']:,.0f}",
                "color": "#bfe084",
                "bg": color_palette[1]
            },
            {
                "label": "Promedio de oficios por mes",
                "value": f"{metrics.get('promedio_oficios_mes', 0):,.2f}",
                "color": "#424e71",
                "bg": color_palette[2]
            },
            {
                "label": "Clientes con embargo",
                "value": f"{metrics.get('clientes', 0):,}",
                "color": "#3c8198",
                "bg": color_palette[3]
            }
        ]
        
        # Segunda fila de métricas
        metric_configs_row2 = [
            {
                "label": "Porcentaje clientes",
                "value": f"{metrics['porcentaje_clientes']:.1f}%",
                "color": "#252559",
                "bg": color_palette[4]
            },
            {
                "label": "Monto promedio/oficio",
                "value": f"${metrics['monto_promedio']:,.0f}",
                "color": "#bfe084",
                "bg": color_palette[5]
            },
            {
                "label": "Embargos coactivos",
                "value": f"{metrics.get('embargos_coactivos', 0):,}",
                "color": "#3c8198",
                "bg": color_palette[6]
            },
            {
                "label": "Embargos judiciales",
                "value": f"{metrics.get('embargos_judiciales', 0):,}",
                "color": "#424e71",
                "bg": color_palette[7]
            }
        ]
        
        # Mostrar primera fila
        cols_row1 = [col1, col2, col3, col4]
        for i, (col, config) in enumerate(zip(cols_row1, metric_configs_row1)):
            with col:
                # Calcular tamaño de fuente dinámico según longitud del valor
                value_length = len(str(config['value']))
                if value_length > 20:
                    font_size = "1.4rem"
                elif value_length > 15:
                    font_size = "1.8rem"
                else:
                    font_size = "2.2rem"
                
                st.markdown(f"""
                <div class="kpi-card" style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    margin-bottom: 1rem;
                    border: 1px solid #e2e8f0;
                    height: 140px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div class="kpi-label" style="font-size: 0.85rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.8rem;">{config['label']}</div>
                    <div class="kpi-value" style="font-size: {font_size}; font-weight: 700; color: #3c8198; letter-spacing: -0.5px; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.2;">{config['value']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Mostrar segunda fila
        cols_row2 = [col5, col6, col7, col8]
        for i, (col, config) in enumerate(zip(cols_row2, metric_configs_row2)):
            with col:
                # Calcular tamaño de fuente dinámico según longitud del valor
                value_length = len(str(config['value']))
                if value_length > 20:
                    font_size = "1.4rem"
                elif value_length > 15:
                    font_size = "1.8rem"
                else:
                    font_size = "2.2rem"
                
                st.markdown(f"""
                <div class="kpi-card" style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    margin-bottom: 1rem;
                    border: 1px solid #e2e8f0;
                    height: 140px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div class="kpi-label" style="font-size: 0.85rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.8rem;">{config['label']}</div>
                    <div class="kpi-value" style="font-size: {font_size}; font-weight: 700; color: #3c8198; letter-spacing: -0.5px; word-wrap: break-word; overflow-wrap: break-word; line-height: 1.2;">{config['value']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Separador visual mejorado
    st.markdown("""
    <div style="height: 1px; background: linear-gradient(90deg, transparent, #e2e8f0, #cbd5e1, transparent); 
                margin: 2rem 0; border-radius: 2px;"></div>
    """, unsafe_allow_html=True)
    
    # === RENDERIZADO DE CONTENIDO SEGÚN NAVEGACIÓN ===
    selected_tab = st.session_state.get('selected_tab', 'Dashboard Principal')
    
    # === TAB 1: DASHBOARD PRINCIPAL ===
    if selected_tab == "Dashboard Principal":
        if df_filt.empty:
            st.markdown("""
            <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); 
                        border-radius: 15px; margin: 2rem 0;'>
                <h2 style='color: #64748b; font-weight: 600;'>No hay datos para mostrar</h2>
                <p style='color: #636e72; font-size: 1.1rem;'>Ajusta los filtros para ver resultados</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Distribución de Datos
            st.markdown("### Distribución de Datos")
            
            # Gráfico de distribución por tipo
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### Distribución por Tipo de Embargo")
                if 'tipo_embargo' in df_filt.columns:
                    tipo_embargo_map = {
                        'JUDICIAL': ['JUDICIAL', 'Judicial', 'judicial', 'JUDICIAL_', 'JUDICIALES'],
                        'COACTIVO': ['COACTIVO', 'Coactivo', 'coactivo', 'COACTIVO_', 'COACTIVOS']
                    }
                    
                    tipo_raw = df_filt['tipo_embargo'].astype(str).str.strip()
                    tipo_normalizado = tipo_raw.str.upper().str.replace(' ', '_').str.rstrip('_')
                    mask_validos = pd.Series(False, index=df_filt.index)
                    tipo_mapeado = pd.Series(index=df_filt.index, dtype=str)
                    
                    for tipo_estandar, variaciones in tipo_embargo_map.items():
                        variaciones_normalizadas = [v.upper().replace(' ', '_').rstrip('_') for v in variaciones]
                        mask = tipo_normalizado.isin(variaciones_normalizadas)
                        mask_validos |= mask
                        tipo_mapeado[mask] = tipo_estandar
                    
                    tipo_filtrado = df_filt[mask_validos].copy()
                    
                    if not tipo_filtrado.empty:
                        # Usar los tipos mapeados (estandarizados)
                        tipo_filtrado['tipo_embargo_clean'] = tipo_mapeado[mask_validos]
                        tipo_counts = tipo_filtrado['tipo_embargo_clean'].value_counts()
                        tipo_counts = tipo_counts[tipo_counts.index.isin(['JUDICIAL', 'COACTIVO'])]
                        
                        if not tipo_counts.empty:
                            df_pie = pd.DataFrame({
                                'tipo': tipo_counts.index,
                                'cantidad': tipo_counts.values
                            })
                            
                            fig = px.pie(
                                df_pie,
                                values='cantidad',
                                names='tipo',
                                hole=0.5,
                                color_discrete_sequence=['#3c8198', '#bfe084', '#424e71', '#252559']
                            )
                            fig.update_traces(
                                textposition='inside', 
                                textinfo='percent+label',
                                marker=dict(line=dict(color='#FFFFFF', width=2))
                            )
                            fig.update_layout(
                                showlegend=True, 
                                height=450,
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(size=12),
                                legend=dict(
                                    orientation="v",
                                    yanchor="middle",
                                    y=0.5,
                                    xanchor="left",
                                    x=1.05
                                )
                            )
                            st.plotly_chart(fig, use_container_width=True)
            
            with col_right:
                st.markdown("#### Distribución por Estado")
                if 'estado_embargo' in df_filt.columns and len(df_filt) > 0:
                    estados_permitidos_map = {
                        'CONFIRMADO': [
                            'CONFIRMADO', 'CONFIRMADOS', 'Confirmado', 'Confirmados', 'confirmado', 'confirmados',
                            'CONFIRMADO_', 'CONFIRMADOS_'
                        ],
                        'PROCESADO': [
                            'PROCESADO', 'PROCESADOS', 'Procesado', 'Procesados', 'procesado', 'procesados',
                            'PROCESADO_', 'PROCESADOS_'
                        ],
                        'SIN_CONFIRMAR': [
                            'SIN_CONFIRMAR', 'SIN CONFIRMAR', 'SINCONFIRMAR', 'Sin confirmar', 'Sin Confirmar',
                            'SIN_CONFIRMAR_', 'SIN_CONFIRMADO', 'SIN CONFIRMADO', 'SINCONFIRMADO'
                        ],
                        'PROCESADO_CON_ERRORES': [
                            'PROCESADO_CON_ERRORES', 'PROCESADO CON ERRORES', 'PROCESADOCONERRORES',
                            'PROCESADO_CON_ERROR', 'PROCESADO CON ERROR', 'PROCESADOCONERROR',
                            'Procesado con error', 'Procesado con errores', 'Procesado Con Error', 'Procesado Con Errores',
                            'CON_ERROR', 'CON_ERRORES', 'CON ERROR', 'CON ERRORES',
                            'PROCESADO_CON_ERRORES_', 'PROCESADO_CON_ERROR_'
                        ]
                    }
                    
                    # Normalizar valores: convertir a string, limpiar, y normalizar a mayúsculas
                    # Reemplazar espacios por guiones bajos y eliminar caracteres especiales
                    estados_raw = df_filt['estado_embargo'].astype(str).str.strip()
                    estados_normalizados = estados_raw.str.upper().str.replace(' ', '_').str.replace('-', '_')
                    # Eliminar guiones bajos al final
                    estados_normalizados = estados_normalizados.str.rstrip('_')
                    
                    # Crear máscara para filtrar estados válidos
                    mask_estados_validos = pd.Series(False, index=df_filt.index)
                    estados_mapeados = pd.Series(index=df_filt.index, dtype=str)
                    
                    for estado_estandar, variaciones in estados_permitidos_map.items():
                        variaciones_normalizadas = []
                        for v in variaciones:
                            v_norm = v.upper().replace(' ', '_').replace('-', '_').rstrip('_')
                            variaciones_normalizadas.append(v_norm)
                        mask = estados_normalizados.isin(variaciones_normalizadas)
                        mask_estados_validos |= mask
                        estados_mapeados[mask] = estado_estandar
                    
                    estados_filtrados = df_filt[mask_estados_validos].copy()
                    
                    if not estados_filtrados.empty:
                        # Usar los estados mapeados (estandarizados)
                        estados_filtrados['estado_clean'] = estados_mapeados[mask_estados_validos]
                        estado_counts = estados_filtrados['estado_clean'].value_counts()
                        
                        # Asegurar que solo tenemos los estados permitidos en el orden correcto
                        estados_orden = ['CONFIRMADO', 'PROCESADO', 'SIN_CONFIRMAR', 'PROCESADO_CON_ERRORES']
                        estado_counts = estado_counts.reindex([e for e in estados_orden if e in estado_counts.index])
                    else:
                        estado_counts = pd.Series(dtype=int)
                    if not estado_counts.empty and len(estado_counts) > 0:
                        fig = go.Figure(data=[
                            go.Bar(
                                x=estado_counts.index,
                                y=estado_counts.values,
                                marker=dict(
                                    color=['#3c8198', '#bfe084', '#424e71', '#252559'][:len(estado_counts)],
                                    line=dict(color='#FFFFFF', width=1)
                                ),
                                text=estado_counts.values,
                                textposition='outside',
                            )
                        ])
                        fig.update_layout(
                            showlegend=False, 
                            height=450,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(title='Estado', tickangle=-45),
                            yaxis=dict(title='Cantidad'),
                            font=dict(size=12)
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Rankings principales
            st.markdown("### Rankings Principales")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.markdown("#### Entidades Bancarias")
                if 'entidad_bancaria' in df_filt.columns and len(df_filt) > 0:
                    # Solo incluir los 4 bancos reales
                    bancos_validos = ['FALABELLA', 'COLPATRIA', 'COOPCENTRAL', 'SANTANDER']
                    
                    # Valores a excluir explícitamente (estados que no son bancos)
                    valores_excluir = ['PROCESADO', 'DESEMBARGO', 'CONFIRMADO', 'EMBARGO',
                                     'Procesado', 'Desembargo', 'Confirmado', 'Embargo',
                                     'procesado', 'desembargo', 'confirmado', 'embargo']
                    
                    # Filtrar datos: solo incluir los bancos válidos y excluir valores de estado
                    df_bancos_filtrado = df_filt[
                        (df_filt['entidad_bancaria'].astype(str).str.upper().isin([b.upper() for b in bancos_validos])) &
                        (~df_filt['entidad_bancaria'].astype(str).str.upper().isin([v.upper() for v in valores_excluir]))
                    ]
                    
                    # Contar bancos válidos (solo los que tienen datos)
                    top_bancos = df_bancos_filtrado['entidad_bancaria'].value_counts()
                    
                    # Filtrar solo los bancos válidos del resultado (por si acaso)
                    top_bancos = top_bancos[top_bancos.index.astype(str).str.upper().isin([b.upper() for b in bancos_validos])]
                    
                    if not top_bancos.empty and len(top_bancos) > 0:
                        fig = go.Figure(data=[
                            go.Bar(
                                x=top_bancos.values,
                                y=top_bancos.index,
                                orientation='h',
                                marker=dict(
                                    color=top_bancos.values,
                                    colorscale=[[0, '#bfe084'], [0.5, '#3c8198'], [1, '#424e71']],
                                    line=dict(color='#FFFFFF', width=1)
                                ),
                                text=top_bancos.values,
                                textposition='outside',
                            )
                        ])
                        fig.update_layout(
                            showlegend=False, 
                            height=450,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(title='Cantidad'),
                            yaxis=dict(title='Banco'),
                            font=dict(size=12)
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with col_b:
                st.markdown("#### Ciudades")
                if 'ciudad' in df_filt.columns and len(df_filt) > 0:
                    top_ciudades = df_filt['ciudad'].value_counts().head(10)
                    if not top_ciudades.empty and len(top_ciudades) > 0:
                        fig = go.Figure(data=[
                            go.Bar(
                                x=top_ciudades.values,
                                y=top_ciudades.index,
                                orientation='h',
                                marker=dict(
                                    color=top_ciudades.values,
                                    colorscale=[[0, '#bfe084'], [0.5, '#3c8198'], [1, '#424e71']],
                                    line=dict(color='#FFFFFF', width=1)
                                ),
                                text=top_ciudades.values,
                                textposition='outside',
                            )
                        ])
                        fig.update_layout(
                            showlegend=False, 
                            height=450,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(title='Cantidad'),
                            yaxis=dict(title='Ciudad'),
                            font=dict(size=12)
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with col_c:
                st.markdown("#### Funcionarios")
                if 'funcionario' in df_filt.columns and len(df_filt) > 0:
                    top_funcionarios = df_filt['funcionario'].value_counts().head(10)
                    if not top_funcionarios.empty and len(top_funcionarios) > 0:
                        fig = go.Figure(data=[
                            go.Bar(
                                x=top_funcionarios.values,
                                y=top_funcionarios.index,
                                orientation='h',
                                marker=dict(
                                    color=top_funcionarios.values,
                                    colorscale=[[0, '#bfe084'], [0.5, '#3c8198'], [1, '#424e71']],
                                    line=dict(color='#FFFFFF', width=1)
                                ),
                                text=top_funcionarios.values,
                                textposition='outside',
                            )
                        ])
                        fig.update_layout(
                            showlegend=False, 
                            height=450,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(title='Cantidad'),
                            yaxis=dict(title='Funcionario'),
                            font=dict(size=12)
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Evolución temporal
            st.markdown("### Evolución Temporal")
            
            if 'mes' in df_filt.columns and len(df_filt) > 0:
                df_time = df_filt.groupby('mes', observed=True).size().reset_index(name='oficios')
                
                try:
                    df_time['mes_datetime'] = pd.to_datetime(df_time['mes'], format='%Y-%m', errors='coerce')
                    df_time = df_time.dropna(subset=['mes_datetime'])
                    df_time = df_time.sort_values('mes_datetime')
                    df_time = df_time.drop(columns=['mes_datetime'])
                except:
                    df_time = df_time.sort_values('mes')
                
                if not df_time.empty:
                    fig = px.line(
                        df_time, 
                        x='mes', 
                        y='oficios', 
                        markers=True,
                        title="Evolución mensual de oficios",
                        labels={"mes": "Mes", "oficios": "Cantidad de Oficios"},
                        color_discrete_sequence=['#3c8198']
                    )
                    fig.update_traces(line=dict(width=3), marker=dict(size=8))
                    fig.update_layout(
                        height=400,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(title='Mes', tickangle=-45),
                        yaxis=dict(title='Cantidad de Oficios'),
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("Interactúa: haz zoom o consulta valores pasando el mouse sobre los puntos.")
            
            # Principales Entidades Remitentes
            st.markdown("### Principales Entidades Remitentes")
            
            if 'entidad_remitente' in df_filt.columns and len(df_filt) > 0:
                top_entidades = df_filt['entidad_remitente'].value_counts().head(10)
                if not top_entidades.empty and len(top_entidades) > 0:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=top_entidades.values,
                            y=top_entidades.index,
                            orientation='h',
                            marker=dict(
                                color=top_entidades.values,
                                colorscale=[[0, '#bfe084'], [0.5, '#3c8198'], [1, '#424e71']],
                                line=dict(color='#FFFFFF', width=1)
                            ),
                            text=top_entidades.values,
                            textposition='outside',
                        )
                    ])
                    fig.update_layout(
                        showlegend=False, 
                        height=450,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(title='Cantidad'),
                        yaxis=dict(title='Entidad Remitente'),
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Gráfica de Proporción Judicial vs Coactivo (Mensual)
            st.markdown("### Proporción Judicial vs Coactivo (Mensual)")
            
            if 'tipo_embargo' in df_filt.columns and 'mes' in df_filt.columns and len(df_filt) > 0:
                # Calcular proporciones mensuales
                # IMPORTANTE: Agrupar TODOS los datos por mes y tipo_embargo primero, sin limitar antes
                # Esto asegura que se muestren todos los meses disponibles, similar al gráfico de evolución
                
                # Agrupar por mes y tipo_embargo (usar todos los datos)
                prop_mensual = df_filt.groupby(['mes', 'tipo_embargo'], observed=True).size().reset_index(name='cantidad')
                total_mensual = prop_mensual.groupby('mes')['cantidad'].sum().reset_index(name='total')
                prop_mensual = prop_mensual.merge(total_mensual, on='mes')
                prop_mensual['proporcion'] = prop_mensual['cantidad'] / prop_mensual['total']
                
                try:
                    prop_mensual['mes_datetime'] = pd.to_datetime(prop_mensual['mes'], format='%Y-%m', errors='coerce')
                    prop_mensual = prop_mensual.dropna(subset=['mes_datetime'])
                    prop_mensual = prop_mensual.sort_values('mes_datetime')
                    prop_mensual = prop_mensual.drop(columns=['mes_datetime'])
                except Exception as e:
                    prop_mensual = prop_mensual.sort_values('mes')
                
                # Crear gráfico de área apilada
                fig = go.Figure()
                
                # Orden de apilamiento (de abajo hacia arriba)
                orden_tipos = ['0', 'COACTIVO', 'JUDICIAL', 'PROCESADO', 'SIN_PROCESAR']
                
                # Colores con nueva paleta personalizada
                # Mapear tipos de embargo a colores de la paleta
                colores = {
                    'COACTIVO': '#424e71',      # Azul oscuro (serie inferior)
                    'JUDICIAL': '#3c8198',      # Azul principal (serie superior)
                    '0': '#252559',             # Azul muy oscuro
                    'PROCESADO': '#bfe084',     # Verde claro
                    'SIN_PROCESAR': '#e2e8f0'   # Gris muy claro
                }
                
                tipos_disponibles = prop_mensual['tipo_embargo'].unique()
                
                for tipo in orden_tipos:
                    if tipo in tipos_disponibles:
                        datos_tipo = prop_mensual[prop_mensual['tipo_embargo'] == tipo].sort_values('mes')
                        color_tipo = colores.get(tipo, '#95a5a6')
                        fig.add_trace(go.Scatter(
                            x=datos_tipo['mes'],
                            y=datos_tipo['proporcion'],
                            mode='lines',
                            name=tipo,
                            stackgroup='one',
                            fill='tonexty' if tipo != orden_tipos[0] else 'tozeroy',
                            line=dict(width=0.5, color=color_tipo),
                            fillcolor=color_tipo,
                            hovertemplate=f'<b>{tipo}</b><br>Mes: %{{x}}<br>Proporción: %{{y:.2%}}<extra></extra>'
                        ))
                
                fig.update_layout(
                    title="Proporción Judicial vs Coactivo (Mensual)",
                    xaxis_title="Mes",
                    yaxis_title="Proporción",
                    yaxis=dict(tickformat='.0%', range=[0, 1]),
                    height=500,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode='x unified',
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.02
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Visualiza la proporción mensual según tipo de embargo.")
        
        # Footer
        st.markdown("""
        <div style='text-align: center; padding: 1rem; color: #64748b; font-size: 0.9rem; margin-top: 3rem;'>
            Desarrollado por Faber Ospina
        </div>
        """, unsafe_allow_html=True)
    
    # === TAB 2: TENDENCIAS Y RANKINGS ===
    elif selected_tab == "Tendencias y Rankings":
        if df_filt.empty:
            st.markdown("""
            <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); 
                        border-radius: 15px; margin: 2rem 0;'>
                <h2 style='color: #64748b; font-weight: 600;'>No hay datos para mostrar</h2>
                <p style='color: #636e72; font-size: 1.1rem;'>Ajusta los filtros para ver resultados</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("### Tendencia Temporal de Oficios")
            
            if 'mes' in df_filt.columns and len(df_filt) > 0:
                oficios_mensual = df_filt.groupby('mes', observed=True).size().reset_index(name='cantidad_oficios')
                
                try:
                    oficios_mensual['mes_datetime'] = pd.to_datetime(oficios_mensual['mes'], format='%Y-%m', errors='coerce')
                    oficios_mensual = oficios_mensual.dropna(subset=['mes_datetime'])
                    oficios_mensual = oficios_mensual.sort_values('mes_datetime')
                    oficios_mensual = oficios_mensual.drop(columns=['mes_datetime'])
                except Exception as e:
                    oficios_mensual = oficios_mensual.sort_values('mes')
                
                if not oficios_mensual.empty:
                    fig = go.Figure()
                    
                    fig.add_trace(
                        go.Scatter(
                            x=oficios_mensual['mes'],
                            y=oficios_mensual['cantidad_oficios'],
                            mode='lines+markers',
                            name="Cantidad de Oficios",
                            line=dict(color='#3c8198', width=3),
                            marker=dict(size=8, color='#3c8198', line=dict(width=2, color='white')),
                            hovertemplate='<b>%{x}</b><br>Cantidad de Oficios: %{y:,.0f}<extra></extra>'
                        )
                    )
                    
                    # Calcular rango del eje Y para que se vea bien (similar a la imagen: 2k a 12k)
                    min_val = oficios_mensual['cantidad_oficios'].min()
                    max_val = oficios_mensual['cantidad_oficios'].max()
                    
                    y_min = max(0, min_val - (max_val - min_val) * 0.1)
                    y_max = max_val + (max_val - min_val) * 0.1
                    
                    if max_val > 1000:
                        y_axis_title = "Cantidad de Oficios"
                        fig.update_layout(
                            yaxis=dict(
                                title=y_axis_title,
                                range=[y_min, y_max],
                                tickformat='.0f',
                                tickmode='linear',
                                tick0=0,
                                dtick=(y_max - y_min) / 10 if (y_max - y_min) > 0 else 1000
                            )
                        )
                    else:
                        fig.update_layout(
                            yaxis=dict(
                                title="Cantidad de Oficios",
                                range=[y_min, y_max]
                            )
                        )
                    
                    fig.update_layout(
                        title=dict(
                            text="Evolución Mensual de Oficios",
                            font=dict(size=20, color='#2d3748'),
                            x=0.5,
                            xanchor='center'
                        ),
                        xaxis=dict(
                            title=dict(text="Mes", font=dict(size=14, color='#4a5568')),
                            tickangle=-45,
                            showgrid=True,
                            gridcolor='rgba(128,128,128,0.2)'
                        ),
                        height=500,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        hovermode='x unified',
                        font=dict(size=12),
                        margin=dict(l=80, r=40, t=80, b=100)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption("Haz zoom o pasa el mouse sobre los puntos para ver detalles.")
                else:
                    st.warning("No se pudieron calcular los datos de oficios mensuales.")
            else:
                st.warning("No hay datos de meses disponibles para el análisis.")
        
        # Footer
        st.markdown("""
        <div style='text-align: center; padding: 1rem; color: #64748b; font-size: 0.9rem; margin-top: 3rem;'>
            Desarrollado por Faber Ospina
        </div>
        """, unsafe_allow_html=True)
    
    # === TAB 3: ANÁLISIS GEOGRÁFICO ===
    elif selected_tab == "Análisis Geográfico":
        if df_filt.empty:
            st.warning("No hay datos para análisis geográfico.")
        else:
            st.markdown("### Distribución Geográfica")
            
            col_geo1, col_geo2 = st.columns(2)
            
            with col_geo1:
                if 'ciudad' in df_filt.columns:
                    # Calcular estadísticas por ciudad
                    ciudad_stats = df_filt.groupby('ciudad').agg({
                        'montoaembargar': 'sum' if 'montoaembargar' in df_filt.columns else 'count'
                    }).reset_index()
                    
                    if 'montoaembargar' in df_filt.columns:
                        ciudad_stats.columns = ['ciudad', 'monto']
                    else:
                        ciudad_stats.columns = ['ciudad', 'monto']
                        ciudad_stats['monto'] = ciudad_stats['monto'] * 1000  # Aproximación
                    
                    ciudad_stats = ciudad_stats.sort_values('monto', ascending=True).tail(20)
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=ciudad_stats['monto'],
                        y=ciudad_stats['ciudad'],
                        orientation='h',
                        marker=dict(
                            color=ciudad_stats['monto'],
                            colorscale=[[0, '#bfe084'], [0.5, '#3c8198'], [1, '#424e71']],
                            line=dict(color='#3c8198', width=1),
                            showscale=True,
                            colorbar=dict(
                                title=dict(text="Monto", font=dict(color='#2d3748')),
                                tickfont=dict(color='#2d3748')
                            )
                        ),
                        text=[f"${x:,.0f}" if x >= 1000 else f"${x:,.2f}" for x in ciudad_stats['monto']],
                        textposition='outside',
                        hovertemplate='<b>%{y}</b><br>Monto: $%{x:,.0f}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title=dict(
                            text="Distribución por Ciudad",
                            font=dict(size=18, color='#2d3748'),
                            x=0.5,
                            xanchor='center'
                        ),
                        xaxis=dict(
                            title=dict(text="Monto ($)", font=dict(size=14, color='#4a5568')),
                            showgrid=True,
                            gridcolor='rgba(128,128,128,0.2)'
                        ),
                        yaxis=dict(
                            title="",
                            showgrid=False
                        ),
                        height=max(600, len(ciudad_stats) * 30),  # Altura dinámica según cantidad
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12),
                        margin=dict(l=150, r=40, t=60, b=40)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar también una tabla con todas las ciudades para referencia
                    with st.expander("Ver todas las ciudades (tabla completa)", expanded=False):
                        ciudad_stats_all = df_filt.groupby('ciudad').agg({
                            'montoaembargar': 'sum' if 'montoaembargar' in df_filt.columns else 'count'
                        }).reset_index()
                        
                        if 'montoaembargar' in df_filt.columns:
                            ciudad_stats_all.columns = ['ciudad', 'monto']
                        else:
                            ciudad_stats_all.columns = ['ciudad', 'monto']
                            ciudad_stats_all['monto'] = ciudad_stats_all['monto'] * 1000
                        
                        ciudad_stats_all = ciudad_stats_all.sort_values('monto', ascending=False)
                        ciudad_stats_all['monto'] = ciudad_stats_all['monto'].apply(lambda x: f"${x:,.0f}")
                        st.dataframe(ciudad_stats_all, use_container_width=True, height=400)
            
            with col_geo2:
                if 'entidad_bancaria' in df_filt.columns and 'ciudad' in df_filt.columns:
                    cross_tab = pd.crosstab(
                        df_filt['ciudad'],
                        df_filt['entidad_bancaria']
                    ).head(10)
                    
                    fig = px.imshow(
                        cross_tab,
                        labels=dict(x="Banco", y="Ciudad", color="Cantidad"),
                        x=cross_tab.columns,
                        y=cross_tab.index,
                        color_continuous_scale=[[0, '#bfe084'], [0.5, '#3c8198'], [1, '#424e71']],
                        aspect="auto"
                    )
                    fig.update_layout(height=500, title="Matriz Ciudad vs Banco")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Footer
        st.markdown("""
        <div style='text-align: center; padding: 1rem; color: #64748b; font-size: 0.9rem; margin-top: 3rem;'>
            Desarrollado por Faber Ospina
        </div>
        """, unsafe_allow_html=True)
    
    # === TAB 4: ANÁLISIS DETALLADO ===
    elif selected_tab == "Análisis Detallado":
        if df_filt.empty:
            st.warning("No hay datos para análisis detallado.")
        else:
            st.markdown("### Análisis Detallado")
            
            # Selector de análisis
            analisis_tipo = st.selectbox(
                "Selecciona tipo de análisis",
                ["Distribución de Montos", "Análisis de Clientes", "Análisis de Documentos"]
            )
            
            if analisis_tipo == "Distribución de Montos":
                if 'montoaembargar' in df_filt.columns:
                    st.markdown("#### Análisis de Montos a Embargar")
                    
                    # Análisis de valores cero y no cero
                    montos = df_filt['montoaembargar'].dropna()
                    valores_cero = (montos == 0).sum()
                    valores_no_cero = (montos != 0).sum()
                    total_montos = len(montos)
                    
                    # Información sobre valores cero
                    if valores_cero > 0:
                        st.info(f"**Nota:** {valores_cero:,} registros ({valores_cero/total_montos*100:.1f}%) tienen monto igual a $0. Estos se excluyen del histograma para mejor visualización.")
                    
                    montos_no_cero = montos[montos > 0]
                    
                    if len(montos_no_cero) > 0:
                        q1 = montos_no_cero.quantile(0.25)
                        q3 = montos_no_cero.quantile(0.75)
                        iqr = q3 - q1
                        limite_inferior = max(0, q1 - 1.5 * iqr)
                        limite_superior = q3 + 1.5 * iqr
                        
                        montos_sin_outliers = montos_no_cero[
                            (montos_no_cero >= limite_inferior) & 
                            (montos_no_cero <= limite_superior)
                        ]
                        
                        outliers_count = len(montos_no_cero) - len(montos_sin_outliers)
                        
                        # Histograma principal (sin outliers)
                        if len(montos_sin_outliers) > 0:
                            fig1 = px.histogram(
                                montos_sin_outliers,
                                x=montos_sin_outliers.values,
                                nbins=50,
                                labels={'x': 'Monto a Embargar', 'count': 'Frecuencia'},
                                color_discrete_sequence=['#3c8198']
                            )
                            fig1.update_layout(height=400, showlegend=False)
                            st.plotly_chart(fig1, use_container_width=True)
                        else:
                            st.warning("No hay suficientes datos para mostrar el histograma.")
                        
                        # Información sobre outliers
                        if outliers_count > 0:
                            st.warning(f"**Valores atípicos detectados:** {outliers_count:,} registros ({outliers_count/len(montos_no_cero)*100:.1f}%) están fuera del rango intercuartílico (IQR) y se excluyen del histograma principal para mejor visualización.")
                        
                        # Estadísticas robustas
                        st.markdown("#### Estadísticas Descriptivas")
                        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                        
                        with col_stat1:
                            st.metric("Mínimo", f"${montos_no_cero.min():,.0f}")
                        with col_stat2:
                            st.metric("Máximo", f"${montos_no_cero.max():,.0f}")
                        with col_stat3:
                            st.metric("Mediana", f"${montos_no_cero.median():,.0f}")
                        with col_stat4:
                            st.metric("Promedio", f"${montos_no_cero.mean():,.0f}")
                        
                        # Segunda fila de estadísticas
                        col_stat5, col_stat6, col_stat7, col_stat8 = st.columns(4)
                        
                        with col_stat5:
                            st.metric("Q1 (25%)", f"${q1:,.0f}")
                        with col_stat6:
                            st.metric("Q3 (75%)", f"${q3:,.0f}")
                        with col_stat7:
                            st.metric("Desv. Estándar", f"${montos_no_cero.std():,.0f}")
                        with col_stat8:
                            st.metric("Valores > 0", f"{valores_no_cero:,}")
                    else:
                        st.warning("No hay registros con montos mayores a cero para analizar.")
            
            elif analisis_tipo == "Análisis de Clientes":
                st.markdown("#### Análisis de Clientes")
                
                if 'es_cliente' in df_filt.columns:
                    cliente_counts = df_filt['es_cliente'].value_counts()
                    
                    fig = px.pie(
                        cliente_counts,
                        values=cliente_counts.values,
                        names=['No Cliente', 'Cliente'],
                        color_discrete_sequence=['#424e71', '#3c8198']
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            elif analisis_tipo == "Análisis de Documentos":
                st.markdown("#### Análisis de Documentos")
                
                if 'tipo_documento' in df_filt.columns:
                    doc_counts = df_filt['tipo_documento'].value_counts().head(10)
                    
                    fig = px.bar(
                        x=doc_counts.index,
                        y=doc_counts.values,
                        labels={'x': 'Tipo de Documento', 'y': 'Cantidad'},
                        color=doc_counts.values,
                        color_continuous_scale=[[0, '#bfe084'], [0.5, '#3c8198'], [1, '#424e71']]
                    )
                    fig.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de datos
            st.markdown("### Datos Filtrados")
            st.dataframe(
                df_filt.head(100),
                use_container_width=True,
                height=400
            )
        
        # Footer
        st.markdown("""
        <div style='text-align: center; padding: 1rem; color: #64748b; font-size: 0.9rem; margin-top: 3rem;'>
            Desarrollado por Faber Ospina
        </div>
        """, unsafe_allow_html=True)
    
    # === TAB 5: EXPORTACIÓN ===
    elif selected_tab == "Exportación":
        st.markdown("### Exportar Datos")
        
        if df_filt.empty:
            st.warning("No hay datos para exportar.")
        else:
            export_format = st.selectbox(
                "Formato de exportación",
                ["CSV", "Excel", "JSON"]
            )
            
            if export_format == "CSV":
                csv = df_filt.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"embargos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            elif export_format == "Excel":
                # Usar la variable global que se importó al inicio
                if not OPENPYXL_AVAILABLE:
                    st.error("No se puede exportar a Excel. La funcionalidad aun no está disponible.")
                else:
                    try:
                        from io import BytesIO
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_filt.to_excel(writer, index=False, sheet_name='Embargos')
                        excel_data = output.getvalue()
                        st.download_button(
                            label="Descargar Excel",
                            data=excel_data,
                            file_name=f"embargos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.error(f"Error al generar archivo Excel: {str(e)}")
            
            elif export_format == "JSON":
                json_str = df_filt.to_json(orient='records', date_format='iso')
                st.download_button(
                    label="Descargar JSON",
                    data=json_str,
                    file_name=f"embargos_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Resumen de exportación
            st.info(f"Se exportarán {len(df_filt):,} registros con {len(df_filt.columns)} columnas.")
        
        # Footer
        st.markdown("""
        <div style='text-align: center; padding: 1rem; color: #64748b; font-size: 0.9rem; margin-top: 3rem;'>
            Desarrollado por Faber Ospina
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

