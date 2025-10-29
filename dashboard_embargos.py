# -*- coding: utf-8 -*-
"""
Dashboard de Oficios Bancarios — HCI + Paleta Unicauca (smart-filters, robusto)
- Azul institucional: #001282
- Rojo institucional: #AD0000
- CSV principal: embargos_consolidado_mensual_sample.csv
- Muestreo opcional para datasets pesados
- Smart-filters para listas gigantes (ciudad, entidad_remitente, funcionario)
- Filtros que no seleccionan "todo" por defecto (no hay chips interminables)
- Render Plotly unificado (use_container_width)
"""

# =========================
# 0) Imports y configuración
# =========================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

st.set_page_config(
    page_title="Dashboard de Oficios Bancarios",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📘",
)

# ---- Paleta Unicauca + estilos de apoyo
UNICAUCA_BLUE = "#001282"
UNICAUCA_RED  = "#AD0000"
BG_SOFT       = "#F5F7FA"
BORDER_SOFT   = "#E6EAF0"

st.markdown(f"""
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{ --u-blue:{UNICAUCA_BLUE}; --u-red:{UNICAUCA_RED}; --bgsoft:{BG_SOFT}; --bsoft:{BORDER_SOFT}; }}
html, body, [class^="css"] {{
  font-family: 'Open Sans', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}}
h1,h2,h3,h4 {{ color: var(--u-blue); }}
.stButton>button, .st-download-button>button {{
  background: var(--u-blue); color:#fff; border:0; border-radius:10px; padding:.5rem 1rem;
}}
.stButton>button:hover, .st-download-button>button:hover {{ filter:brightness(1.06); }}
.metric-card {{
  background: var(--bgsoft); border:1px solid var(--bsoft); border-radius:12px; padding:12px 14px; margin-bottom:8px;
}}
.small-note {{ color:#5b6270; font-size:.9rem; }}
.help-note {{ color:#6a7280; font-size:.85rem; margin-top:-8px; }}
hr.soft {{ border:none; border-top:1px solid var(--bsoft); margin:8px 0 4px; }}
</style>
""", unsafe_allow_html=True)

# =========================
# 1) Utilidades
# =========================
SAFE_MIN_DT = pd.Timestamp("1677-09-21")
SAFE_MAX_DT = pd.Timestamp("2262-04-11")

HEAVY_LIMIT = 200_000
SAMPLE_FOR_HEAVY = 30_000

def show_fig(fig):
    """Render uniforme para Plotly."""
    st.plotly_chart(
        fig,
        config={"displaylogo": False, "responsive": True, "scrollZoom": True, "doubleClick": "reset"},
        use_container_width=True,
    )

def to_streamlit_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte datetimes a 'YYYY-MM-DD' (evita errores de Arrow en la tabla)."""
    df_safe = df.copy()
    for col in df_safe.columns:
        if pd.api.types.is_datetime64_any_dtype(df_safe[col]):
            df_safe[col] = df_safe[col].dt.strftime("%Y-%m-%d")
    return df_safe

def safe_parse_datetime(series: pd.Series) -> pd.Series:
    """Parseo robusto de fechas."""
    s = pd.to_datetime(series, errors="coerce", utc=True)
    try:
        s = s.dt.tz_convert(None)
    except Exception:
        s = s.dt.tz_localize(None) if hasattr(s.dt, "tz_localize") else s
    s = s.mask(~s.between(SAFE_MIN_DT, SAFE_MAX_DT))
    return s

@st.cache_data(show_spinner=False, ttl=120)
def load_data() -> pd.DataFrame:
    """Lee CSV y sanea tipos."""
    try:
        df = pd.read_csv("embargos_consolidado_mensual_sample.csv", encoding="utf-8", low_memory=False)
    except Exception as e:
        st.error(f"No se pudo leer el CSV principal: {e}")
        return pd.DataFrame()

    if "montoaembargar" in df.columns:
        df["montoaembargar"] = pd.to_numeric(df["montoaembargar"], errors="coerce").fillna(0)

    for col in ["fecha_banco", "fecha_oficio"]:
        if col in df.columns:
            df[col] = safe_parse_datetime(df[col])

    if "mes" in df.columns:
        m = pd.to_datetime(df["mes"], errors="coerce", utc=True)
        try:
            m = m.dt.tz_convert(None)
        except Exception:
            m = m.dt.tz_localize(None) if hasattr(m.dt, "tz_localize") else m
        m = m.mask(~m.between(SAFE_MIN_DT, SAFE_MAX_DT))
        df["mes"] = m.dt.to_period("M").dt.to_timestamp()

    if "es_cliente" in df.columns:
        def _to_bin(v):
            s = str(v).strip().upper()
            return 1 if s in {"1","SI","SÍ","TRUE","YES","CLIENTE"} else 0
        if not pd.api.types.is_numeric_dtype(df["es_cliente"]):
            df["es_cliente"] = df["es_cliente"].map(_to_bin).fillna(0).astype(int)
        else:
            df["es_cliente"] = pd.to_numeric(df["es_cliente"], errors="coerce").fillna(0).astype(int)

    return df

def col_exists(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns

@st.cache_data(show_spinner=False, ttl=300)
def uniques_with_freq(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Devuelve DataFrame con valores únicos y conteo (desc)."""
    if not col_exists(df, col):
        return pd.DataFrame(columns=["valor","conteo"])
    vc = (df[col].fillna("DESCONOCIDO").astype(str).value_counts(dropna=False)
          .rename_axis("valor").reset_index(name="conteo"))
    return vc

def normalize_tokens(raw: str) -> list:
    """Tokeniza cadena separada por comas/lineas; limpia espacios y vacíos."""
    if not raw:
        return []
    # admite separadores: coma, punto y coma, salto de línea
    parts = re.split(r"[,\n;]+", str(raw))
    return [p.strip() for p in parts if p.strip()]

def smart_filter(
    df: pd.DataFrame,
    col: str,
    label: str,
    key: str,
    max_show: int = 400,
    top_default: int = 30
):
    """
    Smart-filter para columnas gigantes:
    - Campo de búsqueda (subcadena, insensible a mayúsculas)
    - Pegar lista masiva (coma/por línea)
    - Ver 'Top N' por frecuencia
    - Multiselect SOLO sobre coincidencias (no selecciona todo por defecto)
    Retorna lista o None (si no aplica / vacío).
    """
    if not col_exists(df, col):
        return None

    with st.sidebar.expander(f"{label}", expanded=False):
        vc = uniques_with_freq(df, col)
        total_uni = int(vc.shape[0])

        q = st.text_input("Buscar...", value="", key=f"{key}_q").strip().lower()
        bulk = st.text_area("Pega valores (coma/una por línea)", value="", key=f"{key}_bulk")
        tokens = [t.lower() for t in normalize_tokens(bulk)]

        mode = st.radio(
            "Fuente de opciones",
            options=["Coincidencias", f"Top {top_default} por frecuencia"],
            horizontal=True,
            key=f"{key}_mode"
        )

        if mode.startswith("Top"):
            opts = vc.head(top_default)["valor"].astype(str).tolist()
            st.markdown(f"<div class='help-note'>Mostrando los {top_default} más frecuentes de {total_uni} únicos.</div>", unsafe_allow_html=True)
        else:
            # Coincidencias por búsqueda/tokens
            cand = vc["valor"].astype(str).tolist()
            if q:
                cand = [x for x in cand if q in x.lower()]
            if tokens:
                # unión: cualquiera que contenga uno de los tokens
                extra = [x for x in vc["valor"].astype(str).tolist() if any(t in x.lower() for t in tokens)]
                # mantener orden estable
                seen = set()
                cand = [x for x in cand + extra if not (x in seen or seen.add(x))]
            # límite visual
            if len(cand) > max_show:
                cand = cand[:max_show]
                st.markdown(f"<div class='help-note'>Se muestran {max_show} coincidencias (de {total_uni}). Afina la búsqueda.</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='help-note'>Coincidencias: {len(cand)} de {total_uni}.</div>", unsafe_allow_html=True)
            opts = cand

        sel = st.multiselect("Selecciona (opcional)", options=opts, default=[], key=f"{key}_sel")
        # Si no hay selección => filtro inactivo
        return sel if len(sel) > 0 else None

def safe_multiselect(label: str, df: pd.DataFrame, col: str, key: str):
    """
    Multiselect limpio (sin preseleccionar todo). Si el usuario no escoge nada,
    retorna None (filtro inactivo).
    """
    if not col_exists(df, col):
        return None
    opts = df[col].dropna().astype(str).unique().tolist()
    opts = sorted(opts, key=lambda x: x)
    sel = st.sidebar.multiselect(label, opts, default=[], key=key)
    return sel if len(sel) > 0 else None

def apply_filters(df: pd.DataFrame, selections: dict) -> pd.DataFrame:
    """Aplica filtros de inclusión solo cuando hay selección. None => inactivo."""
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)
    for col, values in selections.items():
        if values is None:
            continue
        mask &= df[col].astype(str).isin([str(v) for v in values])
    return df[mask].copy()

def apply_post_filters(df: pd.DataFrame,
                       rango_monto: tuple|None,
                       query_text: str|None,
                       rango_fechas: tuple|None) -> pd.DataFrame:
    """Filtra por monto, búsqueda rápida y rango temporal (mes o fecha_banco) si existen."""
    if df.empty:
        return df
    out = df.copy()

    if rango_monto and col_exists(out, "montoaembargar"):
        lo, hi = float(rango_monto[0]), float(rango_monto[1])
        out = out[(out["montoaembargar"] >= lo) & (out["montoaembargar"] <= hi)]

    if rango_fechas:
        d0, d1 = pd.to_datetime(rango_fechas[0]), pd.to_datetime(rango_fechas[1])
        if col_exists(out, "mes"):
            out = out[(out["mes"] >= d0) & (out["mes"] <= d1)]
        elif col_exists(out, "fecha_banco"):
            out = out[(out["fecha_banco"] >= d0) & (out["fecha_banco"] <= d1)]

    if query_text:
        q = str(query_text).strip().lower()
        campos = [c for c in ["referencia","identificacion","nombres","expediente","correo","cuenta"] if col_exists(out, c)]
        if campos:
            m = pd.Series(False, index=out.index)
            for c in campos:
                m |= out[c].astype(str).str.lower().str.contains(q, na=False)
            out = out[m]

    return out

def count_eq(df: pd.DataFrame, col: str, value_upper: str) -> int:
    if not col_exists(df, col):
        return 0
    return int((df[col].astype(str).str.upper() == value_upper).sum())

def pareto_df(series: pd.Series, top_n=15) -> pd.DataFrame:
    vc = series.fillna("DESCONOCIDO").astype(str).value_counts().head(top_n)
    dfp = vc.reset_index()
    dfp.columns = ["categoria", "conteo"]
    dfp["conteo"] = pd.to_numeric(dfp["conteo"], errors="coerce").fillna(0.0).astype(float)
    dfp["acum"] = dfp["conteo"].cumsum()
    total = float(dfp["conteo"].sum())
    denom = total if total > 0 else 1.0
    dfp["pct"] = 100.0 * dfp["conteo"] / denom
    dfp["pct_acum"] = 100.0 * dfp["acum"] / denom
    return dfp

def sankey_from_cols(df: pd.DataFrame, cols, min_count=1):
    for c in cols:
        if not col_exists(df, c):
            return None
    labels = []
    for c in cols:
        labels += df[c].fillna("DESCONOCIDO").astype(str).unique().tolist()
    labels = list(dict.fromkeys(labels))
    idx = {lab:i for i, lab in enumerate(labels)}
    source, target, value = [], [], []
    for i in range(len(cols)-1):
        a, b = cols[i], cols[i+1]
        g = (df[[a,b]].fillna("DESCONOCIDO").astype(str)
             .value_counts().reset_index(name="conteo"))
        g = g[g["conteo"] >= min_count]
        source += g[a].map(idx).tolist()
        target += g[b].map(idx).tolist()
        value  += g["conteo"].tolist()
    if not value:
        return None
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=18, line=dict(color="black", width=0.2), label=labels, color="#AAB7C4"),
        link=dict(source=source, target=target, value=value)
    )])
    fig.update_layout(title="Flujos entre actores (Sankey)", font_size=12)
    return fig

def thin_sample(df: pd.DataFrame, use_sample: bool, n_rows: int, seed: int) -> pd.DataFrame:
    if not use_sample or df.empty:
        return df
    n = int(min(max(n_rows, 1), len(df)))
    return df.sample(n=n, random_state=seed)

# =========================
# 2) Carga + muestreo opcional
# =========================
df_full = load_data()

st.sidebar.header("⚙️ Modo de trabajo")
use_sample = st.sidebar.checkbox("Trabajar con una muestra del dataset", value=True,
                                 help="Útil cuando el CSV está pesado. Afecta todo el dashboard.")
sample_rows = st.sidebar.number_input("Tamaño de la muestra", min_value=100, max_value=200_000, step=1000, value=20_000)
sample_seed = st.sidebar.number_input("Semilla aleatoria", min_value=0, max_value=1_000_000, step=1, value=42)

df = thin_sample(df_full, use_sample, sample_rows, sample_seed)

# columna derivada para relaciones
if col_exists(df, "fecha_banco") and col_exists(df, "fecha_oficio"):
    try:
        df["dias_tramite"] = (df["fecha_banco"] - df["fecha_oficio"]).dt.days
    except Exception:
        df["dias_tramite"] = np.nan

# =========================
# 3) Encabezado
# =========================
st.title("📊 Dashboard de Oficios Bancarios")
st.markdown("""
<div style='font-size:17px'>
Interfaz <b>clara y accesible</b> para explorar <b>Embargos, Desembargos y Requerimientos</b> bancarios.<br>
Usa los filtros de la izquierda; las métricas y gráficos se actualizan al instante.
</div>
""", unsafe_allow_html=True)

# =========================
# 4) Filtros (sidebar)
# =========================
with st.sidebar.expander("ℹ️ ¿Cómo usar los filtros?", expanded=False):
    st.markdown("""
- Los **filtros grandes** (ciudad, remitente, funcionario) usan buscador/pegado masivo.
- Si no seleccionas nada en un filtro, **no se aplica**.
- Si te quedas sin resultados, ajusta o **Restablece**.
    """)

# Reset real
if st.sidebar.button("🔄 Restablecer filtros"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

st.sidebar.subheader("🎯 Filtros rápidos")
sel_banco       = safe_multiselect("Banco", df, "entidad_bancaria", key="f_banco")
sel_tipo_doc    = safe_multiselect("Tipo de documento", df, "tipo_documento", key="f_tipo_doc")
sel_estado_emb  = safe_multiselect("Estado embargo", df, "estado_embargo", key="f_estado_emb")
sel_tipo_emb    = safe_multiselect("Tipo embargo", df, "tipo_embargo", key="f_tipo_emb")
sel_mes         = safe_multiselect("Mes", df, "mes", key="f_mes")

st.sidebar.subheader("🧭 Filtros masivos (autocompletar)")
sel_ciudad      = smart_filter(df, "ciudad", "Ciudad", key="sf_ciudad", max_show=400, top_default=30)
sel_ent_rem     = smart_filter(df, "entidad_remitente", "Entidad remitente", key="sf_ent_rem", max_show=400, top_default=30)
sel_funcionario = smart_filter(df, "funcionario", "Funcionario", key="sf_funcionario", max_show=400, top_default=30)

with st.sidebar.expander("🔎 Búsqueda y rangos", expanded=False):
    if col_exists(df, "montoaembargar") and not df["montoaembargar"].dropna().empty:
        vmin, vmax = float(df["montoaembargar"].min()), float(df["montoaembargar"].max())
        rango_monto = st.slider(
            "Rango de monto a embargar",
            min_value=float(np.floor(vmin)),
            max_value=float(np.ceil(vmax)),
            value=(float(np.floor(vmin)), float(np.ceil(vmax))),
        )
    else:
        rango_monto = None

    if col_exists(df, "mes") and not df["mes"].dropna().empty:
        d0, d1 = df["mes"].min(), df["mes"].max()
    elif col_exists(df, "fecha_banco") and not df["fecha_banco"].dropna().empty:
        d0, d1 = df["fecha_banco"].min(), df["fecha_banco"].max()
    else:
        d0 = d1 = pd.Timestamp("today")
    fecha_range = st.date_input("Rango temporal", (d0.date(), d1.date()) if d0 <= d1 else ())
    rango_fechas = (pd.to_datetime(fecha_range[0]), pd.to_datetime(fecha_range[1])) if isinstance(fecha_range, tuple) and len(fecha_range) == 2 else None

    txt_busqueda = st.text_input("Búsqueda rápida (ref/ident/nombres/correo/cuenta)", value="").strip()

# Construye diccionario de filtros → aplica
selections = {
    "entidad_bancaria": sel_banco,
    "ciudad": sel_ciudad,
    "entidad_remitente": sel_ent_rem,
    "tipo_documento": sel_tipo_doc,
    "estado_embargo": sel_estado_emb,
    "tipo_embargo": sel_tipo_emb,
    "mes": sel_mes,
    "funcionario": sel_funcionario,
}
df_filt = apply_filters(df, selections)
df_filt = apply_post_filters(df_filt, rango_monto, txt_busqueda, rango_fechas)

# Guardas y feedback
if df_full.empty:
    st.warning("⚠️ No se pudo cargar ningún CSV. Verifica el archivo en el directorio.")
    st.stop()

if df_filt.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados. Ajusta los filtros o pulsa **Restablecer filtros**.")
    st.stop()
else:
    st.success(f"Se encontraron **{len(df_filt):,}** registros para los filtros actuales."
               + (" (modo muestra activo)" if use_sample else ""))

# =========================
# 5) Pestañas de navegación
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 KPIs Globales",
    "📊 Gráficas y Rankings",
    "🗂️ Tabla Detallada",
    "🔎 Estadísticas Avanzadas"
])

# =========================
# 6) KPIs
# =========================
with tab1:
    st.subheader("Resumen mensual filtrado")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total de oficios", len(df_filt), help="Cantidad total tras aplicar los filtros.")
    monto_total = df_filt["montoaembargar"].sum() if col_exists(df_filt, "montoaembargar") else 0.0
    k2.metric("Monto total embargado", f"${monto_total:,.0f}", help="Suma de montos embargados en la selección.")
    if col_exists(df_filt, "mes"):
        prom_mes = df_filt.groupby("mes").size().mean()
        k3.metric("Promedio de oficios por mes", f"{prom_mes:.2f}")
    else:
        k3.metric("Promedio de oficios por mes", "N/A")
    k4.metric("Registros visualizados", min(len(df_filt), 100), help="En la tabla detallada se listan los primeros 100.")

    st.markdown("#### Indicadores adicionales")
    cA, cB, cC, cD = st.columns(4)
    if col_exists(df_filt, "es_cliente"):
        pct_clientes = 100 * (df_filt["es_cliente"].astype(float).mean())
        cA.metric("Porcentaje clientes", f"{pct_clientes:.1f}%")
    else:
        cA.metric("Porcentaje clientes", "N/A")
    cB.metric("Monto promedio/oficio",
              f"${(df_filt['montoaembargar'].mean() if col_exists(df_filt,'montoaembargar') and len(df_filt) else 0):,.0f}")
    cC.metric("Oficios activos", count_eq(df_filt, "estado_embargo", "ACTIVO"))
    cD.metric("Embargos judiciales", count_eq(df_filt, "tipo_embargo", "JUDICIAL"))

    st.markdown("#### Distribución de tipos de documento y embargo")
    d1, d2 = st.columns(2)
    if col_exists(df_filt, "tipo_documento"):
        d1.dataframe(df_filt["tipo_documento"].value_counts(dropna=False).to_frame("Conteo"), use_container_width=True)
    if col_exists(df_filt, "tipo_embargo"):
        d2.dataframe(df_filt["tipo_embargo"].value_counts(dropna=False).to_frame("Conteo"), use_container_width=True)

# =========================
# 7) Gráficas y rankings
# =========================
with tab2:
    st.subheader("Tendencias y rankings de oficios")

    if col_exists(df_filt, "mes"):
        with st.expander("📅 Oficios mensuales (interactivo)", expanded=True):
            df_time = df_filt.groupby("mes").agg(
                oficios=("id","count") if col_exists(df_filt, "id") else ("mes","size"),
                monto=("montoaembargar","sum") if col_exists(df_filt,"montoaembargar") else ("mes","size")
            ).reset_index().sort_values("mes")

            fig = px.line(df_time, x="mes", y="oficios", markers=True,
                          title="Evolución mensual de oficios",
                          labels={"mes":"Mes","oficios":"Cantidad"})
            fig.update_traces(line=dict(width=3), marker=dict(size=8))
            fig.update_traces(line_color=UNICAUCA_BLUE, selector=dict(mode="lines+markers"))
            show_fig(fig)

            if "monto" in df_time.columns:
                fig_m = px.area(df_time, x="mes", y="monto",
                                title="Monto embargado por mes (área)",
                                labels={"mes":"Mes","monto":"Monto"})
                show_fig(fig_m)
            st.caption("Haz zoom y pasa el cursor para ver valores.")

        if col_exists(df_filt, "tipo_embargo"):
            with st.expander("⚖️ Proporción mensual por tipo de embargo (apilada)", expanded=False):
                tmp = df_filt.groupby(["mes","tipo_embargo"]).size().reset_index(name="conteo")
                fig2 = px.bar(tmp, x="mes", y="conteo", color="tipo_embargo",
                              title="Oficios por mes y tipo de embargo (barras apiladas)")
                show_fig(fig2)

        if col_exists(df_filt, "estado_embargo"):
            with st.expander("📚 Proporción mensual por estado del embargo (apilada)", expanded=False):
                tmp2 = df_filt.groupby(["mes","estado_embargo"]).size().reset_index(name="conteo")
                fig3 = px.bar(tmp2, x="mes", y="conteo", color="estado_embargo",
                              title="Oficios por mes y estado del embargo (barras apiladas)")
                show_fig(fig3)

    st.markdown("#### Top 10 por volumen")
    b1, b2, b3 = st.columns(3)

    def top_bar(colname, titulo=None):
        if col_exists(df_filt, colname):
            top = df_filt[colname].fillna("DESCONOCIDO").astype(str).value_counts().head(10).reset_index()
            top.columns = [colname, "Conteo"]
            figb = px.bar(top, x=colname, y="Conteo", title=titulo or f"Top 10 — {colname}",
                          color_discrete_sequence=[UNICAUCA_RED])
            figb.update_layout(xaxis_title=None)
            show_fig(figb)

    top_bar("ciudad", "Top 10 — Ciudad")
    top_bar("entidad_remitente", "Top 10 — Entidad remitente")
    top_bar("funcionario", "Top 10 — Funcionario")

    d3, d4 = st.columns(2)
    if col_exists(df_filt, "estado_embargo"):
        pie1 = px.pie(df_filt, names=df_filt["estado_embargo"].fillna("DESCONOCIDO"),
                      title="Composición por estado del embargo", hole=0.5)
        show_fig(pie1)
    if col_exists(df_filt, "tipo_embargo"):
        pie2 = px.pie(df_filt, names=df_filt["tipo_embargo"].fillna("DESCONOCIDO"),
                      title="Composición por tipo de embargo", hole=0.5)
        show_fig(pie2)

    if col_exists(df_filt, "entidad_remitente") and col_exists(df_filt, "entidad_bancaria"):
        st.markdown("#### Jerarquías por actor")
        base_tm = df_filt.copy()
        base_tm["entidad_remitente"] = base_tm["entidad_remitente"].fillna("DESCONOCIDO").astype(str)
        base_tm["entidad_bancaria"]  = base_tm["entidad_bancaria"].fillna("DESCONOCIDO").astype(str)
        base_tm["valor"] = 1
        treemap = px.treemap(base_tm, path=["entidad_remitente","entidad_bancaria"], values="valor",
                             title="Treemap: remitente → banco")
        show_fig(treemap)
        sunb = px.sunburst(base_tm, path=["entidad_remitente","entidad_bancaria"], values="valor",
                           title="Sunburst: remitente → banco")
        show_fig(sunb)

    if col_exists(df_filt, "entidad_remitente"):
        st.markdown("#### Análisis Pareto (entidad_remitente)")
        dpf = pareto_df(df_filt["entidad_remitente"])
        figp = go.Figure()
        figp.add_bar(x=dpf["categoria"], y=dpf["conteo"], name="Conteo", marker_color=UNICAUCA_BLUE)
        figp.add_trace(go.Scatter(x=dpf["categoria"], y=dpf["pct_acum"], name="% acumulado",
                                  mode="lines+markers", yaxis="y2",
                                  line=dict(color=UNICAUCA_RED, width=3)))
        figp.update_layout(
            title="Pareto de oficios por entidad remitente",
            yaxis=dict(title="Conteo"),
            yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0,100])
        )
        show_fig(figp)

# =========================
# 8) Tabla detallada + descarga
# =========================
with tab3:
    st.subheader("Detalle de datos filtrados (primeros 100 registros)")
    st.dataframe(to_streamlit_safe(df_filt.head(100)), use_container_width=True)
    st.caption("Vista limitada para exploración rápida. Ajusta filtros para refinar.")

    st.download_button(
        label="⬇️ Descargar datos filtrados (CSV)",
        data=to_streamlit_safe(df_filt).to_csv(index=False).encode("utf-8"),
        file_name="embargos_filtrados.csv",
        mime="text/csv"
    )

# =========================
# 9) Estadísticas avanzadas
# =========================
with tab4:
    st.subheader("Estadísticas avanzadas")

    st.markdown("##### Resumen numérico")
    num_cols = df_filt.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        st.dataframe(df_filt[num_cols].describe().transpose(), use_container_width=True)
    else:
        st.info("No hay columnas numéricas en la selección actual.")

    st.markdown("##### Resumen categórico")
    cat_cols = [c for c in df_filt.select_dtypes(include=["object","category"]).columns
                if not pd.api.types.is_datetime64_any_dtype(df_filt[c])]
    if cat_cols:
        st.dataframe(df_filt[cat_cols].describe().transpose(), use_container_width=True)
    else:
        st.info("No hay columnas categóricas en la selección actual.")

    st.markdown("##### Resumen de fechas")
    date_cols = df_filt.select_dtypes(include=["datetime64[ns]","datetime64[ns, UTC]"]).columns.tolist()
    if date_cols:
        info = pd.DataFrame({
            c: [df_filt[c].min(), df_filt[c].max(), df_filt[c].nunique()]
            for c in date_cols
        }, index=["Mínimo","Máximo","Valores únicos"]).transpose()
        st.dataframe(info, use_container_width=True)
    else:
        st.info("No hay columnas de fecha en la selección actual.")

    st.markdown("##### Distribuciones de monto")
    if col_exists(df_filt, "montoaembargar"):
        show_fig(px.histogram(df_filt, x="montoaembargar", nbins=40, title="Histograma de montos"))
        if col_exists(df_filt, "tipo_embargo"):
            show_fig(px.box(df_filt, x="tipo_embargo", y="montoaembargar", title="Boxplot monto por tipo"))
            show_fig(px.violin(df_filt, x="tipo_embargo", y="montoaembargar", box=True, points="outliers",
                               title="Violin monto por tipo"))

    st.markdown("##### Relaciones")
    if col_exists(df_filt, "dias_tramite") and col_exists(df_filt, "montoaembargar"):
        fig_sc = px.scatter(df_filt, x="dias_tramite", y="montoaembargar",
                            color=df_filt["tipo_embargo"] if col_exists(df_filt,"tipo_embargo") else None,
                            title="Días de trámite vs monto",
                            labels={"dias_tramite":"Días (banco − oficio)","montoaembargar":"Monto"})
        show_fig(fig_sc)

    if col_exists(df_filt, "ciudad") and col_exists(df_filt, "mes"):
        st.markdown("##### Heatmap ciudad × mes")
        df_hm = df_filt
        if len(df_hm) > HEAVY_LIMIT:
            df_hm = df_hm.sample(n=min(SAMPLE_FOR_HEAVY, len(df_hm)), random_state=sample_seed)
            st.info(f"Heatmap usando muestra de {len(df_hm):,} filas por tamaño.")
        top_ciudades = df_hm["ciudad"].fillna("DESCONOCIDO").astype(str).value_counts().head(15).index
        piv = (df_hm[df_hm["ciudad"].fillna("DESCONOCIDO").astype(str).isin(top_ciudades)]
               .groupby(["ciudad","mes"]).size().reset_index(name="conteo"))
        tabla = piv.pivot_table(index="ciudad", columns="mes", values="conteo", fill_value=0)
        fig_hm = px.imshow(tabla, aspect="auto", title="Oficios por ciudad y mes", color_continuous_scale="Blues")
        show_fig(fig_hm)

    if num_cols:
        st.markdown("##### Correlación numérica")
        df_corr = df_filt
        if len(df_corr) > HEAVY_LIMIT:
            df_corr = df_corr.sample(n=min(SAMPLE_FOR_HEAVY, len(df_corr)), random_state=sample_seed)
            st.info(f"Correlación usando muestra de {len(df_corr):,} filas por tamaño.")
        corr = df_corr[num_cols].corr(numeric_only=True)
        fig_corr = px.imshow(corr, text_auto=True, aspect="auto", title="Correlación entre variables numéricas",
                             color_continuous_scale="Blues")
        show_fig(fig_corr)

    st.markdown("##### Flujos (Sankey)")
    cols_sankey = [c for c in ["entidad_remitente","entidad_bancaria","estado_embargo"] if col_exists(df_filt, c)]
    if len(cols_sankey) >= 2:
        df_sk = df_filt
        if len(df_sk) > HEAVY_LIMIT:
            df_sk = df_sk.sample(n=min(SAMPLE_FOR_HEAVY, len(df_sk)), random_state=sample_seed)
            st.info(f"Sankey usando muestra de {len(df_sk):,} filas por tamaño.")
        fig_sk = sankey_from_cols(df_sk, cols_sankey, min_count=1)
        if fig_sk:
            show_fig(fig_sk)
        else:
            st.info("No fue posible construir el Sankey con los datos filtrados.")
    else:
        st.info("Se requieren al menos dos columnas categóricas para el Sankey (p.ej., remitente → banco).")

    st.markdown("##### Calidad de datos")
    nulls = df_filt.isna().mean().sort_values(ascending=False)
    if not nulls.empty:
        df_nulls = nulls.reset_index()
        df_nulls.columns = ["columna","proporcion_nulos"]
        fig_nulls = px.bar(df_nulls, x="columna", y="proporcion_nulos",
                           title="Proporción de nulos por columna",
                           labels={"proporcion_nulos":"Proporción"},
                           color_discrete_sequence=[UNICAUCA_RED])
        fig_nulls.update_xaxes(tickangle=45)
        show_fig(fig_nulls)

    keys = [c for c in ["referencia","identificacion","cuenta"] if col_exists(df_filt, c)]
    if keys:
        dup_mask = df_filt.duplicated(subset=keys, keep=False)
        n_dups = int(dup_mask.sum())
        st.markdown(f"**Posibles duplicados** (por {', '.join(keys)}): **{n_dups}**")
        if n_dups > 0:
            st.dataframe(to_streamlit_safe(df_filt[dup_mask].head(100)), use_container_width=True)

    if col_exists(df_filt, "dias_tramite"):
        neg = df_filt[df_filt["dias_tramite"] < 0]
        st.markdown(f"Diligencias con **días negativos**: **{len(neg)}**")
        if not neg.empty:
            st.dataframe(to_streamlit_safe(neg.head(50)), use_container_width=True)

st.markdown("---")
st.caption("• Desarrollado por Faber Ospina.")
