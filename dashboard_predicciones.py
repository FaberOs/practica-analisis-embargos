# -*- coding: utf-8 -*-
"""
Predicción & Evaluación (modelos .pkl) — con Escenarios por Ciudad/Segmento + Simulador de Clasificadores

Novedades HCI
- Pestaña 🔮 Escenarios (what-if): elige ciudad/segmento y observa cómo cambian las predicciones.
- Dos métodos: (A) Escalar por participación histórica (media móvil 3M) y (B) Inferencia directa sobre el subset.
- “Shock” (%) para probar escenarios de crecimiento/caída.
- Simulador de clasificadores: cambias features y ves la distribución de probabilidades.
- Smart-filters (buscar/pegar masivo) para columnas enormes.
- Plotly con use_container_width=True y mensajes claros.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import json
import re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import joblib
from sklearn.metrics import classification_report, confusion_matrix

# ==============================
# 0) UI (Marca Unicauca)
# ==============================
UNICAUCA_BLUE = "#001282"
UNICAUCA_RED  = "#AD0000"
BG_SOFT       = "#F5F7FA"
BORDER_SOFT   = "#E6EAF0"

st.set_page_config(
    page_title="Predicciones y Métricas — PKL",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📘",
)

st.markdown(f"""
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@700&family=Open+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{ --azul:{UNICAUCA_BLUE}; --rojo:{UNICAUCA_RED}; --bgsoft:{BG_SOFT}; --bsoft:{BORDER_SOFT}; }}
html, body, [class^="css"] {{ font-family:'Open Sans',system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }}
h1,h2,h3,h4 {{ font-family:'EB Garamond',serif; color:var(--azul); }}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 {{ color:var(--azul); }}
.stButton>button, .st-download-button>button {{
  background:var(--azul); color:#fff; border:0; border-radius:10px; padding:.6rem 1rem;
}}
.stButton>button:hover, .st-download-button>button:hover {{ filter:brightness(1.05); }}
.metric-card {{
  background:var(--bgsoft); border:1px solid var(--bsoft); border-radius:12px; padding:12px 14px; margin-bottom:8px;
}}
.small-note {{ color:#5b6270; font-size:.9rem; }}
.badge {{
  display:inline-block; padding:.2rem .5rem; border-radius:.5rem; border:1px solid var(--bsoft);
  background:#fff; font-size:.8rem; color:#334; margin-left:.3rem;
}}
.help-note {{ color:#6a7280; font-size:.85rem; margin-top:-6px; }}
hr.soft {{ border:none; border-top:1px solid var(--bsoft); margin:8px 0 4px; }}
</style>
""", unsafe_allow_html=True)

st.title("🔎 Predicciones y Métricas — Oficios Bancarios (modelos PKL)")
st.caption("Incluye escenarios por ciudad/segmento y simulador de clasificadores. Los .pkl son la única fuente de inferencia.")

# ==============================
# 1) Paths, helpers y ayudas (tooltips “?”)
# ==============================
MODELS_DIR = Path("modelos_pkl")
META_JSON  = MODELS_DIR / "metadata_modelos.json"

HELPS: Dict[str, str] = {
    "csv_base_path": (
        "Ruta del CSV base usado para construir features.\n"
        "Debe contener columnas como fecha_banco, ciudad, entidad_remitente, tipo/estado_embargo, etc.\n"
        "• Apunta a *_full.csv para máxima historia (mejores lags/MA).\n"
        "• *_sample.csv acelera, pero reduce historia y puede afectar precisión."
    ),
    "sample_n": (
        "Máximo de filas a leer del CSV. 0 = todas.\n"
        "Útil para pruebas rápidas. Nota: menos historia ⇒ lags/MA más cortos."
    ),
    "seed": (
        "Semilla aleatoria para muestreos y operaciones determinísticas.\n"
        "Cambiarla puede variar los subconjuntos elegidos."
    ),
    "limitar_rango": (
        "Si está activo, solo se usan registros cuya fecha_banco caiga en el rango elegido (abajo).\n"
        "Esto modifica lags/medias móviles y, por tanto, las predicciones."
    ),
    "rango_temporal": (
        "Intervalo aplicado sobre fecha_banco.\n"
        "Afecta cuántos meses tiene el modelo para calcular lags/MA.\n"
        "Rangos muy cortos pueden dejar meses sin predicción (NaN por falta de lags)."
    ),
    "metodo": (
        "Cómo generamos la predicción del segmento seleccionado:\n"
        "A) Escalar por participación histórica (MA3)\n"
        "   pred_seg_t = pred_total_t × MA3( real_seg_t / real_total_t )\n"
        "   ✔ Estable con pocos datos del segmento.\n"
        "   ✖ Asume que la participación reciente se mantiene.\n"
        "B) Inferencia directa sobre subset (aprox)\n"
        "   Reagregamos SOLO el segmento y ejecutamos el mismo .pkl.\n"
        "   ✔ Capta señales propias del segmento.\n"
        "   ✖ Si hay pocos meses, faltan lags ⇒ NaN.\n"
        "Sugerencia: usa (A) salvo que tengas ≥12 meses sólidos para el segmento."
    ),
    "shock": (
        "Multiplicador a la predicción del segmento.\n"
        "Ej.: +10% ⇒ pred_shock = pred × 1.10; −20% ⇒ pred × 0.80.\n"
        "Sirve para stress testing o metas de gestión."
    ),
    "smart_filter_generic": (
        "Selector para columnas largas:\n"
        "• “Buscar…” filtra por texto que contenga.\n"
        "• “Pega valores” acepta lista separada por comas o saltos de línea.\n"
        "• “Top por frecuencia” muestra los valores más comunes.\n"
        "• “Coincidencias” cambia a un listado filtrado por tu búsqueda/pegado.\n"
        "Deja vacío para NO filtrar por esa columna."
    ),
    "smart_filter_mode": (
        "Top por frecuencia: lista los valores más comunes (rápido y útil para empezar).\n"
        "Coincidencias: lista filtrada por el término de búsqueda y/o los valores pegados."
    ),
    "smart_filter_pick": (
        "Valores elegidos para filtrar. Si lo dejas vacío, NO filtra por esta columna."
    ),
    "tipo_embargo": (
        "Filtra el segmento por tipo de embargo. Si lo dejas vacío, se incluyen todos los tipos."
    ),
    "estado_embargo": (
        "Filtra el segmento por estado del embargo. Si lo dejas vacío, se incluyen todos los estados."
    ),
    "sel_clfs": (
        "Elige qué clasificadores evaluar. La evaluación usa el dataset cargado (tras filtros de la barra lateral)\n"
        "y compara predicción vs etiqueta real del CSV base."
    ),
    "simulador": (
        "Construye una fila sintética con las features del modelo y calcula predict_proba (si el estimador lo soporta).\n"
        "Campos *_enc: selecciona el valor legible; se codifica automáticamente con el encoder de entrenamiento."
    ),
    "proba_top": (
        "Cantidad de clases con mayor probabilidad a mostrar en la gráfica. Solo afecta la visualización."
    ),
    "mes_num": (
        "Mes numérico (1=enero,…,12=diciembre) usado como feature en algunos clasificadores.\n"
        "No cambia los regresores de series; afecta únicamente el simulador."
    ),
    "montoaembargar": (
        "Monto en pesos. Se sugiere la mediana del dataset como punto de partida.\n"
        "Puedes ajustar en pasos de 1.000."
    ),
    "es_cliente_bin": (
        "1 si corresponde a cliente (SI/TRUE/CLIENTE/1), 0 en otro caso. Se deriva de 'es_cliente' del CSV."
    ),
}

def show_fig(fig):
    st.plotly_chart(
        fig,
        config={"displaylogo": False, "responsive": True, "scrollZoom": True, "doubleClick": "reset"},
        use_container_width=True,
    )

@st.cache_data(show_spinner=False, ttl=60)
def _load_meta() -> Dict:
    if META_JSON.exists():
        return json.loads(META_JSON.read_text(encoding="utf-8"))
    return {"csv_origen": "embargos_consolidado_mensual_full.csv", "modelos": {}, "encoders": {}, "features": {}}

def _safe_ts(s: pd.Series) -> pd.Series:
    x = pd.to_datetime(s, errors="coerce", utc=True)
    try:
        x = x.dt.tz_convert(None)
    except Exception:
        x = x.dt.tz_localize(None) if hasattr(x.dt, "tz_localize") else x
    return x

def _normalize_cats(df: pd.DataFrame, cols: List[str], fill="OTRO") -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = df[c].fillna(fill).astype(str).str.strip().str.upper()
        else:
            df[c] = fill
    return df

def _ym_to_timestamp(year_series: pd.Series, month_series: pd.Series) -> pd.Series:
    return pd.to_datetime({"year": year_series.astype(int), "month": month_series.astype(int), "day": 1}, errors="coerce")

# ==============================
# 2) Carga base + normalización
# ==============================
def _cargar_base(csv_origen: str, sample_n: Optional[int]=None, seed: int=42) -> pd.DataFrame:
    df = pd.read_csv(csv_origen, encoding="utf-8", low_memory=False)
    if sample_n and len(df) > sample_n:
        df = df.sample(sample_n, random_state=seed).reset_index(drop=True)

    df["montoaembargar"] = pd.to_numeric(df.get("montoaembargar", 0), errors="coerce").fillna(0.0)

    fb = _safe_ts(df.get("fecha_banco", pd.NaT))
    df["año"] = pd.to_numeric(fb.dt.year, errors="coerce")
    df["mes_num"] = pd.to_numeric(fb.dt.month, errors="coerce")
    df = df.dropna(subset=["año","mes_num"]).copy()
    df["año"] = df["año"].astype(int); df["mes_num"] = df["mes_num"].astype(int)

    df = _normalize_cats(df, ['ciudad','entidad_remitente','entidad_bancaria','tipo_embargo','estado_embargo'])

    df["mes_sin"] = np.sin(2*np.pi*df["mes_num"]/12.0)
    df["mes_cos"] = np.cos(2*np.pi*df["mes_num"]/12.0)
    s = pd.Series(df.get("es_cliente", 0)).astype(str).str.upper().str.strip()
    df["es_cliente_bin"] = s.isin({"1","SI","SÍ","TRUE","YES","CLIENTE","Y","SI_ES_CLIENTE"}).astype(int)
    if 'id' not in df.columns: df['id'] = 0
    if 'identificacion' not in df.columns: df['identificacion'] = ""
    return df

def _agg_mensual(df_base: pd.DataFrame) -> pd.DataFrame:
    g = (
        df_base.groupby(['año','mes_num'])
               .agg(id=('id','count'),
                    identificacion=('identificacion', pd.Series.nunique),
                    montoaembargar=('montoaembargar','sum'))
               .reset_index()
               .sort_values(['año','mes_num'])
               .copy()
    )
    g['mes_sin'] = np.sin(2*np.pi*g['mes_num']/12.0)
    g['mes_cos'] = np.cos(2*np.pi*g['mes_num']/12.0)
    for base, pref in [('id','oficios'), ('identificacion','demandados')]:
        g[f"{pref}_lag1"] = g[base].shift(1)
        g[f"{pref}_lag2"] = g[base].shift(2)
        g[f"{pref}_lag3"] = g[base].shift(3)
        g[f"{pref}_ma3"]  = g[base].rolling(3).mean().shift(1)
    g["mes"] = _ym_to_timestamp(g["año"], g["mes_num"])
    return g

# ==============================
# 3) Encoders / Features / Modelos
# ==============================
def _load_encoders(meta: Dict) -> Dict[str, object]:
    enc = {}
    for key, fname in meta.get("encoders", {}).items():
        p = MODELS_DIR / fname
        if p.exists():
            enc[key] = joblib.load(p)
    return enc

def _safe_transform(le, series: pd.Series, unknown_token="OTRO") -> np.ndarray:
    s = series.astype(str).str.upper().fillna(unknown_token)
    classes = set([str(x).upper() for x in getattr(le, "classes_", [])])
    if unknown_token not in classes and len(classes) > 0:
        default = list(classes)[0]
        s = s.map(lambda x: x if x in classes else default)
    else:
        s = s.map(lambda x: x if x in classes else unknown_token)
    return le.transform(s)

def _ensure_encoded_columns(df_raw: pd.DataFrame, encoders: Dict[str, object]) -> pd.DataFrame:
    df = df_raw.copy()
    if "ciudad_enc" not in df.columns and "ciudad" in df.columns and "ciudad" in encoders:
        df["ciudad_enc"] = _safe_transform(encoders["ciudad"], df["ciudad"])
    if "entidad_remitente_enc" not in df.columns and "entidad_remitente" in df.columns and "entidad_remitente" in encoders:
        df["entidad_remitente_enc"] = _safe_transform(encoders["entidad_remitente"], df["entidad_remitente"])
    if "tipo_embargo_enc" not in df.columns and "tipo_embargo" in df.columns and "tipo_embargo" in encoders:
        df["tipo_embargo_enc"] = _safe_transform(encoders["tipo_embargo"], df["tipo_embargo"])
    if "estado_embargo_enc" not in df.columns and "estado_embargo" in df.columns and "estado_embargo" in encoders:
        df["estado_embargo_enc"] = _safe_transform(encoders["estado_embargo"], df["estado_embargo"])

    if "montoaembargar" not in df.columns:
        df["montoaembargar"] = 0.0
    if "es_cliente_bin" not in df.columns:
        raw = df.get("es_cliente", 0)
        s = pd.Series(raw).astype(str).str.upper().str.strip()
        df["es_cliente_bin"] = s.isin({"1","SI","SÍ","TRUE","YES","CLIENTE","Y","SI_ES_CLIENTE"}).astype(int)

    if "mes_num" not in df.columns or "año" not in df.columns:
        fb = _safe_ts(df.get("fecha_banco", pd.NaT))
        df["año"] = pd.to_numeric(fb.dt.year, errors="coerce")
        df["mes_num"] = pd.to_numeric(fb.dt.month, errors="coerce")
    df = df.dropna(subset=["año","mes_num"]).copy()
    df["año"] = df["año"].astype(int); df["mes_num"] = df["mes_num"].astype(int)
    df["mes_sin"] = np.sin(2*np.pi*df["mes_num"]/12.0)
    df["mes_cos"] = np.cos(2*np.pi*df["mes_num"]/12.0)
    return df

# ==============================
# 4) Smart-filters (buscar/pegar) con ayudas
# ==============================
def normalize_tokens(raw: str) -> list:
    if not raw:
        return []
    parts = re.split(r"[,\n;]+", str(raw))
    return [p.strip() for p in parts if p.strip()]

@st.cache_data(show_spinner=False, ttl=300)
def uniques_with_freq(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col not in df.columns:
        return pd.DataFrame(columns=["valor","conteo"])
    vc = (df[col].fillna("OTRO").astype(str).value_counts(dropna=False)
          .rename_axis("valor").reset_index(name="conteo"))
    return vc

def smart_filter(df: pd.DataFrame, col: str, label: str, key: str, base_help: Optional[str]=None, max_show=400, top_default=30):
    if col not in df.columns:
        return None
    with st.expander(label, expanded=False):
        vc = uniques_with_freq(df, col); total_uni = int(vc.shape[0])
        q = st.text_input("Buscar…", value="", key=f"{key}_q", help=base_help or HELPS["smart_filter_generic"]).strip().upper()
        bulk = st.text_area("Pega valores (coma/una por línea)", value="", key=f"{key}_bulk",
                            help=base_help or HELPS["smart_filter_generic"])
        tokens = [t.upper() for t in normalize_tokens(bulk)]
        mode = st.radio("Fuente de opciones", [f"Top {top_default} por frecuencia", "Coincidencias"],
                        index=0, horizontal=True, key=f"{key}_mode", help=HELPS["smart_filter_mode"])
        if mode.startswith("Top"):
            opts = vc.head(top_default)["valor"].astype(str).tolist()
            st.markdown(f"<div class='help-note'>Mostrando {top_default} de {total_uni} únicos.</div>", unsafe_allow_html=True)
        else:
            cand = vc["valor"].astype(str).tolist()
            if q: cand = [x for x in cand if q in x.upper()]
            if tokens:
                extra = [x for x in vc["valor"].astype(str).tolist() if any(t in x.upper() for t in tokens)]
                seen = set(); cand = [x for x in cand + extra if not (x in seen or seen.add(x))]
            if len(cand) > max_show:
                cand = cand[:max_show]
                st.markdown(f"<div class='help-note'>Se muestran {max_show} coincidencias (de {total_uni}). Afina la búsqueda.</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='help-note'>Coincidencias: {len(cand)}.</div>", unsafe_allow_html=True)
            opts = cand
        sel = st.multiselect("Selecciona (opcional)", options=opts, default=[], key=f"{key}_sel", help=HELPS["smart_filter_pick"])
        return sel if sel else None

# ==============================
# 5) Sidebar — Controles base (con tooltips claros)
# ==============================
meta = _load_meta()
csv_origen_default = meta.get("csv_origen", "embargos_consolidado_mensual_full.csv")

with st.sidebar:
    st.header("⚙️ Controles")
    with st.form("form_base"):
        colA, colB = st.columns([2,1])
        csv_base_path = colA.text_input("Ruta del CSV base", value=csv_origen_default, help=HELPS["csv_base_path"])
        sample_n = colB.number_input("Muestra (filas)", min_value=0, value=0, help=HELPS["sample_n"])
        seed = colB.number_input("Semilla", min_value=0, value=42, help=HELPS["seed"])
        limitar_rango = st.checkbox("Filtrar rango temporal", value=True, help=HELPS["limitar_rango"])
        submitted = st.form_submit_button("Aplicar / recargar")

# Carga base
try:
    df_base = _cargar_base(csv_base_path, sample_n=int(sample_n) if sample_n else None, seed=int(seed))
except Exception as e:
    st.error(f"No pude leer el CSV base: {e}")
    st.stop()

# Rango temporal
if limitar_rango and not df_base.empty:
    rango_min = _ym_to_timestamp(df_base["año"], df_base["mes_num"]).min()
    rango_max = _ym_to_timestamp(df_base["año"], df_base["mes_num"]).max()
    dr = st.sidebar.date_input("Rango temporal", (rango_min.date(), rango_max.date()), help=HELPS["rango_temporal"])
    if isinstance(dr, tuple) and len(dr) == 2:
        i0, i1 = pd.to_datetime(dr[0]), pd.to_datetime(dr[1])
        df_base["_mes"] = _ym_to_timestamp(df_base["año"], df_base["mes_num"])
        df_base = df_base[(df_base["_mes"] >= i0) & (df_base["_mes"] <= i1)].drop(columns=["_mes"], errors="ignore")

if df_base.empty:
    st.warning("No hay filas tras filtros de base.")
    st.stop()

# Preparación común
agg_total = _agg_mensual(df_base)
encoders  = _load_encoders(meta)
df_cls    = _ensure_encoded_columns(df_base, encoders)
modelos   = meta.get("modelos", {})
feats_map = meta.get("features", {})

# ==============================
# 6) Inferencia — Regresión
# ==============================
def _predecir_oficios(agg: pd.DataFrame, model_path: Path) -> pd.DataFrame:
    feats = ['año','mes_num','mes_sin','mes_cos','oficios_lag1','oficios_lag2','oficios_lag3','oficios_ma3']
    if not model_path or not model_path.exists():
        return pd.DataFrame()
    model = joblib.load(model_path)
    df_te = agg.dropna(subset=feats).copy()
    if df_te.empty:
        return pd.DataFrame()
    yhat = model.predict(df_te[feats])
    out = df_te[['mes','id']].copy().rename(columns={'id':'real_oficios'})
    out['pred_oficios'] = yhat
    return out

def _predecir_demandados(agg: pd.DataFrame, model_path: Path) -> pd.DataFrame:
    feats = ['año','mes_num','mes_sin','mes_cos','demandados_lag1','demandados_lag2','demandados_ma3']
    if not model_path or not model_path.exists():
        return pd.DataFrame()
    model = joblib.load(model_path)
    df_te = agg.dropna(subset=feats).copy()
    if df_te.empty:
        return pd.DataFrame()
    yhat = model.predict(df_te[feats])
    out = df_te[['mes','identificacion']].copy().rename(columns={'identificacion':'real_demandados'})
    out['pred_demandados'] = yhat
    return out

p_reg_ofi = MODELS_DIR / modelos.get("reg_oficios", "reg_oficios_xgb_poisson.pkl") if modelos else None
p_reg_dem = MODELS_DIR / modelos.get("reg_demandados", "reg_demandados_xgb_poisson.pkl") if modelos else None

df_pred_total_ofi = _predecir_oficios(agg_total, p_reg_ofi)
df_pred_total_dem = _predecir_demandados(agg_total, p_reg_dem)

# ==============================
# 7) Tabs
# ==============================
tab0, tab1, tab2, tab3 = st.tabs([
    "🔮 Escenarios (what-if)",
    "📅 Oficios (regresión)",
    "📅 Demandados (regresión)",
    "📊 Clasificadores (PKL)"
])

# ==============================
# 🔮 TAB 0 — Escenarios por segmento
# ==============================
with tab0:
    st.header("🔮 Escenarios por ciudad/segmento")
    st.caption("Elige un segmento y ve cómo cambian las predicciones. Método recomendado: Escalar por participación histórica (MA3).")

    with st.form("escenario_form"):
        c1, c2 = st.columns(2)
        metodo = c1.radio(
            "Método de predicción por segmento",
            options=["Escalar por participación histórica (MA3)", "Inferencia directa sobre subset (aprox)"],
            index=0,
            help=HELPS["metodo"]
        )
        shock = c2.slider("Shock al resultado (%)", min_value=-50, max_value=50, value=0, step=5,
                          help=HELPS["shock"])

        st.markdown("**Filtros del segmento** (puedes usar uno o varios):")
        seg_ciudades  = smart_filter(df_base, "ciudad", "Ciudad (smart-filter)", key="sf_city", base_help=HELPS["smart_filter_generic"])
        with st.expander("Más filtros (opcionales)", expanded=False):
            seg_bancos    = smart_filter(df_base, "entidad_bancaria", "Banco (smart-filter)", key="sf_bank", base_help=HELPS["smart_filter_generic"])
            seg_remitente = smart_filter(df_base, "entidad_remitente", "Entidad remitente (smart-filter)", key="sf_rem", base_help=HELPS["smart_filter_generic"])
            # rápidos
            colr1, colr2 = st.columns(2)
            tipo_opts = sorted(df_base["tipo_embargo"].dropna().astype(str).unique().tolist())
            estado_opts = sorted(df_base["estado_embargo"].dropna().astype(str).unique().tolist())
            seg_tipo   = colr1.multiselect("Tipo de embargo", tipo_opts, default=[], help=HELPS["tipo_embargo"])
            seg_estado = colr2.multiselect("Estado embargo", estado_opts, default=[], help=HELPS["estado_embargo"])

        aplicar = st.form_submit_button("Aplicar escenario")

    # Construir máscara de segmento
    def _mask_segmento(df: pd.DataFrame) -> pd.Series:
        m = pd.Series(True, index=df.index)
        if seg_ciudades:  m &= df["ciudad"].astype(str).isin(seg_ciudades)
        if seg_bancos:    m &= df["entidad_bancaria"].astype(str).isin(seg_bancos)
        if seg_remitente: m &= df["entidad_remitente"].astype(str).isin(seg_remitente)
        if seg_tipo:      m &= df["tipo_embargo"].astype(str).isin(seg_tipo)
        if seg_estado:    m &= df["estado_embargo"].astype(str).isin(seg_estado)
        return m

    seg_mask = _mask_segmento(df_base)
    df_seg = df_base[seg_mask].copy()

    if df_seg.empty:
        st.info("No hay filas para el segmento actual. Ajusta los filtros.")
    else:
        agg_seg = _agg_mensual(df_seg)

        # 7.1 Oficios — escenario
        st.subheader("Oficios — Escenario del segmento")
        if df_pred_total_ofi.empty:
            st.warning("No hay modelo de oficios disponible o no se pudo inferir en total.")
        else:
            df_merge = df_pred_total_ofi.merge(
                agg_total[["mes","id"]].rename(columns={"id":"real_total"}),
                on="mes", how="left"
            ).merge(
                agg_seg[["mes","id"]].rename(columns={"id":"real_seg"}),
                on="mes", how="left"
            )

            # share histórico (MA3)
            df_merge["share_seg"] = (df_merge["real_seg"] / df_merge["real_total"]).replace([np.inf,-np.inf], np.nan)
            df_merge["share_seg_ma3"] = df_merge["share_seg"].rolling(3, min_periods=1).mean()

            # Método A: escala por share
            df_merge["pred_seg_A"] = df_merge["pred_oficios"] * df_merge["share_seg_ma3"]

            # Método B: inferencia directa sobre subset
            if metodo.endswith("subset (aprox)"):
                pred_seg_B = _predecir_oficios(agg_seg, p_reg_ofi) if p_reg_ofi else pd.DataFrame()
                if not pred_seg_B.empty:
                    df_merge = df_merge.merge(pred_seg_B[["mes","pred_oficios"]].rename(columns={"pred_oficios":"pred_seg_B"}),
                                              on="mes", how="left")
                else:
                    df_merge["pred_seg_B"] = np.nan
            else:
                df_merge["pred_seg_B"] = np.nan

            # Elegir método activo
            metodo_activo_col = "pred_seg_A" if metodo.startswith("Escalar") else "pred_seg_B"
            df_merge["pred_seg"] = df_merge[metodo_activo_col]

            # Shock %
            df_merge["pred_seg_shock"] = df_merge["pred_seg"] * (1.0 + shock/100.0)

            # Métricas rápidas (cuando hay real_seg)
            dfm = df_merge.dropna(subset=["pred_seg_shock"])
            dfm["residuo"] = dfm["real_seg"] - dfm["pred_seg_shock"]
            dfm["ae"] = dfm["residuo"].abs()
            dfm["mape"] = np.where(dfm["real_seg"]!=0, 100*np.abs(dfm["residuo"])/np.abs(dfm["real_seg"]), np.nan)

            k1, k2, k3 = st.columns(3)
            k1.markdown(f'<div class="metric-card"><b>MAE:</b> {dfm["ae"].mean():,.2f}</div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="metric-card"><b>RMSE:</b> {np.sqrt(np.mean(dfm["residuo"]**2)):,.2f}</div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="metric-card"><b>MAPE (%):</b> {dfm["mape"].mean():,.2f}</div>', unsafe_allow_html=True)

            # Gráfico
            plot_df = df_merge[["mes","real_seg","pred_seg_shock"]].rename(
                columns={"real_seg":"Real segmento", "pred_seg_shock":"Pred segmento"}
            ).dropna(subset=["mes"])
            fig = px.line(plot_df, x="mes", y=["Real segmento","Pred segmento"], markers=True,
                          labels={"value":"Oficios","variable":"Serie","mes":"Mes"},
                          title=f"Oficios — Segmento vs Pred ({'MA3' if metodo.startswith('Escalar') else 'Subset'})")
            fig.update_traces(line=dict(width=3)); fig.update_layout(legend_title_text="")
            show_fig(fig)

        st.markdown("---")

        # 7.2 Demandados — escenario
        st.subheader("Demandados únicos — Escenario del segmento")
        if df_pred_total_dem.empty:
            st.warning("No hay modelo de demandados disponible o no se pudo inferir en total.")
        else:
            dfm2 = df_pred_total_dem.merge(
                agg_total[["mes","identificacion"]].rename(columns={"identificacion":"real_total"}),
                on="mes", how="left"
            ).merge(
                agg_seg[["mes","identificacion"]].rename(columns={"identificacion":"real_seg"}),
                on="mes", how="left"
            )
            dfm2["share_seg"] = (dfm2["real_seg"] / dfm2["real_total"]).replace([np.inf,-np.inf], np.nan)
            dfm2["share_seg_ma3"] = dfm2["share_seg"].rolling(3, min_periods=1).mean()
            dfm2["pred_seg_A"] = dfm2["pred_demandados"] * dfm2["share_seg_ma3"]

            if metodo.endswith("subset (aprox)"):
                pred_seg_B2 = _predecir_demandados(agg_seg, p_reg_dem) if p_reg_dem else pd.DataFrame()
                if not pred_seg_B2.empty:
                    dfm2 = dfm2.merge(pred_seg_B2[["mes","pred_demandados"]].rename(columns={"pred_demandados":"pred_seg_B"}),
                                      on="mes", how="left")
                else:
                    dfm2["pred_seg_B"] = np.nan
            else:
                dfm2["pred_seg_B"] = np.nan

            metodo_activo_col2 = "pred_seg_A" if metodo.startswith("Escalar") else "pred_seg_B"
            dfm2["pred_seg"] = dfm2[metodo_activo_col2]
            dfm2["pred_seg_shock"] = dfm2["pred_seg"] * (1.0 + shock/100.0)

            plot_df2 = dfm2[["mes","real_seg","pred_seg_shock"]].rename(
                columns={"real_seg":"Real segmento", "pred_seg_shock":"Pred segmento"}
            ).dropna(subset=["mes"])
            fig2 = px.line(plot_df2, x="mes", y=["Real segmento","Pred segmento"], markers=True,
                           labels={"value":"Demandados","variable":"Serie","mes":"Mes"},
                           title=f"Demandados — Segmento vs Pred ({'MA3' if metodo.startswith('Escalar') else 'Subset'})")
            fig2.update_traces(line=dict(width=3)); fig2.update_layout(legend_title_text="")
            show_fig(fig2)

# ==============================
# 📅 TAB 1 — Oficios (global)
# ==============================
with tab1:
    st.header("📅 Oficios por mes — Real vs Pred (global)")
    mdl = modelos.get("reg_oficios", "reg_oficios_xgb_poisson.pkl")
    p = MODELS_DIR / mdl
    if not p.exists():
        st.info(f"No encuentro el modelo de oficios: `{mdl}` en `{MODELS_DIR}`.")
    else:
        df_ofi = df_pred_total_ofi.copy()
        if df_ofi.empty:
            st.warning("No se pudo inferir oficios (faltan lags o datos insuficientes).")
        else:
            df_ofi["residuo"] = df_ofi["real_oficios"] - df_ofi["pred_oficios"]
            df_ofi["ae"] = df_ofi["residuo"].abs()
            df_ofi["mape"] = np.where(
                df_ofi["real_oficios"]!=0, 100*np.abs(df_ofi["residuo"])/np.abs(df_ofi["real_oficios"]), np.nan
            )
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><b>MAE:</b> {df_ofi["ae"].mean():,.2f}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><b>RMSE:</b> {np.sqrt(np.mean(df_ofi["residuo"]**2)):,.2f}</div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><b>MAPE (%):</b> {df_ofi["mape"].mean():,.2f}</div>', unsafe_allow_html=True)

            fig1 = px.line(df_ofi, x="mes", y=["real_oficios","pred_oficios"], markers=True,
                           labels={"value":"Oficios","variable":"Serie","mes":"Mes"},
                           title="Oficios — Real vs Pred (global)",
                           color_discrete_map={"real_oficios":UNICAUCA_BLUE, "pred_oficios":UNICAUCA_RED})
            fig1.update_traces(line=dict(width=3)); fig1.update_layout(legend_title_text="")
            show_fig(fig1)

            fig3 = px.bar(df_ofi, x="mes", y="residuo",
                          title="Residuales (Real − Pred)", labels={"residuo":"Residuo","mes":"Mes"},
                          color_discrete_sequence=[UNICAUCA_RED])
            show_fig(fig3)

            st.download_button("⬇️ Descargar oficios_pred.csv",
                               df_ofi.to_csv(index=False).encode("utf-8"),
                               file_name="oficios_pred.csv", mime="text/csv")

# ==============================
# 📅 TAB 2 — Demandados (global)
# ==============================
with tab2:
    st.header("📅 Demandados únicos — Real vs Pred (global)")
    mdl = modelos.get("reg_demandados", "reg_demandados_xgb_poisson.pkl")
    p = MODELS_DIR / mdl
    if not p.exists():
        st.info(f"No encuentro el modelo de demandados: `{mdl}` en `{MODELS_DIR}`.")
    else:
        df_dem = df_pred_total_dem.copy()
        if df_dem.empty:
            st.warning("No se pudo inferir demandados (faltan lags o datos insuficientes).")
        else:
            df_dem["residuo"] = df_dem["real_demandados"] - df_dem["pred_demandados"]
            df_dem["ae"] = df_dem["residuo"].abs()
            df_dem["mape"] = np.where(
                df_dem["real_demandados"]!=0, 100*np.abs(df_dem["residuo"])/np.abs(df_dem["real_demandados"]), np.nan
            )
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="metric-card"><b>MAE:</b> {df_dem["ae"].mean():,.2f}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-card"><b>RMSE:</b> {np.sqrt(np.mean(df_dem["residuo"]**2)):,.2f}</div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="metric-card"><b>MAPE (%):</b> {df_dem["mape"].mean():,.2f}</div>', unsafe_allow_html=True)

            fig1 = px.line(df_dem, x="mes", y=["real_demandados","pred_demandados"], markers=True,
                           labels={"value":"Demandados","variable":"Serie","mes":"Mes"},
                           title="Demandados — Real vs Pred (global)",
                           color_discrete_map={"real_demandados":UNICAUCA_BLUE, "pred_demandados":UNICAUCA_RED})
            fig1.update_traces(line=dict(width=3)); fig1.update_layout(legend_title_text="")
            show_fig(fig1)

            fig3 = px.bar(df_dem, x="mes", y="residuo",
                          title="Residuales (Real − Pred)", labels={"residuo":"Residuo","mes":"Mes"},
                          color_discrete_sequence=[UNICAUCA_RED])
            show_fig(fig3)

            st.download_button("⬇️ Descargar demandados_pred.csv",
                               df_dem.to_csv(index=False).encode("utf-8"),
                               file_name="demandados_pred.csv", mime="text/csv")

# ==============================
# 📊 TAB 3 — Clasificadores (simulador + métricas)
# ==============================
with tab3:
    st.header("📊 Clasificadores (desde .pkl)")

    # Selección de clasificadores
    all_clfs = [k for k in modelos.keys() if k.startswith("clf_")]
    if not all_clfs:
        st.info("No hay clasificadores declarados en metadata.")
    else:
        sel_clfs = st.multiselect("Elige clasificadores a evaluar", all_clfs, default=all_clfs, help=HELPS["sel_clfs"])

    # === Simulador (what-if de una fila) ===
    st.subheader("🧪 Simulador de clasificación (cambia features y mira predict_proba)")
    with st.expander("Abrir simulador", expanded=False):
        colA, colB = st.columns([2,1])
        clf_key = colA.selectbox("Clasificador", sel_clfs if all_clfs else [], index=0 if sel_clfs else 0, help=HELPS["simulador"])
        proba_top = colB.slider("Top clases a mostrar", min_value=3, max_value=15, value=8, help=HELPS["proba_top"])
        if clf_key:
            feats = feats_map.get(clf_key, [])
            mdl_path = MODELS_DIR / modelos.get(clf_key, "")
            if mdl_path.exists() and feats:
                model = joblib.load(mdl_path)
                # Construir un input row con UI
                inputs = {}
                for f in feats:
                    if f.endswith("_enc"):
                        base = f.replace("_enc","")
                        opts = sorted(df_base[base].dropna().astype(str).unique().tolist())
                        sel = st.selectbox(f"{base}", opts[:1000], index=0 if opts else 0,
                                           help="Selecciona el valor legible; se codifica automáticamente con el encoder del entrenamiento.")
                        enc = encoders.get(base)
                        val_enc = int(_safe_transform(enc, pd.Series([sel]))[0]) if enc is not None else 0
                        inputs[f] = val_enc
                    elif f == "mes_num":
                        inputs[f] = st.slider("mes_num", 1, 12, 6, help=HELPS["mes_num"])
                    elif f == "montoaembargar":
                        default = float(np.nanmedian(df_base["montoaembargar"]))
                        inputs[f] = st.number_input("montoaembargar", value=round(default,2), min_value=0.0, step=1000.0, help=HELPS["montoaembargar"])
                    elif f == "es_cliente_bin":
                        inputs[f] = 1 if st.checkbox("¿Es cliente?", value=True, help=HELPS["es_cliente_bin"]) else 0
                    else:
                        inputs[f] = st.number_input(f, value=float(df_cls[f].median()) if f in df_cls.columns else 0.0,
                                                    help="Feature numérica usada por el modelo. Ajusta si quieres forzar un escenario.")

                X_one = pd.DataFrame([inputs], columns=feats)
                try:
                    if hasattr(model, "predict_proba"):
                        probs = model.predict_proba(X_one)[0]
                        # mapear clases a texto si hay encoder de destino
                        classes_idx = np.arange(len(probs))
                        try:
                            classes_idx = getattr(model, "classes_", classes_idx)
                        except Exception:
                            pass
                        label_text = None
                        for k_enc, enc in encoders.items():
                            if len(getattr(enc, "classes_", [])) == len(classes_idx):
                                try:
                                    label_text = enc.inverse_transform(classes_idx.astype(int))
                                    break
                                except Exception:
                                    continue
                        labels = label_text if label_text is not None else [str(c) for c in classes_idx]
                        dfp = pd.DataFrame({"clase": labels, "prob": probs}).sort_values("prob", ascending=False).head(proba_top)
                        figp = px.bar(dfp, x="clase", y="prob", title=f"predict_proba — {clf_key}", range_y=[0,1])
                        show_fig(figp)
                        st.dataframe(dfp, use_container_width=True)
                    else:
                        pred = model.predict(X_one)[0]
                        st.info(f"Predicción (sin proba): **{pred}**")
                except Exception as e:
                    st.error(f"No se pudo simular: {e}")

    # === Evaluación rápida (como antes) ===
    st.subheader("📈 Métricas por clasificador (dataset filtrado en sidebar)")
    def evaluar_clf(key_modelo: str, target_col: str, target_enc_key: Optional[str], nombre_legible: str):
        mdl_name = modelos.get(key_modelo)
        if not mdl_name:
            st.info(f"No hay modelo configurado para {key_modelo}."); return None
        feats = feats_map.get(key_modelo, [])
        p = MODELS_DIR / mdl_name
        if not p.exists():
            st.warning(f"{key_modelo}: falta `{p.name}`."); return None
        if target_col not in df_base.columns:
            st.warning(f"{key_modelo}: no encuentro `{target_col}` en el CSV base."); return None
        faltan = sorted(set(feats) - set(df_cls.columns))
        if faltan:
            st.warning(f"{key_modelo}: faltan features {faltan}."); return None

        model = joblib.load(p)
        X = df_cls[feats].copy(); y_true_raw = df_base[target_col].copy()
        try:
            y_pred_raw = model.predict(X)
        except Exception as e:
            st.error(f"{key_modelo}: no se pudo predecir → {e}"); return None

        def _to_upper_str(a):
            return pd.Series(a, copy=False).astype(str).str.upper().str.strip().values
        def _is_numeric(a): return np.issubdtype(np.asarray(a).dtype, np.number)

        enc = encoders.get(target_enc_key) if target_enc_key else None
        y_true_series = pd.Series(y_true_raw); y_pred_series = pd.Series(y_pred_raw)
        mask = y_true_series.notna() & y_pred_series.notna()
        y_true_series = y_true_series[mask]; y_pred_series = y_pred_series[mask]

        y_eval=y_pred_aligned=y_true_txt=y_pred_txt=None
        if enc is not None:
            try:
                y_true_enc = enc.transform(_to_upper_str(y_true_series))
                if _is_numeric(y_pred_series.values):
                    y_pred_enc = pd.Series(y_pred_series.values).astype(int).values
                else:
                    y_pred_enc = enc.transform(_to_upper_str(y_pred_series))
                y_eval = y_true_enc; y_pred_aligned = y_pred_enc
                try:
                    y_true_txt = enc.inverse_transform(y_true_enc.astype(int))
                    y_pred_txt = enc.inverse_transform(y_pred_enc.astype(int))
                except Exception:
                    y_true_txt = _to_upper_str(y_true_series); y_pred_txt = _to_upper_str(y_pred_series)
            except Exception:
                y_true_txt = _to_upper_str(y_true_series)
                if _is_numeric(y_pred_series.values):
                    try:
                        y_pred_txt = enc.inverse_transform(pd.Series(y_pred_series.values).astype(int).values)
                    except Exception:
                        y_pred_txt = _to_upper_str(y_pred_series)
                else:
                    y_pred_txt = _to_upper_str(y_pred_series)
                y_eval = y_true_txt; y_pred_aligned = y_pred_txt
        else:
            y_true_txt = _to_upper_str(y_true_series)
            y_pred_txt = _to_upper_str(y_pred_series)
            y_eval = y_true_txt; y_pred_aligned = y_pred_txt

        rep = classification_report(y_eval, y_pred_aligned, zero_division=0, output_dict=True)
        rows = [{"clase": c, "precision": m.get("precision", np.nan),
                 "recall": m.get("recall", np.nan), "f1": m.get("f1-score", np.nan)}
                for c, m in rep.items() if c not in {"accuracy","macro avg","weighted avg"}]
        dfm = pd.DataFrame(rows)

        st.markdown(
            f"Modelo: **{nombre_legible}** "
            f"<span class='badge'>{mdl_name}</span> <span class='badge'>features: {len(feats)}</span>",
            unsafe_allow_html=True
        )
        if not dfm.empty:
            figf = px.bar(dfm, x="clase", y="f1", title=f"F1 por clase — {nombre_legible}",
                          labels={"f1":"F1-score","clase":"Clase"}, color_discrete_sequence=[UNICAUCA_BLUE])
            show_fig(figf)
            st.dataframe(dfm.sort_values("f1", ascending=False), use_container_width=True)

        try:
            if y_true_txt is not None and y_pred_txt is not None:
                labels = sorted(list(set(y_true_txt) | set(y_pred_txt)))
                cm = confusion_matrix(y_true_txt, y_pred_txt, labels=labels)
            else:
                labels = sorted(list(set(y_eval) | set(y_pred_aligned)))
                cm = confusion_matrix(y_eval, y_pred_aligned, labels=labels)
            figc = px.imshow(cm, x=labels, y=labels, text_auto=True, color_continuous_scale="Blues",
                             title=f"Matriz de confusión — {nombre_legible}")
            figc.update_layout(xaxis_title="Predicho", yaxis_title="Real")
            show_fig(figc)
        except Exception:
            pass
        return dfm

    # Ejecutar evaluación para los seleccionados (targets típicos)
    target_map = {
        "clf_tipo_embargo": ("tipo_embargo", "tipo_embargo", "Tipo de embargo"),
        "clf_estado_embargo": ("estado_embargo", "estado_embargo", "Estado del embargo"),
        "clf_es_cliente": ("es_cliente_bin", None, "¿Es cliente?"),
        "clf_ciudad": ("ciudad", "ciudad", "Ciudad"),
        "clf_entidad_remitente": ("entidad_remitente", "entidad_remitente", "Entidad remitente"),
    }
    dfs_out = []
    if 'sel_clfs' in locals() and sel_clfs:
        for key_modelo in sel_clfs:
            tgt_col, enc_key, legible = target_map.get(key_modelo, (None, None, key_modelo))
            if tgt_col is None:
                st.info(f"{key_modelo}: define la columna objetivo en target_map.")
                continue
            res = evaluar_clf(key_modelo, tgt_col, enc_key, legible)
            if res is not None:
                dfs_out.append(res.assign(modelo=key_modelo))
    if dfs_out:
        df_metrics_all = pd.concat(dfs_out, ignore_index=True)
        with st.expander("⬇️ Descargar métricas consolidadas"):
            st.dataframe(df_metrics_all, use_container_width=True)
            st.download_button(
                "Descargar CSV",
                df_metrics_all.to_csv(index=False).encode("utf-8"),
                file_name="resultados_clasificaciones_desde_pkl.csv",
                mime="text/csv"
            )
