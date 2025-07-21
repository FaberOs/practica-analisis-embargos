import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# === Utilidad para conversión segura a string de fechas ===
def to_streamlit_safe(df):
    df_safe = df.copy()
    for col in df_safe.columns:
        if pd.api.types.is_datetime64_any_dtype(df_safe[col]):
            df_safe[col] = df_safe[col].dt.strftime('%Y-%m-%d')
    return df_safe

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv("embargos_consolidado_mensual.csv", encoding='utf-8')
    df['montoaembargar'] = pd.to_numeric(df['montoaembargar'], errors='coerce').fillna(0)
    for col in ['fecha_banco', 'fecha_oficio']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    if 'es_cliente' in df.columns:
        df['es_cliente'] = pd.to_numeric(df['es_cliente'], errors='coerce').fillna(0)
    return df

df = load_data()

st.set_page_config(
    page_title="Dashboard de Oficios Bancarios",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==== Encabezado y guía ====
st.title("📊 Dashboard de Oficios Bancarios")
st.markdown("""
<div style='font-size:18px'>
<b>Interfaz interactiva y accesible</b> para explorar <b>Embargos, Desembargos y Requerimientos</b> bancarios.<br>
Aplica filtros, explora tendencias y consulta métricas clave. Todos los datos corresponden al histórico mensual consolidado.<br>
<span style='color: #0080FF;'>Consejo:</span> Utiliza las pestañas y filtros para navegar y descubrir patrones o alertas relevantes.
</div>
""", unsafe_allow_html=True)

# === Filtros sidebar con ayuda accesible ===
st.sidebar.header("Filtros interactivos")
with st.sidebar.expander("ℹ️ ¿Cómo usar los filtros?", expanded=False):
    st.markdown("""
    - **Banco, Ciudad, Entidad, etc.:** Elige uno o varios valores para personalizar los resultados.<br>
    - Puedes combinar múltiples filtros.<br>
    - Haz clic en '🔄 Restablecer filtros' para limpiar la selección.
    """, unsafe_allow_html=True)

if st.sidebar.button("🔄 Restablecer filtros"):
    st.experimental_rerun()

# Filtros principales
filtros = {
    "Banco": st.sidebar.multiselect("Banco", sorted(df['entidad_bancaria'].dropna().unique()), default=sorted(df['entidad_bancaria'].dropna().unique())),
    "Ciudad": st.sidebar.multiselect("Ciudad", sorted(df['ciudad'].dropna().unique()), default=sorted(df['ciudad'].dropna().unique())),
    "Entidad remitente": st.sidebar.multiselect("Entidad remitente", sorted(df['entidad_remitente'].dropna().unique()), default=sorted(df['entidad_remitente'].dropna().unique())),
    "Tipo de documento": st.sidebar.multiselect("Tipo de documento", sorted(df['tipo_documento'].dropna().unique()), default=sorted(df['tipo_documento'].dropna().unique())),
    "Estado embargo": st.sidebar.multiselect("Estado embargo", sorted(df['estado_embargo'].dropna().unique()), default=sorted(df['estado_embargo'].dropna().unique())),
    "Tipo embargo": st.sidebar.multiselect("Tipo embargo", sorted(df['tipo_embargo'].dropna().unique()), default=sorted(df['tipo_embargo'].dropna().unique())),
    "Mes": st.sidebar.multiselect("Mes", sorted(df['mes'].dropna().unique()), default=sorted(df['mes'].dropna().unique())),
}

# Filtros secundarios accesibles
with st.sidebar.expander("Filtros adicionales", expanded=False):
    filtro_funcionario = st.multiselect("Funcionario", sorted(df['funcionario'].dropna().unique()), default=sorted(df['funcionario'].dropna().unique()))
    filtro_estado_demandado = st.multiselect("Estado demandado", sorted(df['estado_demandado'].dropna().unique()), default=sorted(df['estado_demandado'].dropna().unique()))
    filtro_tipo_carta = st.multiselect("Tipo carta", sorted(df['tipo_carta'].dropna().unique()), default=sorted(df['tipo_carta'].dropna().unique()))

# Aplica los filtros
df_filt = df[
    df['entidad_bancaria'].isin(filtros["Banco"]) &
    df['ciudad'].isin(filtros["Ciudad"]) &
    df['entidad_remitente'].isin(filtros["Entidad remitente"]) &
    df['tipo_documento'].isin(filtros["Tipo de documento"]) &
    df['estado_embargo'].isin(filtros["Estado embargo"]) &
    df['tipo_embargo'].isin(filtros["Tipo embargo"]) &
    df['mes'].isin(filtros["Mes"]) &
    df['funcionario'].isin(filtro_funcionario) &
    df['estado_demandado'].isin(filtro_estado_demandado) &
    df['tipo_carta'].isin(filtro_tipo_carta)
]

if df_filt.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados. Por favor ajusta los filtros o haz clic en 'Restablecer filtros'.")
    st.stop()
else:
    st.success(f"Se encontraron **{len(df_filt)} registros** para los filtros actuales.")

# === Diseño de pestañas para navegación clara ===
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 KPIs Globales",
    "📊 Gráficas y Rankings",
    "🗂️ Tabla Detallada",
    "🔎 Estadísticas Avanzadas"
])

# ==== KPIs claros y accesibles ====
with tab1:
    st.subheader("Resumen mensual filtrado")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total de oficios", len(df_filt), help="Cantidad total de oficios tras aplicar los filtros.")
    kpi2.metric("Monto total embargado", f"${df_filt['montoaembargar'].sum():,.0f}", help="Suma de los montos embargados filtrados.")
    if 'mes' in df_filt.columns:
        kpi3.metric("Promedio de oficios por mes", round(df_filt.groupby('mes').size().mean(), 2), help="Promedio mensual según selección.")
    else:
        kpi3.metric("Promedio de oficios por mes", "N/A")
    kpi4.metric("Registros visualizados", min(len(df_filt), 100), help="Registros mostrados en la tabla detallada.")

    # Otros KPIs destacados con contexto
    colA, colB, colC, colD = st.columns(4)
    colA.metric("Porcentaje clientes", f"{(df_filt['es_cliente'].mean()*100):.1f}%" if 'es_cliente' in df_filt.columns else "N/A", help="Porcentaje de oficios a clientes del banco.")
    colB.metric("Monto promedio/oficio", f"${df_filt['montoaembargar'].mean():,.0f}" if len(df_filt) else "N/A", help="Monto embargado promedio por oficio.")
    colC.metric("Oficios activos", df_filt[df_filt['estado_embargo']=='Activo'].shape[0] if 'estado_embargo' in df_filt.columns else "N/A", help="Total con estado activo.")
    colD.metric("Embargos judiciales", df_filt[df_filt['tipo_embargo']=='Judicial'].shape[0] if 'tipo_embargo' in df_filt.columns else "N/A", help="Total judiciales según filtro.")

    # Proporciones visuales y tablas rápidas
    st.markdown("#### Distribución de tipos de documento y embargo")
    colx, coly = st.columns(2)
    if 'tipo_documento' in df_filt.columns:
        colx.dataframe(df_filt['tipo_documento'].value_counts().to_frame('Conteo'), use_container_width=True)
    if 'tipo_embargo' in df_filt.columns:
        coly.dataframe(df_filt['tipo_embargo'].value_counts().to_frame('Conteo'), use_container_width=True)

# ==== Gráficas amigables e interactivas ====
with tab2:
    st.subheader("Tendencias y rankings de oficios")

    if 'mes' in df_filt.columns:
        with st.expander("📅 Oficios mensuales (realiza zoom o hover)", expanded=True):
            df_time = df_filt.groupby('mes').size().reset_index(name='oficios')
            fig = px.line(df_time, x='mes', y='oficios', markers=True, title="Evolución mensual de oficios", labels={"mes": "Mes", "oficios": "Cantidad"})
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Interactúa: haz zoom o consulta valores pasando el mouse.")

    st.markdown("#### Top 10 ciudades, entidades y funcionarios con más oficios")
    col1, col2, col3 = st.columns(3)
    top_ciudades = df_filt['ciudad'].value_counts().head(10)
    top_entidades = df_filt['entidad_remitente'].value_counts().head(10)
    top_funcionarios = df_filt['funcionario'].value_counts().head(10)
    with col1:
        st.bar_chart(top_ciudades, use_container_width=True)
        st.caption("Top ciudades")
    with col2:
        st.bar_chart(top_entidades, use_container_width=True)
        st.caption("Top entidades remitentes")
    with col3:
        st.bar_chart(top_funcionarios, use_container_width=True)
        st.caption("Top funcionarios")

    if 'tipo_embargo' in df_filt.columns and 'mes' in df_filt.columns:
        with st.expander("⚖️ Proporciones Judicial/Coactivo por mes", expanded=False):
            prop_tipo = df_filt.pivot_table(index='mes', columns='tipo_embargo', values='id', aggfunc='count', fill_value=0)
            prop_tipo = prop_tipo.div(prop_tipo.sum(axis=1), axis=0)  # proporciones por mes
            fig2 = px.area(
                prop_tipo, x=prop_tipo.index, y=prop_tipo.columns,
                title="Judicial vs Coactivo (proporción mensual)",
                labels={"value": "Proporción", "mes": "Mes", "variable": "Tipo"}
            )
            fig2.update_traces(line=dict(width=0.5))
            st.plotly_chart(fig2, use_container_width=True)
            st.caption("Visualiza la proporción mensual según tipo de embargo.")

# ==== Detalle accesible, descarga y preview ====
with tab3:
    st.subheader("Detalle de datos filtrados (primeros 100 registros)")
    st.dataframe(to_streamlit_safe(df_filt.head(100)), use_container_width=True)
    st.caption("Muestra limitada para facilitar la exploración rápida. Usa los filtros para refinar.")

    st.download_button(
        label="⬇️ Descargar datos filtrados (CSV)",
        data=to_streamlit_safe(df_filt).to_csv(index=False).encode('utf-8'),
        file_name='embargos_filtrados.csv',
        mime='text/csv'
    )

# ==== Estadísticas Avanzadas amigables y sin errores Arrow ====
with tab4:
    st.subheader("Estadísticas avanzadas y exploración completa")

    # Estadísticas numéricas (solo numéricas)
    st.markdown("##### Estadísticas resumen numéricas")
    num_cols = df_filt.select_dtypes(include=[np.number]).columns
    if len(num_cols):
        st.dataframe(df_filt[num_cols].describe().transpose(), use_container_width=True)
    else:
        st.info("No hay columnas numéricas en la selección actual.")

    # Estadísticas categóricas (solo objeto/categórico)
    st.markdown("##### Estadísticas resumen categóricas")
    cat_cols = [col for col in df_filt.select_dtypes(include=['object', 'category']).columns
                if not pd.api.types.is_datetime64_any_dtype(df_filt[col])]
    if cat_cols:
        st.dataframe(df_filt[cat_cols].describe().transpose(), use_container_width=True)
    else:
        st.info("No hay columnas categóricas en la selección actual.")

    # Estadísticas fechas (min, max, únicos)
    st.markdown("##### Estadísticas de columnas de fecha")
    date_cols = df_filt.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns
    if len(date_cols):
        st.dataframe(
            pd.DataFrame({
                col: [
                    df_filt[col].min(),
                    df_filt[col].max(),
                    df_filt[col].nunique()
                ] for col in date_cols
            }, index=["Mínimo", "Máximo", "Valores únicos"]).transpose(),
            use_container_width=True
        )
    else:
        st.info("No hay columnas de fecha en la selección actual.")

    # Frecuencias de campos categóricos principales
    st.markdown("##### Frecuencias de campos categóricos seleccionados")
    for cat_col in ['tipo_identificacion_tipo', 'estado_embargo', 'tipo_documento', 'tipo_embargo', 'estado_demandado', 'es_cliente', 'tipo_carta']:
        if cat_col in df_filt.columns:
            st.write(f"**{cat_col}**")
            st.dataframe(df_filt[cat_col].value_counts().to_frame("Conteo"), use_container_width=True)

    st.markdown("##### Vista rápida de registros (10 primeros)")
    st.dataframe(to_streamlit_safe(df_filt.head(10)), use_container_width=True)

st.markdown("---")
st.caption("🖥️ Desarrollado por Faber Ospina.")
