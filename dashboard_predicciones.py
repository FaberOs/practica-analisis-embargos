import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Predicciones y Métricas", layout="wide", initial_sidebar_state="expanded")
st.title("🔎 Dashboard de Predicción y Evaluación - Oficios Bancarios")

st.markdown("""
Bienvenido al dashboard interactivo para el análisis de **predicciones, desempeño y métricas** de modelos sobre embargos bancarios.
Navega entre las pestañas, explora tendencias, compara valores reales vs predichos y descarga los resultados.
""")

# --- Carga de datos ---
@st.cache_data(show_spinner=False)
def load_csv(name):
    return pd.read_csv(name)

df_oficios = load_csv("predicciones_oficios_por_mes.csv")
df_demandados = load_csv("predicciones_demandados_por_mes.csv")
df_metricas = load_csv("resultados_clasificaciones.csv")

tab1, tab2, tab3 = st.tabs([
    "📅 Predicción de Oficios", 
    "📅 Predicción de Demandados",
    "📊 Métricas de Clasificación"
])

# 1. Predicción de Oficios por mes
with tab1:
    st.header("📅 Oficios por mes: Real vs Predicción")
    st.markdown("""
    Visualiza la evolución mensual del **total de oficios**. Compara los valores reales vs. la predicción del modelo.
    """)
    fig1 = px.line(df_oficios, x="mes", y=["real_oficios", "pred_oficios"], markers=True,
        labels={"value": "Cantidad de oficios", "variable": "Serie"}, 
        title="Oficios por mes: Real vs Predicción"
    )
    fig1.update_traces(line=dict(width=3))
    st.plotly_chart(fig1, use_container_width=True)
    st.dataframe(df_oficios, use_container_width=True)
    st.download_button(
        "⬇️ Descargar CSV de predicción de oficios", 
        df_oficios.to_csv(index=False).encode("utf-8"),
        file_name="predicciones_oficios_por_mes.csv", mime="text/csv"
    )

# 2. Predicción de demandados únicos
with tab2:
    st.header("📅 Demandados únicos por mes: Real vs Predicción")
    st.markdown("""
    Visualiza la evolución mensual del **número de demandados únicos**. Compara el valor real vs. la predicción.
    """)
    fig2 = px.line(df_demandados, x="mes", y=["real_demandados", "pred_demandados"], markers=True,
        labels={"value": "Cantidad de demandados", "variable": "Serie"},
        title="Demandados únicos por mes: Real vs Predicción"
    )
    fig2.update_traces(line=dict(width=3))
    st.plotly_chart(fig2, use_container_width=True)
    st.dataframe(df_demandados, use_container_width=True)
    st.download_button(
        "⬇️ Descargar CSV de predicción de demandados", 
        df_demandados.to_csv(index=False).encode("utf-8"),
        file_name="predicciones_demandados_por_mes.csv", mime="text/csv"
    )

# 3. Métricas de Clasificación
with tab3:
    st.header("📊 Resultados y métricas de clasificación")
    st.markdown("""
    Consulta la precisión, recall y F1-score de cada modelo, desglosados por clase y tipo de predicción.
    Filtra y ordena la tabla según tu necesidad.
    """)
    col1, col2 = st.columns(2)
    modelos = df_metricas["modelo"].unique().tolist()
    clases = sorted(df_metricas["clase"].unique().tolist())
    modelo_sel = col1.multiselect("Filtrar por modelo", modelos, default=modelos)
    clase_sel = col2.multiselect("Filtrar por clase", clases, default=clases)
    df_filt = df_metricas[
        df_metricas["modelo"].isin(modelo_sel) & df_metricas["clase"].isin(clase_sel)
    ]
    st.dataframe(df_filt, use_container_width=True)
    st.download_button(
        "⬇️ Descargar métricas de clasificación", 
        df_metricas.to_csv(index=False).encode("utf-8"),
        file_name="resultados_clasificaciones.csv", mime="text/csv"
    )
    # Resúmenes visuales rápidos
    if st.checkbox("Mostrar resumen gráfico (F1 por modelo)", value=True):
        fig3 = px.bar(
            df_filt, x="clase", y="f1", color="modelo",
            barmode="group", title="F1-score por modelo y clase",
            labels={"f1":"F1-score", "clase":"Clase"}
        )
        st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.caption("Desarrollado por Faber Ospina")
