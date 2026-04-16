import base64
import random
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
st.set_page_config(
    page_title="Sistema de Mejora Continua - Fabricación y PDI",
    page_icon="🚌",
    layout="wide",
)

APP_DIR = Path(__file__).resolve().parent
FAB_CHECKLIST_PATH = APP_DIR / "Checklist_PRO_resultado.xlsx"
MEDIA_DIR = APP_DIR / "evidencias_fabricacion"
MEDIA_DIR.mkdir(exist_ok=True)

# =========================================================
# BÚSQUEDA DE LOGOS
# =========================================================
def find_first_existing(candidates):
    for p in candidates:
        if p.exists():
            return p
    return None

LOGO_ANDES = find_first_existing([
    APP_DIR / "logo_andes_motor.png",
    APP_DIR / "logo_andes_motor.jpg",
    APP_DIR / "logo_andes_motor.jpeg",
    APP_DIR / "logo_andes_motor.webp",
    APP_DIR / "logo_andes_motor.png.png",
    APP_DIR / "andes_motor.png",
    APP_DIR / "andes_motor.jpg",
    APP_DIR / "andes_motor.jpeg",
    APP_DIR / "andes_motor.webp",
])

LOGO_FOTON = find_first_existing([
    APP_DIR / "logo_foton.png",
    APP_DIR / "logo_foton.jpg",
    APP_DIR / "logo_foton.jpeg",
    APP_DIR / "logo_foton.webp",
    APP_DIR / "logo_foton.png.png",
    APP_DIR / "logo_foton.png(1).png",
    APP_DIR / "88b1d5_a1735a5d1d534f359bfcdf5c93d2165d~mv2.png",
])

# =========================================================
# MAESTROS
# =========================================================
MODELOS = [
    "Foton U9 eléctrico",
    "Foton U10 eléctrico",
    "Foton U12 eléctrico",
    "Foton DU9 diésel",
    "Foton DU10 diésel",
]

STAGE_1 = "Línea de producción estructural del bus"
STAGE_2 = "Línea de montaje de partes y piezas al bus"
STAGE_3 = "Línea de montaje equipamiento tecnológico"

FAB_STAGES = [STAGE_1, STAGE_2, STAGE_3]

PDI_BLOCKS = [
    "Recepción y seguridad",
    "Eléctrico",
    "Mecánico",
    "Carrocería",
    "Prueba de ruta",
    "Liberación",
]

ESTADOS = ["Sí", "No", "Obs", "NA"]

DEFAULT_FAB_CHECKLIST = [
    {"Etapa": STAGE_1, "Seccion": "Estructura", "Requisito": "Geometría general conforme a especificación", "Norma Base": "Plano / estándar de fabricación", "Criticidad": "Alta"},
    {"Etapa": STAGE_1, "Seccion": "Soldaduras", "Requisito": "Soldaduras sin fisuras, porosidad ni discontinuidades", "Norma Base": "Control visual soldadura", "Criticidad": "Alta"},
    {"Etapa": STAGE_1, "Seccion": "Carrocería", "Requisito": "Alineación de paneles y uniones estructurales", "Norma Base": "Tolerancia visual y dimensional", "Criticidad": "Alta"},
    {"Etapa": STAGE_1, "Seccion": "Protección", "Requisito": "Aplicación de protección anticorrosiva", "Norma Base": "Estándar proceso pintura", "Criticidad": "Media"},
    {"Etapa": STAGE_2, "Seccion": "Puertas", "Requisito": "Montaje de puertas conforme y sin interferencias", "Norma Base": "Checklist montaje", "Criticidad": "Alta"},
    {"Etapa": STAGE_2, "Seccion": "Ventanas", "Requisito": "Ventanas y fijaciones correctamente instaladas", "Norma Base": "Checklist montaje", "Criticidad": "Media"},
    {"Etapa": STAGE_2, "Seccion": "Acabados", "Requisito": "Terminaciones interiores sin daños ni holguras excesivas", "Norma Base": "Control calidad visual", "Criticidad": "Media"},
    {"Etapa": STAGE_2, "Seccion": "Fijaciones", "Requisito": "Fijaciones críticas instaladas y verificadas", "Norma Base": "Torque / montaje", "Criticidad": "Alta"},
    {"Etapa": STAGE_3, "Seccion": "Eléctrico", "Requisito": "Cableado protegido y correctamente fijado", "Norma Base": "Estándar eléctrico", "Criticidad": "Alta"},
    {"Etapa": STAGE_3, "Seccion": "Equipamiento", "Requisito": "Instalación de GPS, cámaras y validador", "Norma Base": "Especificación comercial", "Criticidad": "Media"},
    {"Etapa": STAGE_3, "Seccion": "Iluminación", "Requisito": "Iluminación interior y exterior instalada", "Norma Base": "Checklist eléctrico", "Criticidad": "Media"},
    {"Etapa": STAGE_3, "Seccion": "Calidad final", "Requisito": "Unidad cumple estándar de fabricación", "Norma Base": "Liberación interna", "Criticidad": "Alta"},
]

PDI_CHECKLIST = [
    ("Recepción y seguridad", "Recepción", "El o los técnicos cuentan con protección mínima para trabajar en el vehículo y sistema de alto voltaje", "Pauta PDI", "Alta"),
    ("Recepción y seguridad", "Recepción", "Desconexión de seguridad de fusibles de alto voltaje realizada por personal responsable", "Pauta PDI", "Alta"),
    ("Recepción y seguridad", "Recepción", "No existen daños visibles de transporte en arribo", "Pauta PDI", "Alta"),
    ("Recepción y seguridad", "Documentación", "Documentación, OT, VIN y KM correctamente registrados", "Pauta PDI", "Media"),
    ("Eléctrico", "Puesto conductor", "Luces del tablero de instrumentos operativas", "Pauta PDI", "Media"),
    ("Eléctrico", "24V", "Verificación de fallas sistema diagnóstico, lectura y borrado de códigos", "Pauta PDI", "Alta"),
    ("Eléctrico", "24V", "Iluminación externa operativa", "Pauta PDI", "Alta"),
    ("Eléctrico", "24V", "Iluminación interna operativa", "Pauta PDI", "Media"),
    ("Eléctrico", "24V", "Puertas de pasajeros operativas, antiatrapamiento y emergencia", "Pauta PDI", "Alta"),
    ("Eléctrico", "Central eléctrica", "Fijación de cables y disyuntores KL15/KL30/KL31", "Pauta PDI", "Alta"),
    ("Eléctrico", "Baterías", "Estado de baterías con MidTronic y adjunto en pauta", "Pauta PDI", "Alta"),
    ("Eléctrico", "Alta tensión", "Inspección de cables de alto voltaje: estado, ruteo y fijación", "Pauta PDI", "Alta"),
    ("Eléctrico", "Alta tensión", "Sistema de incendio alto voltaje", "Pauta PDI", "Alta"),
    ("Mecánico", "Niveles", "Nivel de aceite de dirección conforme", "Pauta PDI", "Media"),
    ("Mecánico", "Niveles", "Nivel de aceite diferencial conforme", "Pauta PDI", "Media"),
    ("Mecánico", "Estanqueidad", "Sin fugas de aceites sistema de dirección", "Pauta PDI", "Alta"),
    ("Mecánico", "Estanqueidad", "Sin fugas de líquido refrigerante alto/bajo voltaje", "Pauta PDI", "Alta"),
    ("Mecánico", "Estanqueidad", "Sin fugas de aire en sistema neumático", "Pauta PDI", "Alta"),
    ("Mecánico", "Montaje", "Mangueras y tuberías sin roces anormales", "Pauta PDI", "Media"),
    ("Mecánico", "Motor", "Estado de radiadores", "Pauta PDI", "Media"),
    ("Mecánico", "Torques", "Torque rueda 600 Nm verificado", "Pauta PDI", "Alta"),
    ("Mecánico", "Suspensión", "Funcionamiento de suspensión neumática y altura conforme", "Pauta PDI", "Alta"),
    ("Carrocería", "General", "Estado del piso pasajeros", "Pauta PDI", "Media"),
    ("Carrocería", "General", "Estado asiento conductor, ajustes y movilidad", "Pauta PDI", "Media"),
    ("Carrocería", "Frontal", "Estado del parabrisas y goma", "Pauta PDI", "Alta"),
    ("Carrocería", "Costados", "Vidrios y espejos retrovisores", "Pauta PDI", "Alta"),
    ("Carrocería", "Costados", "Alineación de puertas", "Pauta PDI", "Alta"),
    ("Carrocería", "Trasero", "Luneta y goma", "Pauta PDI", "Media"),
    ("Carrocería", "Techo", "Cierre y apertura de escotillas", "Pauta PDI", "Media"),
    ("Carrocería", "Techo", "Impermeabilidad post lavado", "Pauta PDI", "Media"),
    ("Prueba de ruta", "Ruta", "Movimiento normal hacia adelante y hacia atrás", "Pauta PDI", "Alta"),
    ("Prueba de ruta", "Ruta", "Funcionamiento del motor eléctrico", "Pauta PDI", "Alta"),
    ("Prueba de ruta", "Ruta", "Sistema de dirección funciona normalmente", "Pauta PDI", "Alta"),
    ("Prueba de ruta", "Ruta", "Sistema de frenos y ABS funciona normalmente", "Pauta PDI", "Alta"),
    ("Prueba de ruta", "Ruta", "Puertas funcionan normalmente", "Pauta PDI", "Alta"),
    ("Prueba de ruta", "Ruta", "Controlar carga de freno regenerativo", "Pauta PDI", "Media"),
    ("Prueba de ruta", "Ruta", "Controlar accionamiento alarma exterior transeúntes", "Pauta PDI", "Media"),
    ("Liberación", "Cierre", "Unidad apta para liberación a cliente", "Pauta PDI", "Alta"),
]

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "fab_checklist_master": pd.DataFrame(),
    "plan": pd.DataFrame(),
    "fab_records": pd.DataFrame(),
    "pdi_records": pd.DataFrame(),
    "fab_filtro_activo": "Todas",
    "pdi_filtro_activo": "Todas",
    "dashboard_filtro_activo": "Todas",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# UI / ESTILO
# =========================================================
def img_to_data_uri(path: Path) -> str:
    if not path or not path.exists():
        return ""
    ext = path.suffix.lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{ext};base64,{encoded}"

def render_header():
    top1, top2 = st.columns([2.2, 7.8], vertical_alignment="center")
    with top1:
        if LOGO_ANDES and LOGO_ANDES.exists():
            st.image(str(LOGO_ANDES), width=190)
        else:
            st.warning("No se encontró el logo de Andes Motor en la carpeta del proyecto.")
    with top2:
        st.title("Sistema de Mejora Continua – Fabricación y PDI")
        st.caption("Visión directorio: control de calidad, revisión Chile, cumplimiento PDI y liberación de unidades")
    st.markdown(
        """
        <div style="
            height:8px;
            background: linear-gradient(90deg, #173F5F, #20639B, #3CAEA3);
            border-radius:999px;
            margin-top: 2px;
            margin-bottom: 14px;
        "></div>
        """,
        unsafe_allow_html=True,
    )

watermark_css = ""
if LOGO_FOTON:
    foton_uri_bg = img_to_data_uri(LOGO_FOTON)
    watermark_css = f"""
.stApp::before {{
    content: "";
    position: fixed;
    top: 50%;
    left: 50%;
    width: 500px;
    height: 500px;
    transform: translate(-50%, -50%);
    background-image: url("{foton_uri_bg}");
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain;
    opacity: 0.05;
    pointer-events: none;
    z-index: 0;
}}
"""

st.markdown(
    f"""
<style>
{watermark_css}
.block-container {{
    padding-top: 0.9rem;
    padding-bottom: 2rem;
    position: relative;
    z-index: 1;
}}
.main-title-wrap -unused {{
    background: linear-gradient(90deg, #0b3c5d, #1d70a2, #2e8bc0);
    border-radius: 18px;
    padding: 12px 18px;
    margin-top: 8px;
    margin-bottom: 16px;
    min-height: 84px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-shadow: 0 6px 22px rgba(11,60,93,0.18);
    overflow: hidden;
    width: 100%;
}}
.main-title-grid -unused {{
    display: grid;
    grid-template-columns: auto 1fr;
    align-items: center;
    column-gap: 18px;
}}
.main-title-text -unused {{
    color: white;
    font-size: 24px;
    font-weight: 800;
    line-height: 1.15;
    margin: 0;
    white-space: normal;
    word-break: break-word;
}}
.main-title-sub -unused {{
    color: rgba(255,255,255,0.92);
    font-size: 13px;
    margin-top: 3px;
    word-break: break-word;
}}
.kpi-card {{
    border-radius: 16px;
    padding: 12px 14px;
    color: white;
    font-weight: 700;
    text-align: center;
    margin-bottom: 8px;
    min-height: 102px;
    display:flex;
    align-items:center;
    justify-content:center;
    flex-direction:column;
    box-shadow: 0 8px 20px rgba(0,0,0,0.10);
}}
.bg-blue {{background: linear-gradient(135deg, #1565c0, #42a5f5);}}
.bg-green {{background: linear-gradient(135deg, #2e7d32, #66bb6a);}}
.bg-yellow {{background: linear-gradient(135deg, #f9a825, #ffd54f); color:#222;}}
.bg-red {{background: linear-gradient(135deg, #b71c1c, #ef5350);}}
.bg-purple {{background: linear-gradient(135deg, #6a1b9a, #ab47bc);}}
.bg-gray {{background: linear-gradient(135deg, #455a64, #90a4ae);}}
.info-chip {{
    background: rgba(238,245,251,0.95);
    border:1px solid #d6e4f0;
    border-radius:12px;
    padding:10px 12px;
    margin-bottom:8px;
}}
.small-note {{
    font-size: 13px;
    color: #4b5563;
    margin-top: -4px;
    margin-bottom: 10px;
}}

.stButton > button {{
    width: 100%;
    min-height: 48px;
    border-radius: 12px;
    white-space: normal;
}}

div[data-testid="stImage"] img {{
    max-width: 100%;
    height: auto;
}}

.section-card {{
    background: rgba(255,255,255,0.92);
    border: 1px solid #e6eef6;
    border-radius: 16px;
    padding: 12px 14px;
    margin-bottom: 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.05);
}}
div[role="radiogroup"] {{
    gap: 10px;
    flex-wrap: wrap;
}}
div[role="radiogroup"] > label {{
    background: rgba(245,247,251,0.95);
    border: 1px solid #dce6f2;
    border-radius: 12px;
    padding: 8px 12px;
    margin-bottom: 6px;
}}
div[data-testid="stPlotlyChart"] {{
    background: transparent !important;
}}
div[data-testid="stDataFrame"] {{
    background: rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}}
div[data-testid="stDataFrame"] div {{
    background: transparent !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

render_header()

# =========================================================
# HELPERS LÓGICOS
# =========================================================
def fmt_num(v):
    try:
        return f"{int(round(float(v), 0)):,.0f}".replace(",", ".")
    except Exception:
        return "0"

def fmt_pct(v):
    try:
        return f"{float(v):.1f}%"
    except Exception:
        return "0.0%"

def ensure_columns(df, cols):
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            if c == "Archivos_Registro":
                out[c] = out.get("Evidencia", "")
            else:
                out[c] = ""
    return out

def card(label, value, css):
    st.markdown(
        f'<div class="kpi-card {css}">{label}<br><span style="font-size:24px">{value}</span></div>',
        unsafe_allow_html=True,
    )

def render_evidence_preview(value, title="Evidencia"):
    items = [x.strip() for x in str(value).split(",") if x.strip()]
    if not items:
        return
    st.markdown(f"#### {title}")
    cols = st.columns(min(3, len(items)))
    for i, item in enumerate(items):
        path = APP_DIR / item
        with cols[i % len(cols)]:
            st.caption(item)
            if path.exists() and path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                st.image(str(path), use_container_width=True)

def dashboard_reason(row, fab_df, pdi_df):
    uid = row["Unidad_ID"]
    if row.get("Liberada") == "Sí":
        return "Proceso terminado y unidad liberada para entrega"
    pdi_u = pdi_df[pdi_df["Unidad_ID"] == uid].copy() if not pdi_df.empty else pd.DataFrame()
    fab_u = fab_df[fab_df["Unidad_ID"] == uid].copy() if not fab_df.empty else pd.DataFrame()
    crit_pending = critical_unvalidated_pdi(uid)
    if not crit_pending.empty:
        return "Desviaciones críticas de fabricación pendientes de validación en PDI Chile"
    if not pdi_u.empty:
        pdi_dev = pdi_u[pdi_u["Estado"].isin(["No", "Obs"])]
        if not pdi_dev.empty:
            sistemas = ", ".join(sorted(pdi_dev["Sistema"].astype(str).unique().tolist()))
            return f"Desviaciones abiertas en PDI: {sistemas}"
    if row.get("Marcada_PDI", 0) == 1:
        return "Unidad con desviaciones corregidas en fábrica, pendiente de revisión PDI Chile"
    if row.get("Estado_Fabricacion") == "Terminada" and row.get("Estado_PDI") == "Pendiente":
        return "Fabricación terminada, pendiente de tránsito / ingreso a revisión en Chile"
    return "Unidad en proceso"

def apply_dashboard_filter(plan_df, fab_df, filtro):
    if plan_df.empty:
        return plan_df.copy()
    out = plan_df.copy()
    if filtro == "EntregaSinReproceso":
        out = out[out["Liberada"] == "Sí"]
    elif filtro == "Liberadas":
        out = out[out["Liberada"] == "Sí"]
    elif filtro == "EnTransito":
        out = out[(out["Estado_Fabricacion"] == "Terminada") & (out["Estado_PDI"] == "Pendiente")]
    elif filtro == "DesviacionFabrica":
        out = out[out["Marcada_PDI"] == 1]
    elif filtro == "Bloqueadas":
        out = out[out["Estado_PDI"] == "Bloqueada"]
    elif filtro == "RevisionPDI":
        out = out[out["Estado_PDI"] == "Con desviaciones"]
    elif filtro == "Etapa1":
        out = out[out["Etapa_Habilitada"] == 1]
    elif filtro == "Etapa2":
        out = out[out["Etapa_Habilitada"] == 2]
    elif filtro == "Etapa3":
        out = out[out["Etapa_Habilitada"] == 3]
    elif filtro == "ConDesviosFab":
        if not fab_df.empty:
            units = fab_df[fab_df["Estado"].isin(["No", "Obs"])]["Unidad_ID"].unique().tolist()
            out = out[out["Unidad_ID"].isin(units)]
        else:
            out = out.iloc[0:0].copy()
    return out

def infer_criticidad(texto):
    t = str(texto).lower()
    crit_words = ["alto voltaje", "fren", "dirección", "direccion", "sold", "estructura", "puert", "parabris", "bater", "cable", "torque", "motor"]
    return "Alta" if any(w in t for w in crit_words) else "Media"

def infer_stage(texto):
    t = str(texto).lower()
    struct_words = ["estructura", "sold", "anticorros", "carrocer", "panel", "geometr", "dimens", "parabris"]
    parts_words = ["puert", "ventan", "acab", "fijac", "piso", "asiento", "cintur", "espejo", "luneta", "moldura", "portalón", "portalon"]
    if any(w in t for w in struct_words):
        return STAGE_1
    if any(w in t for w in parts_words):
        return STAGE_2
    return STAGE_3

def build_gauge(value, title, subtitle=""):
    color = "#70AD47" if value >= 95 else "#D9A300" if value >= 85 else "#C00000"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(value),
            number={"suffix": "%"},
            title={"text": f"{title}<br><span style='font-size:13px'>{subtitle}</span>"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "bgcolor": "rgba(0,0,0,0)",
                "steps": [
                    {"range": [0, 85], "color": "rgba(254,226,226,0.65)"},
                    {"range": [85, 95], "color": "rgba(254,243,199,0.65)"},
                    {"range": [95, 100], "color": "rgba(220,252,231,0.65)"},
                ],
            },
        )
    )
    fig.update_layout(
        height=240,
        margin=dict(l=15, r=15, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def build_stage_gauge(fab_df, stage, title=None):
    if title is None:
        title = stage
    if fab_df.empty:
        value = 0
    else:
        s = fab_df[fab_df["Etapa"] == stage].copy()
        total = len(s)
        ok = int((s["Estado"] == "Sí").sum()) if total else 0
        value = (ok / total * 100) if total else 0
    return build_gauge(value, title, "Fabricación")



def build_stage_deviation_pie(fab_df, stage, title=None):
    if title is None:
        title = stage
    if fab_df.empty:
        values = pd.DataFrame({"Estado": ["Conforme", "Desviación"], "Cantidad": [0, 0]})
    else:
        s = fab_df[fab_df["Etapa"] == stage].copy()
        conforme = int((s["Estado"] == "Sí").sum()) if not s.empty else 0
        desvio = int((s["Estado"].isin(["No", "Obs"])).sum()) if not s.empty else 0
        values = pd.DataFrame({"Estado": ["Conforme", "Desviación"], "Cantidad": [conforme, desvio]})
    fig = px.pie(values, names="Estado", values="Cantidad", title=title, hole=0.45)
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(height=290, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=50, b=10))
    return fig

def build_total_fabrication_pie(fab_df):
    if fab_df.empty:
        values = pd.DataFrame({"Estado": ["Aprobaciones", "Desviaciones"], "Cantidad": [0, 0]})
    else:
        ok = int((fab_df["Estado"] == "Sí").sum())
        bad = int((fab_df["Estado"].isin(["No", "Obs"])).sum())
        values = pd.DataFrame({"Estado": ["Aprobaciones", "Desviaciones"], "Cantidad": [ok, bad]})
    fig = px.pie(
        values,
        names="Estado",
        values="Cantidad",
        title="% total aprobaciones vs desviaciones en fábrica",
        hole=0.52,
        color="Estado",
        color_discrete_map={"Aprobaciones": "#70AD47", "Desviaciones": "#C00000"},
    )
    fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color="white", width=2)))
    fig.update_layout(height=330, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=60, b=10), title_font_size=16)
    return fig

def executive_status(row):
    if row["Liberada"] == "Sí":
        return "Liberada"
    if row["Estado_PDI"] == "Bloqueada":
        return "Bloqueada"
    if row["Estado_PDI"] == "Con desviaciones":
        return "En revisión PDI"
    if row["Estado_Fabricacion"] == "Terminada":
        return "Lista envío Chile"
    return row["Estado_Fabricacion"]

def generate_ppu(modelo, idx):
    pref = re.sub(r"[^A-Z0-9]", "", modelo.upper().replace("FOTON", ""))[:3]
    return f"{pref}{str(idx).zfill(4)[-4:]}"

def normalize_fab_output(df_out):
    if df_out is None or df_out.empty:
        df_out = pd.DataFrame(DEFAULT_FAB_CHECKLIST)
    df_out = df_out.copy()
    for col in ["Etapa", "Seccion", "Requisito", "Norma Base", "Criticidad"]:
        if col not in df_out.columns:
            df_out[col] = ""
    for c in ["Etapa", "Seccion", "Requisito", "Norma Base", "Criticidad"]:
        df_out[c] = df_out[c].astype(str).str.strip()
    df_out = df_out[df_out["Requisito"].ne("") & ~df_out["Requisito"].str.lower().isin(["nan", "none"])].copy()
    df_out.loc[df_out["Criticidad"] == "", "Criticidad"] = df_out["Requisito"].apply(infer_criticidad)
    empty_stage = df_out["Etapa"] == ""
    df_out.loc[empty_stage, "Etapa"] = (df_out.loc[empty_stage, "Seccion"] + " " + df_out.loc[empty_stage, "Requisito"]).apply(infer_stage)
    if df_out.empty:
        df_out = pd.DataFrame(DEFAULT_FAB_CHECKLIST)
    return df_out[["Etapa", "Seccion", "Requisito", "Norma Base", "Criticidad"]].drop_duplicates().reset_index(drop=True)

@st.cache_data
def cargar_checklist_fabricacion(source):
    if isinstance(source, (str, Path)):
        source = Path(source)
        if not source.exists():
            return normalize_fab_output(pd.DataFrame(DEFAULT_FAB_CHECKLIST))
        xls = pd.ExcelFile(source)
        read_source = source
    else:
        xls = pd.ExcelFile(source)
        read_source = source

    frames = []
    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(read_source, sheet_name=sheet)
        except Exception:
            continue
        if df.empty:
            continue

        df.columns = [str(c).strip() for c in df.columns]
        lower_map = {str(c).strip().lower(): c for c in df.columns}

        # Lectura exacta para el nuevo checklist estructurado por etapa
        codigo_col = next((lower_map[k] for k in lower_map if k in ["código", "codigo"]), None)
        etapa_col = next((lower_map[k] for k in lower_map if k == "etapa"), None)
        sistema_col = next((lower_map[k] for k in lower_map if "sistema / subsistema" in k or "sistema/subsistema" in k), None)
        punto_col = next((lower_map[k] for k in lower_map if "punto de revisión" in k or "punto de revision" in k), None)

        if etapa_col and sistema_col and punto_col:
            tmp = pd.DataFrame()
            tmp["Etapa"] = df[etapa_col].astype(str).str.strip()
            tmp["Seccion"] = df[sistema_col].astype(str).str.strip()
            tmp["Requisito"] = df[punto_col].astype(str).str.strip()
            tmp["Norma Base"] = df[codigo_col].astype(str).str.strip() if codigo_col else sheet
            tmp["Criticidad"] = ""
            frames.append(tmp)
            continue

        # Respaldo para formatos anteriores del checklist
        req_col = next((lower_map[k] for k in lower_map if "requis" in k), None)
        sec_col = next((lower_map[k] for k in lower_map if "secci" in k or "grupo" in k), None)
        norm_col = next((lower_map[k] for k in lower_map if "norma" in k), None)
        etapa_col = next((lower_map[k] for k in lower_map if "etapa" in k), None)
        crit_col = next((lower_map[k] for k in lower_map if "critic" in k), None)

        if req_col is None:
            text_cols = [c for c in df.columns if df[c].astype(str).str.strip().ne("").sum() > 3]
            if text_cols:
                req_col = text_cols[min(1, len(text_cols) - 1)]
                sec_col = text_cols[0]

        if req_col is None:
            continue

        tmp = pd.DataFrame()
        tmp["Seccion"] = df[sec_col].astype(str).str.strip() if sec_col else sheet
        tmp["Requisito"] = df[req_col].astype(str).str.strip()
        tmp["Norma Base"] = df[norm_col].astype(str).str.strip() if norm_col else sheet
        tmp["Criticidad"] = df[crit_col].astype(str).str.strip() if crit_col else ""
        tmp["Etapa"] = df[etapa_col].astype(str).str.strip() if etapa_col else ""
        frames.append(tmp)

    if frames:
        return normalize_fab_output(pd.concat(frames, ignore_index=True))
    return normalize_fab_output(pd.DataFrame(DEFAULT_FAB_CHECKLIST))

def pdi_master():
    return pd.DataFrame(PDI_CHECKLIST, columns=["Sistema", "Seccion", "Requisito", "Norma Base", "Criticidad"])

def load_checklists():
    if st.session_state["fab_checklist_master"].empty:
        if FAB_CHECKLIST_PATH.exists():
            st.session_state["fab_checklist_master"] = cargar_checklist_fabricacion(FAB_CHECKLIST_PATH)
        else:
            legacy_path = APP_DIR / "Checklist_PRO_resultado.xlsx"
            if legacy_path.exists():
                st.session_state["fab_checklist_master"] = cargar_checklist_fabricacion(legacy_path)
            else:
                st.session_state["fab_checklist_master"] = pd.DataFrame(DEFAULT_FAB_CHECKLIST)

def get_plan():
    return st.session_state["plan"].copy()

def save_plan(df):
    st.session_state["plan"] = df.copy()

def get_fab():
    return st.session_state["fab_records"].copy()

def save_fab(df):
    st.session_state["fab_records"] = df.copy()

def get_pdi():
    return st.session_state["pdi_records"].copy()

def save_pdi(df):
    st.session_state["pdi_records"] = df.copy()

def plan_selector(df):
    if df.empty:
        return None

    view = st.radio("Vista", ["Una unidad", "Varias unidades", "Todas"], horizontal=True, key=f"view_{st.session_state.get('_current_menu','menu')}")
    modelos = sorted(df["Modelo"].unique().tolist())

    if view == "Una unidad":
        df_aux = df.copy()
        df_aux["Label"] = df_aux["VIN"] + " | " + df_aux["Modelo"] + " | " + df_aux["PPU"]
        label = st.selectbox("Seleccionar unidad", df_aux["Label"].tolist(), key=f"unit_{st.session_state.get('_current_menu','menu')}")
        unit = df_aux[df_aux["Label"] == label].iloc[0].to_dict()
        return {"view": view, "df": df_aux[df_aux["Unidad_ID"] == unit["Unidad_ID"]].copy(), "unit": unit}

    if view == "Varias unidades":
        modelo_sel = st.multiselect("Filtrar modelos", modelos, default=modelos[:1] if modelos else [], key=f"models_{st.session_state.get('_current_menu','menu')}")
        df_f = df[df["Modelo"].isin(modelo_sel)].copy() if modelo_sel else df.iloc[0:0].copy()
        return {"view": view, "df": df_f, "unit": None}

    return {"view": view, "df": df.copy(), "unit": None}

def fab_stage_records(unit_ids=None):
    df = get_fab()
    if unit_ids is not None and not df.empty:
        df = df[df["Unidad_ID"].isin(unit_ids)].copy()
    return df

def pdi_block_records(unit_ids=None):
    df = get_pdi()
    if unit_ids is not None and not df.empty:
        df = df[df["Unidad_ID"].isin(unit_ids)].copy()
    return df

def calc_completion(df, group_col):
    if df.empty:
        return pd.DataFrame({group_col: [], "cumplimiento": []})
    tmp = df.copy()
    tmp["ok"] = np.where(tmp["Estado"] == "Sí", 1, 0)
    out = tmp.groupby(group_col, as_index=False).agg(total=("Estado", "count"), ok=("ok", "sum"))
    out["cumplimiento"] = np.where(out["total"] > 0, out["ok"] / out["total"] * 100, 0)
    return out[[group_col, "cumplimiento"]]

def save_uploaded_files(files, unit_id, stage, row_idx):
    saved_names = []
    for file in files:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", file.name)
        folder = MEDIA_DIR / unit_id
        folder.mkdir(exist_ok=True)
        final_name = f"{stage[:10].replace(' ','_')}_{row_idx}_{ts}_{safe_name}"
        target = folder / final_name
        with open(target, "wb") as f:
            f.write(file.getbuffer())
        saved_names.append(str(target.relative_to(APP_DIR)))
    return saved_names

def unit_stage_complete(unit_id, stage):
    fab = get_fab()
    if fab.empty:
        return False
    x = fab[(fab["Unidad_ID"] == unit_id) & (fab["Etapa"] == stage)].copy()
    if x.empty:
        return False
    if "Evidencia" not in x.columns:
        x["Evidencia"] = x.get("Fotos", "")
    pending_corr = x[x["Estado"].isin(["No", "Obs"]) & x["Correccion"].fillna("").astype(str).str.strip().eq("")]
    pending_ev = x[x["Estado"].isin(["No", "Obs"]) & x["Evidencia"].fillna("").astype(str).str.strip().eq("")]
    return pending_corr.empty and pending_ev.empty

def allowed_fabrication_stages(unit_id):
    allowed = [STAGE_1]
    if unit_stage_complete(unit_id, STAGE_1):
        allowed.append(STAGE_2)
    if unit_stage_complete(unit_id, STAGE_2):
        allowed.append(STAGE_3)
    return allowed

def pending_rechecks_for_pdi(unit_id):
    fab = get_fab()
    if fab.empty:
        return pd.DataFrame()
    x = fab[(fab["Unidad_ID"] == unit_id) & (fab["Estado"].isin(["No", "Obs"]))].copy()
    if x.empty:
        return x
    if "Resultado_revision_PDI" not in x.columns:
        x["Resultado_revision_PDI"] = ""
    x["Resultado_revision_PDI"] = x["Resultado_revision_PDI"].fillna("")
    return x[x["Resultado_revision_PDI"] == ""].copy()

def critical_unvalidated_pdi(unit_id):
    x = pending_rechecks_for_pdi(unit_id)
    if x.empty:
        return x
    return x[x["Criticidad"] == "Alta"].copy()

def refresh_plan_status():
    plan = get_plan()
    if plan.empty:
        return

    fab = get_fab()
    pdi = get_pdi()

    for idx, row in plan.iterrows():
        uid = row["Unidad_ID"]
        fab_u = fab[fab["Unidad_ID"] == uid].copy() if not fab.empty else pd.DataFrame()
        pdi_u = pdi[pdi["Unidad_ID"] == uid].copy() if not pdi.empty else pd.DataFrame()

        marked = 0
        if not fab_u.empty:
            marked = int(((fab_u["Estado"].isin(["No", "Obs"])) & fab_u["Correccion"].fillna("").ne("")).sum() > 0)
        plan.loc[idx, "Marcada_PDI"] = marked

        if not fab_u.empty:
            completed_count = sum(unit_stage_complete(uid, s) for s in FAB_STAGES)
            plan.loc[idx, "Etapa_Habilitada"] = min(completed_count + 1, 3)
            plan.loc[idx, "Estado_Fabricacion"] = "Terminada" if completed_count == 3 else f"Etapa {min(completed_count + 1, 3)}"
        else:
            plan.loc[idx, "Etapa_Habilitada"] = 1
            plan.loc[idx, "Estado_Fabricacion"] = "Etapa 1"

        crit_pending = critical_unvalidated_pdi(uid)
        if not crit_pending.empty:
            plan.loc[idx, "Estado_PDI"] = "Bloqueada"
            plan.loc[idx, "Liberada"] = "No"
        elif not pdi_u.empty:
            non_yes = pdi_u[pdi_u["Estado"].isin(["No", "Obs"])]
            if non_yes.empty:
                plan.loc[idx, "Estado_PDI"] = "Conforme"
                lib_block = pdi_u[pdi_u["Sistema"] == "Liberación"]
                lib_yes = not lib_block.empty and (lib_block["Estado"] == "Sí").all()
                plan.loc[idx, "Liberada"] = "Sí" if lib_yes else "No"
            else:
                plan.loc[idx, "Estado_PDI"] = "Con desviaciones"
                plan.loc[idx, "Liberada"] = "No"
        else:
            plan.loc[idx, "Estado_PDI"] = "Pendiente"
            plan.loc[idx, "Liberada"] = "No"

    save_plan(plan)

def simulate_plan_auto():
    plan = get_plan()
    if plan.empty:
        return

    fab_master = st.session_state["fab_checklist_master"].copy()
    pdi_master_df = pdi_master().copy()

    fab_rows = []
    pdi_rows = []
    random.seed(42)

    for _, unit in plan.iterrows():
        uid = unit["Unidad_ID"]

        for stage in FAB_STAGES:
            base = fab_master[fab_master["Etapa"] == stage].copy()
            if base.empty:
                continue
            for _, r in base.iterrows():
                estado = random.choices(["Sí", "Obs", "No"], weights=[0.82, 0.12, 0.06])[0]
                correction = ""
                if estado in ["Obs", "No"]:
                    correction = f"Corrección aplicada en fábrica - {stage[:28]}"
                fab_rows.append({
                    "Unidad_ID": uid,
                    "Modelo": unit["Modelo"],
                    "VIN": unit["VIN"],
                    "PPU": unit["PPU"],
                    "Etapa": stage,
                    "Seccion": r["Seccion"],
                    "Requisito": r["Requisito"],
                    "Norma Base": r["Norma Base"],
                    "Criticidad": r["Criticidad"],
                    "Estado": estado,
                    "Observaciones": "Desviación detectada" if estado in ["Obs", "No"] else "",
                    "Correccion": correction,
                    "Evidencia": "evidencias_fabricacion/simulada.jpg" if estado in ["Obs", "No"] else "",
                    "Resultado_revision_PDI": "",
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })

        for _, r in pdi_master_df.iterrows():
            estado = random.choices(["Sí", "Obs", "No"], weights=[0.88, 0.08, 0.04])[0]
            pdi_rows.append({
                "Unidad_ID": uid,
                "Modelo": unit["Modelo"],
                "VIN": unit["VIN"],
                "PPU": unit["PPU"],
                "Sistema": r["Sistema"],
                "Seccion": r["Seccion"],
                "Requisito": r["Requisito"],
                "Norma Base": r["Norma Base"],
                "Criticidad": r["Criticidad"],
                "Estado": estado,
                "Observaciones": "Hallazgo PDI" if estado in ["Obs", "No"] else "",
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

    fab_df = pd.DataFrame(fab_rows)
    if not fab_df.empty:
        mask = fab_df["Estado"].isin(["Obs", "No"])
        results = np.random.choice(["Sí", "Obs", "No"], size=int(mask.sum()), p=[0.7, 0.2, 0.1])
        fab_df.loc[mask, "Resultado_revision_PDI"] = results

    save_fab(fab_df)
    save_pdi(pd.DataFrame(pdi_rows))
    refresh_plan_status()

def pdi_review_stage_summary(plan_scope, fab_scope):
    review = fab_scope[fab_scope["Estado"].isin(["No", "Obs"])].copy() if not fab_scope.empty else pd.DataFrame()
    if review.empty:
        return {
            STAGE_1: {"total": 0, "pendientes": 0},
            STAGE_2: {"total": 0, "pendientes": 0},
            STAGE_3: {"total": 0, "pendientes": 0},
        }
    out = {}
    for stage in FAB_STAGES:
        s = review[review["Etapa"] == stage].copy()
        total = len(s) if not s.empty else 0
        pendientes = len(s[s["Resultado_revision_PDI"].fillna("") == ""]) if not s.empty else 0
        out[stage] = {"total": total, "pendientes": pendientes}
    return out

# =========================================================
# RENDER
# =========================================================
def render_simulacion():
    st.subheader("📦 Simulación")
    load_checklists()
    plan = get_plan()

    c1, c2, c3 = st.columns(3)
    with c1:
        card("Unidades simuladas", fmt_num(len(plan)), "bg-blue")
    with c2:
        card("Modelos activos", fmt_num(plan["Modelo"].nunique() if not plan.empty else 0), "bg-green")
    with c3:
        card("Checklist fabricación", "Cargado" if not st.session_state["fab_checklist_master"].empty else "No cargado", "bg-purple")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        q_u9 = st.number_input("Foton U9 eléctrico", 0, 200, 5, 1)
    with c2:
        q_u10 = st.number_input("Foton U10 eléctrico", 0, 200, 4, 1)
    with c3:
        q_u12 = st.number_input("Foton U12 eléctrico", 0, 200, 3, 1)
    with c4:
        q_du9 = st.number_input("Foton DU9 diésel", 0, 200, 2, 1)
    with c5:
        q_du10 = st.number_input("Foton DU10 diésel", 0, 200, 2, 1)

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Generar simulación", use_container_width=True):
            rows = []
            idx = 1
            for modelo, qty in {
                "Foton U9 eléctrico": q_u9,
                "Foton U10 eléctrico": q_u10,
                "Foton U12 eléctrico": q_u12,
                "Foton DU9 diésel": q_du9,
                "Foton DU10 diésel": q_du10,
            }.items():
                for _ in range(int(qty)):
                    rows.append({
                        "Unidad_ID": f"UID-{idx:05d}",
                        "Modelo": modelo,
                        "VIN": f"SIM-{idx:05d}",
                        "PPU": generate_ppu(modelo, idx),
                        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Etapa_Habilitada": 1,
                        "Estado_Fabricacion": "Etapa 1",
                        "Marcada_PDI": 0,
                        "Estado_PDI": "Pendiente",
                        "Liberada": "No",
                    })
                    idx += 1
            save_plan(pd.DataFrame(rows))
            save_fab(pd.DataFrame())
            save_pdi(pd.DataFrame())
            st.success("Simulación generada correctamente.")
    with b2:
        if st.button("Simular fabricación + PDI", use_container_width=True):
            if plan.empty:
                st.warning("Primero genera una simulación.")
            else:
                simulate_plan_auto()
                st.success("Se generó simulación automática de fabricación y PDI.")
    with b3:
        if st.button("Reiniciar simulación", use_container_width=True):
            save_plan(pd.DataFrame())
            save_fab(pd.DataFrame())
            save_pdi(pd.DataFrame())
            st.success("Simulación reiniciada.")
    st.markdown('</div>', unsafe_allow_html=True)

    plan = get_plan()
    if not plan.empty:
        plan_show = plan.copy()
        plan_show["Estado Ejecutivo"] = plan_show.apply(executive_status, axis=1)
        st.dataframe(plan_show[["VIN", "Modelo", "PPU", "Estado_Fabricacion", "Estado_PDI", "Liberada", "Estado Ejecutivo"]], use_container_width=True)

def render_fabricacion():
    st.subheader("🏭 Fabricación")
    load_checklists()
    plan = get_plan()
    if plan.empty:
        st.info("Primero genera la simulación.")
        return

    filt = plan_selector(plan)
    df_view = filt["df"]
    unit = filt["unit"]
    unit_ids = df_view["Unidad_ID"].tolist() if not df_view.empty else []

    plan_scope = df_view.copy()
    fab_scope = fab_stage_records(unit_ids)

    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(build_stage_gauge(fab_scope, STAGE_1, "Producción estructural"), use_container_width=True)
    with g2:
        st.plotly_chart(build_stage_gauge(fab_scope, STAGE_2, "Montaje partes y piezas"), use_container_width=True)
    with g3:
        st.plotly_chart(build_stage_gauge(fab_scope, STAGE_3, "Equipamiento tecnológico"), use_container_width=True)
    et1 = len(plan_scope[plan_scope["Etapa_Habilitada"] == 1]) if not plan_scope.empty else 0
    et2 = len(plan_scope[plan_scope["Etapa_Habilitada"] == 2]) if not plan_scope.empty else 0
    et3 = len(plan_scope[plan_scope["Etapa_Habilitada"] == 3]) if not plan_scope.empty else 0
    terminadas = len(plan_scope[plan_scope["Estado_Fabricacion"] == "Terminada"]) if not plan_scope.empty else 0
    envio_chile = terminadas
    desv_fab = len(fab_scope[fab_scope["Estado"].isin(["No", "Obs"])]) if not fab_scope.empty else 0
    marcadas_pdi = int(plan_scope["Marcada_PDI"].sum()) if not plan_scope.empty else 0

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        card("Unidades en Línea de producción estructural del bus", fmt_num(et1), "bg-blue")
    with r1c2:
        card("Unidades en Línea de montaje de partes y piezas al bus", fmt_num(et2), "bg-blue")
    with r1c3:
        card("Unidades en Línea de montaje equipamiento tecnológico", fmt_num(et3), "bg-blue")
    with r1c4:
        card("Unidades listas para envío a Chile", fmt_num(envio_chile), "bg-green")

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        card("Desviaciones fabricación", fmt_num(desv_fab), "bg-red")
    with r2c2:
        card("Unidades con desviación corregida en fábrica", fmt_num(marcadas_pdi), "bg-yellow")
    with r2c3:
        card("Unidades fabricación terminada", fmt_num(terminadas), "bg-purple")

    b1, b2, b3, b4, b5, b6, b7, b8 = st.columns(8)
    with b1:
        if st.button("Ver Etapa 1", use_container_width=True, key="fab_btn_et1"):
            st.session_state["fab_filtro_activo"] = "Etapa 1"
    with b2:
        if st.button("Ver Etapa 2", use_container_width=True, key="fab_btn_et2"):
            st.session_state["fab_filtro_activo"] = "Etapa 2"
    with b3:
        if st.button("Ver Etapa 3", use_container_width=True, key="fab_btn_et3"):
            st.session_state["fab_filtro_activo"] = "Etapa 3"
    with b4:
        if st.button("Ver terminadas", use_container_width=True, key="fab_btn_term"):
            st.session_state["fab_filtro_activo"] = "Terminadas"
    with b5:
        if st.button("Ver desvíos", use_container_width=True, key="fab_btn_desv"):
            st.session_state["fab_filtro_activo"] = "Desvios"
    with b6:
        if st.button("Ver revisión PDI Chile", use_container_width=True, key="fab_btn_pdi"):
            st.session_state["fab_filtro_activo"] = "MarcadasPDI"
    with b7:
        if st.button("Ver envío Chile", use_container_width=True, key="fab_btn_envio"):
            st.session_state["fab_filtro_activo"] = "EnvioChile"
    with b8:
        if st.button("Ver todas", use_container_width=True, key="fab_btn_all"):
            st.session_state["fab_filtro_activo"] = "Todas"

    tabla_fabricacion = plan_scope.copy()
    filtro_fab = st.session_state.get("fab_filtro_activo", "Todas")
    if filtro_fab == "Etapa 1":
        tabla_fabricacion = tabla_fabricacion[tabla_fabricacion["Etapa_Habilitada"] == 1]
    elif filtro_fab == "Etapa 2":
        tabla_fabricacion = tabla_fabricacion[tabla_fabricacion["Etapa_Habilitada"] == 2]
    elif filtro_fab == "Etapa 3":
        tabla_fabricacion = tabla_fabricacion[tabla_fabricacion["Etapa_Habilitada"] == 3]
    elif filtro_fab == "Terminadas":
        tabla_fabricacion = tabla_fabricacion[tabla_fabricacion["Estado_Fabricacion"] == "Terminada"]
    elif filtro_fab == "Desvios":
        unidades_con_desvio = []
        if not fab_scope.empty:
            unidades_con_desvio = fab_scope[fab_scope["Estado"].isin(["No", "Obs"])]["Unidad_ID"].unique().tolist()
        tabla_fabricacion = tabla_fabricacion[tabla_fabricacion["Unidad_ID"].isin(unidades_con_desvio)]
    elif filtro_fab == "MarcadasPDI":
        tabla_fabricacion = tabla_fabricacion[tabla_fabricacion["Marcada_PDI"] == 1]
    elif filtro_fab == "EnvioChile":
        tabla_fabricacion = tabla_fabricacion[tabla_fabricacion["Estado_Fabricacion"] == "Terminada"]

    tabla_show = tabla_fabricacion.copy()
    if not tabla_show.empty:
        tabla_show["Estado Ejecutivo"] = tabla_show.apply(executive_status, axis=1)

    st.markdown(f"### Unidades filtradas: {filtro_fab}")
    if not tabla_show.empty:
        st.dataframe(tabla_show[["VIN", "Modelo", "PPU", "Estado_Fabricacion", "Etapa_Habilitada", "Marcada_PDI", "Estado Ejecutivo"]], use_container_width=True)
    else:
        st.info("No hay unidades para el filtro seleccionado.")

    if filtro_fab in ["Etapa 1", "Etapa 2", "Etapa 3", "Terminadas", "EnvioChile"] and not tabla_show.empty:
        st.markdown("#### Detalle de unidades")
        st.dataframe(tabla_show[["VIN", "Modelo", "PPU", "Estado_Fabricacion", "Etapa_Habilitada", "Estado Ejecutivo"]], use_container_width=True)

    if filtro_fab in ["Desvios", "MarcadasPDI"] and not fab_scope.empty:
        detalle_fab = fab_scope[fab_scope["Estado"].isin(["No", "Obs"])].copy()
        if filtro_fab == "MarcadasPDI":
            unidades = tabla_show["Unidad_ID"].tolist() if not tabla_show.empty else []
            detalle_fab = detalle_fab[detalle_fab["Unidad_ID"].isin(unidades)]
        if not detalle_fab.empty:
            st.markdown("#### Detalle de desviaciones de fabricación")
            detalle_cols = ["VIN", "Etapa", "Seccion", "Requisito", "Criticidad", "Estado", "Correccion", "Evidencia"]
            detalle_fab = ensure_columns(detalle_fab, detalle_cols)
            st.dataframe(detalle_fab[detalle_cols], use_container_width=True)
            first_ev = detalle_fab.iloc[0]["Evidencia"] if "Evidencia" in detalle_fab.columns else ""
            if str(first_ev).strip():
                render_evidence_preview(first_ev, "Vista previa evidencia de corrección")


    if filt["view"] != "Una unidad":
        return

    st.markdown(
        f"<div class='info-chip'><b>Unidad:</b> {unit['VIN']} | {unit['Modelo']} | {unit['PPU']} "
        f"&nbsp;&nbsp; <b>Etapa habilitada:</b> {unit['Etapa_Habilitada']}</div>",
        unsafe_allow_html=True,
    )

    allowed = allowed_fabrication_stages(unit["Unidad_ID"])
    stage = st.selectbox(
        "Etapa de fabricación",
        FAB_STAGES,
        index=min(unit["Etapa_Habilitada"] - 1, 2)
    )

    if stage not in allowed:
        st.error("No se puede avanzar a la siguiente etapa si la etapa anterior no está completamente terminada, corregida y guardada.")
        return

    master = normalize_fab_output(st.session_state["fab_checklist_master"].copy())
    base = master[master["Etapa"] == stage].copy()
    if base.empty:
        st.warning("No se encontraron ítems para esta etapa.")
        return

    existing = get_fab()
    prev = existing[(existing["Unidad_ID"] == unit["Unidad_ID"]) & (existing["Etapa"] == stage)].copy() if not existing.empty else pd.DataFrame()

    if not prev.empty:
        prev = prev.copy()
        if "Evidencia" not in prev.columns:
            prev["Evidencia"] = prev.get("Fotos", "")
        df_edit = prev[["Seccion", "Requisito", "Norma Base", "Criticidad", "Estado", "Observaciones", "Correccion", "Evidencia", "Resultado_revision_PDI"]].copy()
    else:
        df_edit = base.copy()
        df_edit["Estado"] = "Sí"
        df_edit["Observaciones"] = ""
        df_edit["Correccion"] = ""
        df_edit["Evidencia"] = ""
        df_edit["Resultado_revision_PDI"] = ""

    st.markdown(
        "<div class='small-note'>Toda desviación se corrige en fabricación y queda marcada para una segunda revisión obligatoria en Chile antes de la pauta PDI rutinaria. Cada hallazgo debe quedar con evidencia visual.</div>",
        unsafe_allow_html=True,
    )

    edited = st.data_editor(
        df_edit,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS),
            "Observaciones": st.column_config.TextColumn("Observaciones"),
            "Correccion": st.column_config.TextColumn("Cómo se corrigió"),
            "Evidencia": st.column_config.TextColumn("Evidencia de corrección", disabled=True),
            "Resultado_revision_PDI": st.column_config.TextColumn("Revisión PDI Chile", disabled=True),
        },
        key=f"fab_editor_{unit['Unidad_ID']}_{stage}",
    )

    flagged_idx = edited[edited["Estado"].isin(["No", "Obs"])].index.tolist()
    upload_map = {}
    if flagged_idx:
        st.markdown("### Evidencia por hallazgo")
        for idx in flagged_idx:
            req = str(edited.loc[idx, "Requisito"])
            current_ev = str(edited.loc[idx, "Evidencia"]).strip()
            if current_ev:
                st.caption(f"Evidencia actual: {current_ev}")
            files = st.file_uploader(
                f"Subir imágenes o videos - ítem {idx + 1}",
                accept_multiple_files=True,
                type=["png", "jpg", "jpeg", "webp", "mp4", "mov"],
                key=f"fab_media_{unit['Unidad_ID']}_{stage}_{idx}",
                help=req,
            )
            upload_map[idx] = files or []

    if st.button("Guardar etapa de fabricación", use_container_width=True):
        edited_save = edited.copy()
        for idx in flagged_idx:
            current = str(edited_save.loc[idx, "Evidencia"]).strip()
            new_files = upload_map.get(idx, [])
            saved = save_uploaded_files(new_files, unit["Unidad_ID"], stage, idx) if new_files else []
            edited_save.loc[idx, "Evidencia"] = ", ".join(saved) if saved else current

        need_corr = edited_save[edited_save["Estado"].isin(["No", "Obs"]) & edited_save["Correccion"].astype(str).str.strip().eq("")]
        need_ev = edited_save[edited_save["Estado"].isin(["No", "Obs"]) & edited_save["Evidencia"].astype(str).str.strip().eq("")]
        if not need_corr.empty:
            st.error("Toda desviación debe registrar cómo se corrigió antes de guardar.")
            return
        if not need_ev.empty:
            st.error("Toda observación o no cumplimiento debe adjuntar evidencia antes de guardar.")
            return

        rows = edited_save.copy()
        rows["Unidad_ID"] = unit["Unidad_ID"]
        rows["Modelo"] = unit["Modelo"]
        rows["VIN"] = unit["VIN"]
        rows["PPU"] = unit["PPU"]
        rows["Etapa"] = stage
        rows["Fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        fab = get_fab()
        if not fab.empty:
            fab = fab[~((fab["Unidad_ID"] == unit["Unidad_ID"]) & (fab["Etapa"] == stage))].copy()
            fab = pd.concat([fab, rows], ignore_index=True)
        else:
            fab = rows.copy()

        save_fab(fab)
        refresh_plan_status()
        st.success("Etapa guardada correctamente. Si hubo desviaciones, la unidad quedó marcada para revisión PDI Chile con evidencia disponible para consulta.")

def render_pdi():
    st.subheader("🛠️ PDI")
    plan = get_plan()
    if plan.empty:
        st.info("Primero genera la simulación.")
        return

    filt = plan_selector(plan)
    df_view = filt["df"]
    unit = filt["unit"]
    unit_ids = df_view["Unidad_ID"].tolist() if not df_view.empty else []

    plan_scope = df_view.copy()
    fab_scope = fab_stage_records(unit_ids)
    pdi_scope = pdi_block_records(unit_ids)

    review_summary = pdi_review_stage_summary(plan_scope, fab_scope)

    st.markdown("### Cantidad de desvíos por etapa")
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Estructural", fmt_num(review_summary[STAGE_1]["total"]), "bg-yellow")
        st.caption(f"Pendientes de revisión: {fmt_num(review_summary[STAGE_1]['pendientes'])}")
    with c2:
        card("Partes y piezas", fmt_num(review_summary[STAGE_2]["total"]), "bg-yellow")
        st.caption(f"Pendientes de revisión: {fmt_num(review_summary[STAGE_2]['pendientes'])}")
    with c3:
        card("Equipamiento tecnológico", fmt_num(review_summary[STAGE_3]["total"]), "bg-yellow")
        st.caption(f"Pendientes de revisión: {fmt_num(review_summary[STAGE_3]['pendientes'])}")

    st.markdown("### Cumplimiento pauta PDI rutinaria")
    comp = calc_completion(pdi_scope, "Sistema")
    comp_map = {r["Sistema"]: r["cumplimiento"] for _, r in comp.iterrows()} if not comp.empty else {}
    pdi_gauges = [s for s in PDI_BLOCKS if s != "Liberación"]
    cols = st.columns(len(pdi_gauges))
    for i, sistema in enumerate(pdi_gauges):
        with cols[i]:
            st.plotly_chart(build_gauge(comp_map.get(sistema, 0), sistema, "PDI"), use_container_width=True)

    pendientes_pdi = len(plan_scope[plan_scope["Estado_PDI"] == "Pendiente"]) if not plan_scope.empty else 0
    en_revision = len(plan_scope[plan_scope["Estado_PDI"] == "Con desviaciones"]) if not plan_scope.empty else 0
    bloqueadas = len(plan_scope[plan_scope["Estado_PDI"] == "Bloqueada"]) if not plan_scope.empty else 0
    liberadas = len(plan_scope[plan_scope["Liberada"] == "Sí"]) if not plan_scope.empty else 0
    alertas_fab = int(plan_scope["Marcada_PDI"].sum()) if not plan_scope.empty else 0
    en_transito = len(plan_scope[(plan_scope["Estado_Fabricacion"] == "Terminada") & (plan_scope["Estado_PDI"] == "Pendiente")]) if not plan_scope.empty else 0
    crit_pend = 0
    if not fab_scope.empty:
        crit_pend = len(
            fab_scope[
                fab_scope["Estado"].isin(["No", "Obs"]) &
                (fab_scope["Criticidad"] == "Alta") &
                (fab_scope["Resultado_revision_PDI"].fillna("") == "")
            ]
        )

    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    with k1:
        card("Pendientes PDI", fmt_num(pendientes_pdi), "bg-blue")
    with k2:
        card("En revisión PDI", fmt_num(en_revision), "bg-yellow")
    with k3:
        card("Bloqueadas", fmt_num(bloqueadas), "bg-red")
    with k4:
        card("Unidades liberadas", fmt_num(liberadas), "bg-green")
    with k5:
        card("Unidades con desviación en fábrica", fmt_num(alertas_fab), "bg-purple")
    with k6:
        card("En tránsito China-Chile", fmt_num(en_transito), "bg-gray")
    with k7:
        card("Pendientes revisión Chile", fmt_num(crit_pend), "bg-gray")

    if int(plan_scope["Marcada_PDI"].sum()) > 0:
        st.warning("Hay unidades con desviaciones corregidas en fábrica que deben validarse en Chile antes de ejecutar la pauta PDI rutinaria. Mientras no se validen evidencia y corrección, la pauta PDI queda bloqueada.")

    b1, b2, b3, b4, b5, b6, b7, b8 = st.columns(8)
    with b1:
        if st.button("Ver pendientes", use_container_width=True, key="pdi_btn_pend"):
            st.session_state["pdi_filtro_activo"] = "Pendientes"
    with b2:
        if st.button("Ver revisión", use_container_width=True, key="pdi_btn_rev"):
            st.session_state["pdi_filtro_activo"] = "Revision"
    with b3:
        if st.button("Ver bloqueadas", use_container_width=True, key="pdi_btn_block"):
            st.session_state["pdi_filtro_activo"] = "Bloqueadas"
    with b4:
        if st.button("Ver unidades liberadas", use_container_width=True, key="pdi_btn_lib"):
            st.session_state["pdi_filtro_activo"] = "Liberadas"
    with b5:
        if st.button("Ver revisión Chile", use_container_width=True, key="pdi_btn_alert"):
            st.session_state["pdi_filtro_activo"] = "Alertas"
    with b6:
        if st.button("Ver críticas", use_container_width=True, key="pdi_btn_crit"):
            st.session_state["pdi_filtro_activo"] = "Criticas"
    with b7:
        if st.button("Ver tránsito", use_container_width=True, key="pdi_btn_trans"):
            st.session_state["pdi_filtro_activo"] = "Transito"
    with b8:
        if st.button("Ver todas", use_container_width=True, key="pdi_btn_all"):
            st.session_state["pdi_filtro_activo"] = "Todas"

    tabla_pdi = plan_scope.copy()
    filtro_pdi = st.session_state.get("pdi_filtro_activo", "Todas")
    if filtro_pdi == "Pendientes":
        tabla_pdi = tabla_pdi[tabla_pdi["Estado_PDI"] == "Pendiente"]
    elif filtro_pdi == "Revision":
        tabla_pdi = tabla_pdi[tabla_pdi["Estado_PDI"] == "Con desviaciones"]
    elif filtro_pdi == "Bloqueadas":
        tabla_pdi = tabla_pdi[tabla_pdi["Estado_PDI"] == "Bloqueada"]
    elif filtro_pdi == "Liberadas":
        tabla_pdi = tabla_pdi[tabla_pdi["Liberada"] == "Sí"]
    elif filtro_pdi == "Alertas":
        tabla_pdi = tabla_pdi[tabla_pdi["Marcada_PDI"] == 1]
    elif filtro_pdi == "Transito":
        tabla_pdi = tabla_pdi[(tabla_pdi["Estado_Fabricacion"] == "Terminada") & (tabla_pdi["Estado_PDI"] == "Pendiente")]
    elif filtro_pdi == "Criticas":
        unidades_criticas = []
        if not fab_scope.empty:
            unidades_criticas = fab_scope[
                fab_scope["Estado"].isin(["No", "Obs"]) &
                (fab_scope["Criticidad"] == "Alta") &
                (fab_scope["Resultado_revision_PDI"].fillna("") == "")
            ]["Unidad_ID"].unique().tolist()
        tabla_pdi = tabla_pdi[tabla_pdi["Unidad_ID"].isin(unidades_criticas)]

    tabla_show = tabla_pdi.copy()
    if not tabla_show.empty:
        tabla_show["Estado Ejecutivo"] = tabla_show.apply(executive_status, axis=1)

    st.markdown(f"### Unidades filtradas: {filtro_pdi}")
    if not tabla_show.empty:
        st.dataframe(
            tabla_show[["VIN", "Modelo", "PPU", "Marcada_PDI", "Estado_PDI", "Liberada", "Estado Ejecutivo"]],
            use_container_width=True,
        )
    else:
        st.info("No hay unidades para el filtro seleccionado.")

    if filtro_pdi in ["Pendientes", "Liberadas", "Transito"] and not tabla_show.empty:
        st.markdown("#### Detalle de unidades")
        st.dataframe(
            tabla_show[["VIN", "Modelo", "PPU", "Marcada_PDI", "Estado_PDI", "Liberada", "Estado Ejecutivo"]],
            use_container_width=True,
        )

    if filtro_pdi in ["Revision", "Bloqueadas", "Criticas"] and not pdi_scope.empty:
        detalle_pdi = pdi_scope[pdi_scope["Estado"].isin(["No", "Obs"])].copy()
        if filtro_pdi == "Revision":
            unidades = tabla_show["Unidad_ID"].tolist() if not tabla_show.empty else []
            detalle_pdi = detalle_pdi[detalle_pdi["Unidad_ID"].isin(unidades)]
        elif filtro_pdi == "Bloqueadas":
            unidades = tabla_show["Unidad_ID"].tolist() if not tabla_show.empty else []
            detalle_pdi = detalle_pdi[detalle_pdi["Unidad_ID"].isin(unidades)]
        elif filtro_pdi == "Criticas":
            detalle_pdi = detalle_pdi[detalle_pdi["Criticidad"] == "Alta"]
        if not detalle_pdi.empty:
            st.markdown("#### Detalle de hallazgos PDI")
            st.dataframe(detalle_pdi[["VIN", "Sistema", "Seccion", "Requisito", "Criticidad", "Estado", "Observaciones"]], use_container_width=True)

    if filtro_pdi in ["Alertas", "Criticas"] and not fab_scope.empty:
        detalle_fab = fab_scope[fab_scope["Estado"].isin(["No", "Obs"])].copy()
        if filtro_pdi == "Criticas":
            detalle_fab = detalle_fab[(detalle_fab["Criticidad"] == "Alta") & (detalle_fab["Resultado_revision_PDI"].fillna("") == "")]
        else:
            unidades = tabla_show["Unidad_ID"].tolist() if not tabla_show.empty else []
            detalle_fab = detalle_fab[detalle_fab["Unidad_ID"].isin(unidades)]
        if not detalle_fab.empty:
            st.markdown("#### Detalle de desviaciones de fabricación para revisión Chile")
            detalle_cols = ["VIN", "Etapa", "Seccion", "Requisito", "Criticidad", "Correccion", "Evidencia", "Resultado_revision_PDI"]
            detalle_fab = ensure_columns(detalle_fab, detalle_cols)
            st.dataframe(detalle_fab[detalle_cols], use_container_width=True)
            first_ev = detalle_fab.iloc[0]["Evidencia"] if "Evidencia" in detalle_fab.columns else ""
            if str(first_ev).strip():
                render_evidence_preview(first_ev, "Vista previa evidencia de corrección")

    if not fab_scope.empty:
        review = fab_scope[fab_scope["Estado"].isin(["No", "Obs"])].copy()
        if not review.empty:
            resumen_rechecks = review.groupby("Etapa", as_index=False).agg(
                Total=("Requisito", "count"),
                Pendientes=("Resultado_revision_PDI", lambda x: (x.fillna("") == "").sum()),
                Aprobadas=("Resultado_revision_PDI", lambda x: (x == "Sí").sum()),
                Observadas=("Resultado_revision_PDI", lambda x: (x == "Obs").sum()),
                Rechazadas=("Resultado_revision_PDI", lambda x: (x == "No").sum()),
            )
            st.markdown("### Estado de revisión Chile por etapa de fabricación")
            st.dataframe(resumen_rechecks, use_container_width=True)

    if filt["view"] != "Una unidad":
        return

    st.markdown(
        f"<div class='info-chip'><b>Unidad:</b> {unit['VIN']} | {unit['Modelo']} | {unit['PPU']} "
        f"&nbsp;&nbsp; <b>Estado PDI:</b> {unit['Estado_PDI']}</div>",
        unsafe_allow_html=True,
    )

    pendientes = pending_rechecks_for_pdi(unit["Unidad_ID"])
    if not pendientes.empty:
        st.error("⚠️ Esta unidad presenta desviaciones corregidas en fábrica que deben validarse en PDI Chile antes de ejecutar la pauta de preentrega.")
        show_cols = [c for c in ["Etapa", "Seccion", "Requisito", "Criticidad", "Observaciones", "Correccion", "Evidencia"] if c in pendientes.columns]
        st.dataframe(ensure_columns(pendientes, show_cols)[show_cols], use_container_width=True)
        first_ev = ensure_columns(pendientes, ["Evidencia"]).iloc[0]["Evidencia"] if not pendientes.empty else ""
        if str(first_ev).strip():
            render_evidence_preview(first_ev, "Vista previa evidencia de corrección")
        st.markdown("#### Validación obligatoria de funcionamiento y evidencia")
    else:
        st.success("No hay alertas de revisión Chile pendientes para esta unidad. Ya puedes ejecutar la pauta PDI rutinaria.")

    sistema = st.selectbox("Bloque PDI rutinario", PDI_BLOCKS)
    base = pdi_master()[lambda d: d["Sistema"] == sistema].copy()
    pdi = get_pdi()
    prev = pdi[(pdi["Unidad_ID"] == unit["Unidad_ID"]) & (pdi["Sistema"] == sistema)].copy() if not pdi.empty else pd.DataFrame()

    if not prev.empty:
        df_edit = prev[["Sistema", "Seccion", "Requisito", "Norma Base", "Criticidad", "Estado", "Observaciones"]].copy()
    else:
        df_edit = base.copy()
        df_edit["Estado"] = "Sí"
        df_edit["Observaciones"] = ""

    st.markdown(
        "<div class='small-note'>No se puede liberar una unidad si presenta desviaciones en PDI o si una desviación crítica arrastrada desde fabricación no fue validada correctamente en Chile.</div>",
        unsafe_allow_html=True,
    )
    edited = st.data_editor(
        df_edit,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS),
            "Observaciones": st.column_config.TextColumn("Observaciones"),
        },
        key=f"pdi_editor_{unit['Unidad_ID']}_{sistema}",
    )

    if not pendientes.empty:
        st.markdown("### Revisión PDI Chile de desviaciones originadas en fabricación")
        if "Evidencia" not in pendientes.columns:
            pendientes["Evidencia"] = pendientes.get("Fotos", "")
        rev = pendientes[["Etapa", "Seccion", "Requisito", "Criticidad", "Correccion", "Evidencia", "Resultado_revision_PDI"]].copy()
        rev["Resultado_revision_PDI"] = rev["Resultado_revision_PDI"].replace("", "Pendiente")
        reval = st.data_editor(
            rev,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "Resultado_revision_PDI": st.column_config.SelectboxColumn(
                    "Resultado revisión PDI Chile",
                    options=["Pendiente", "Sí", "Obs", "No"]
                )
            },
            key=f"reval_{unit['Unidad_ID']}",
        )
    else:
        reval = pd.DataFrame()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Guardar bloque PDI", use_container_width=True):
            rows = edited.copy()
            rows["Unidad_ID"] = unit["Unidad_ID"]
            rows["Modelo"] = unit["Modelo"]
            rows["VIN"] = unit["VIN"]
            rows["PPU"] = unit["PPU"]
            rows["Fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M")

            pdi_cur = get_pdi()
            if not pdi_cur.empty:
                pdi_cur = pdi_cur[~((pdi_cur["Unidad_ID"] == unit["Unidad_ID"]) & (pdi_cur["Sistema"] == sistema))].copy()
                pdi_cur = pd.concat([pdi_cur, rows], ignore_index=True)
            else:
                pdi_cur = rows.copy()

            save_pdi(pdi_cur)

            if not reval.empty:
                fab = get_fab()
                updates = reval.copy()
                updates["Resultado_revision_PDI"] = updates["Resultado_revision_PDI"].replace("Pendiente", "")
                for _, u in updates.iterrows():
                    mask = (
                        (fab["Unidad_ID"] == unit["Unidad_ID"]) &
                        (fab["Etapa"] == u["Etapa"]) &
                        (fab["Seccion"] == u["Seccion"]) &
                        (fab["Requisito"] == u["Requisito"])
                    )
                    fab.loc[mask, "Resultado_revision_PDI"] = u["Resultado_revision_PDI"]
                save_fab(fab)

            refresh_plan_status()
            st.success("Bloque PDI guardado correctamente.")

    with c2:
        crit_pending = critical_unvalidated_pdi(unit["Unidad_ID"])
        pdi_cur = get_pdi()
        pdi_unit = pdi_cur[pdi_cur["Unidad_ID"] == unit["Unidad_ID"]].copy() if not pdi_cur.empty else pd.DataFrame()
        has_pdi_deviation = (not pdi_unit.empty) and (not pdi_unit[pdi_unit["Estado"].isin(["No", "Obs"])].empty)
        can_release = crit_pending.empty and (not has_pdi_deviation) and (not pdi_unit.empty)

        if st.button("Liberar unidad", use_container_width=True, disabled=not can_release):
            plan = get_plan()
            plan.loc[plan["Unidad_ID"] == unit["Unidad_ID"], "Liberada"] = "Sí"
            plan.loc[plan["Unidad_ID"] == unit["Unidad_ID"], "Estado_PDI"] = "Conforme"
            save_plan(plan)
            st.success("Unidad liberada correctamente.")

        if not can_release:
            st.error("No se puede liberar: existen desviaciones en PDI o desviaciones críticas de fabricación pendientes de validación.")


def render_dashboard():
    st.subheader("📊 Dashboard Ejecutivo")
    st.caption("Vista ejecutiva de lo que ocurre en fábrica y PDI, orientada a corregir, revalidar y entregar sin reproceso.")
    plan = get_plan()
    fab = get_fab()
    pdi = get_pdi()
    if plan.empty:
        st.info("Primero genera la simulación.")
        return

    fab_comp = calc_completion(fab, "Etapa")
    pdi_comp = calc_completion(pdi, "Sistema")
    fab_global = float(fab_comp["cumplimiento"].mean()) if not fab_comp.empty else 0
    pdi_global = float(pdi_comp["cumplimiento"].mean()) if not pdi_comp.empty else 0
    liberacion = (plan["Liberada"] == "Sí").mean() * 100 if not plan.empty else 0
    unidades_liberadas = len(plan[plan["Liberada"] == "Sí"])

    envio_chile = len(plan[plan["Estado_Fabricacion"] == "Terminada"])
    revision_pdi = len(plan[plan["Estado_PDI"] == "Con desviaciones"])
    bloqueadas = len(plan[plan["Estado_PDI"] == "Bloqueada"])
    marcadas_chile = int(plan["Marcada_PDI"].sum())
    en_transito = len(plan[(plan["Estado_Fabricacion"] == "Terminada") & (plan["Estado_PDI"] == "Pendiente")])

    plan_exec = plan.copy()
    plan_exec["Estado Ejecutivo"] = plan_exec.apply(executive_status, axis=1)
    plan_exec["Motivo operacional"] = plan_exec.apply(lambda r: dashboard_reason(r, fab, pdi), axis=1)

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        card("Cumplimiento fabricación", fmt_pct(fab_global), "bg-green")
    with c2:
        card("Cumplimiento PDI", fmt_pct(pdi_global), "bg-green")
    with c3:
        card("Entrega sin reproceso", fmt_pct(liberacion), "bg-purple")
    with c4:
        card("Unidades liberadas", fmt_num(unidades_liberadas), "bg-green")
    with c5:
        card("Unidades en tránsito China-Chile", fmt_num(en_transito), "bg-blue")
    with c6:
        card("Unidades con desviación en fábrica", fmt_num(marcadas_chile), "bg-yellow")
    with c7:
        card("Bloqueadas", fmt_num(bloqueadas), "bg-red")

    f1, f2, f3, f4, f5, f6, f7, f8 = st.columns(8)
    with f1:
        if st.button("Ver entrega sin reproceso", use_container_width=True, key="dash_btn_entrega"):
            st.session_state["dashboard_filtro_activo"] = "EntregaSinReproceso"
    with f2:
        if st.button("Ver unidades liberadas", use_container_width=True, key="dash_btn_lib"):
            st.session_state["dashboard_filtro_activo"] = "Liberadas"
    with f3:
        if st.button("Ver tránsito", use_container_width=True, key="dash_btn_transito"):
            st.session_state["dashboard_filtro_activo"] = "EnTransito"
    with f4:
        if st.button("Ver desvíos fábrica", use_container_width=True, key="dash_btn_fab"):
            st.session_state["dashboard_filtro_activo"] = "DesviacionFabrica"
    with f5:
        if st.button("Ver revisión PDI", use_container_width=True, key="dash_btn_rev"):
            st.session_state["dashboard_filtro_activo"] = "RevisionPDI"
    with f6:
        if st.button("Ver bloqueadas", use_container_width=True, key="dash_btn_block"):
            st.session_state["dashboard_filtro_activo"] = "Bloqueadas"
    with f7:
        if st.button("Ver hallazgos fábrica", use_container_width=True, key="dash_btn_etapas"):
            st.session_state["dashboard_filtro_activo"] = "ConDesviosFab"
    with f8:
        if st.button("Ver todas", use_container_width=True, key="dash_btn_all"):
            st.session_state["dashboard_filtro_activo"] = "Todas"

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(build_gauge(fab_global, "Cumplimiento fabricación", "Visión directorio"), use_container_width=True)
    with g2:
        st.plotly_chart(build_gauge(pdi_global, "Cumplimiento PDI", "Visión directorio"), use_container_width=True)

    p1 = st.columns(1)[0]
    with p1:
        st.plotly_chart(build_total_fabrication_pie(fab), use_container_width=True)

    e1, e2, e3, e4 = st.columns(4)
    with e1:
        if st.button("Detalle Etapa 1", use_container_width=True, key="dash_stage1"):
            st.session_state["dashboard_filtro_activo"] = "Etapa1"
    with e2:
        if st.button("Detalle Etapa 2", use_container_width=True, key="dash_stage2"):
            st.session_state["dashboard_filtro_activo"] = "Etapa2"
    with e3:
        if st.button("Detalle Etapa 3", use_container_width=True, key="dash_stage3"):
            st.session_state["dashboard_filtro_activo"] = "Etapa3"
    with e4:
        if st.button("Detalle hallazgos fábrica", use_container_width=True, key="dash_hallazgos"):
            st.session_state["dashboard_filtro_activo"] = "ConDesviosFab"

    x1, x2 = st.columns(2)
    with x1:
        estado_exec = plan_exec.groupby("Estado Ejecutivo", as_index=False).size().rename(columns={"size": "Cantidad"})
        fig = px.pie(
            estado_exec,
            names="Estado Ejecutivo",
            values="Cantidad",
            title="Distribución ejecutiva de unidades",
            hole=0.45,
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with x2:
        modelo_estado = plan_exec.groupby(["Modelo", "Estado Ejecutivo"], as_index=False).size().rename(columns={"size": "Cantidad"})
        fig = px.bar(
            modelo_estado,
            x="Modelo",
            y="Cantidad",
            color="Estado Ejecutivo",
            title="Estado ejecutivo por modelo",
            barmode="stack",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    y1, y2 = st.columns(2)
    with y1:
        if not fab_comp.empty:
            fig = px.bar(fab_comp, x="Etapa", y="cumplimiento", title="Cumplimiento por etapa de fabricación")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with y2:
        if not pdi_comp.empty:
            fig = px.bar(pdi_comp, x="Sistema", y="cumplimiento", title="Cumplimiento por sistema PDI")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    filtro_dash = st.session_state.get("dashboard_filtro_activo", "Todas")
    detalle = apply_dashboard_filter(plan_exec, fab, filtro_dash)
    st.markdown(f"### Detalle operativo filtrado: {filtro_dash}")
    if not detalle.empty:
        st.dataframe(
            detalle[["VIN", "Modelo", "PPU", "Estado_Fabricacion", "Estado_PDI", "Liberada", "Estado Ejecutivo", "Motivo operacional"]],
            use_container_width=True,
        )
        if filtro_dash in {"ConDesviosFab", "DesviacionFabrica"} and not fab.empty:
            hall = fab[fab["Unidad_ID"].isin(detalle["Unidad_ID"].tolist())].copy()
            hall = hall[hall["Estado"].isin(["No", "Obs"])]
            if not hall.empty:
                hall = ensure_columns(hall, ["VIN", "Etapa", "Seccion", "Requisito", "Criticidad", "Correccion", "Evidencia", "Resultado_revision_PDI"])[["VIN", "Etapa", "Seccion", "Requisito", "Criticidad", "Correccion", "Evidencia", "Resultado_revision_PDI"]].copy()
                st.markdown("#### Hallazgos de fabricación y evidencia asociada")
                st.dataframe(hall, use_container_width=True)
        if filtro_dash in {"Bloqueadas", "RevisionPDI"} and not pdi.empty:
            pdi_det = pdi[pdi["Unidad_ID"].isin(detalle["Unidad_ID"].tolist())].copy()
            pdi_det = pdi_det[pdi_det["Estado"].isin(["No", "Obs"])]
            if not pdi_det.empty:
                st.markdown("#### Desviaciones abiertas en PDI")
                st.dataframe(
                    pdi_det[["VIN", "Sistema", "Seccion", "Requisito", "Criticidad", "Estado", "Observaciones"]],
                    use_container_width=True,
                )
    else:
        st.info("No hay unidades para el filtro seleccionado.")

def render_trazabilidad():
    st.subheader("🔎 Trazabilidad")
    plan = get_plan()
    if plan.empty:
        st.info("Primero genera la simulación.")
        return

    df_aux = plan.copy()
    df_aux["Label"] = df_aux["VIN"] + " | " + df_aux["Modelo"] + " | " + df_aux["PPU"]
    label = st.selectbox("Seleccionar unidad", df_aux["Label"].tolist())
    unit = df_aux[df_aux["Label"] == label].iloc[0].to_dict()

    st.markdown(
        f"<div class='info-chip'><b>Unidad:</b> {unit['VIN']} | {unit['Modelo']} | {unit['PPU']} "
        f"&nbsp;&nbsp; <b>Fabricación:</b> {unit['Estado_Fabricacion']} "
        f"&nbsp;&nbsp; <b>PDI:</b> {unit['Estado_PDI']} "
        f"&nbsp;&nbsp; <b>Liberada:</b> {unit['Liberada']}</div>",
        unsafe_allow_html=True,
    )

    fab_u = get_fab()
    pdi_u = get_pdi()
    fab_u = fab_u[fab_u["Unidad_ID"] == unit["Unidad_ID"]].copy() if not fab_u.empty else pd.DataFrame()
    pdi_u = pdi_u[pdi_u["Unidad_ID"] == unit["Unidad_ID"]].copy() if not pdi_u.empty else pd.DataFrame()

    tabs = st.tabs(["Fabricación", "PDI", "Resumen"])
    with tabs[0]:
        if fab_u.empty:
            st.info("Sin registros de fabricación.")
        else:
            st.dataframe(fab_u.sort_values(["Etapa", "Seccion"]), use_container_width=True)
    with tabs[1]:
        if pdi_u.empty:
            st.info("Sin registros de PDI.")
        else:
            st.dataframe(pdi_u.sort_values(["Sistema", "Seccion"]), use_container_width=True)
    with tabs[2]:
        n_dev_fab = len(fab_u[fab_u["Estado"].isin(["No", "Obs"])]) if not fab_u.empty else 0
        n_pend = len(pending_rechecks_for_pdi(unit["Unidad_ID"]))
        n_dev_pdi = len(pdi_u[pdi_u["Estado"].isin(["No", "Obs"])]) if not pdi_u.empty else 0

        c1, c2, c3 = st.columns(3)
        with c1:
            card("Desviaciones fábrica", fmt_num(n_dev_fab), "bg-yellow")
        with c2:
            card("Pendientes revisión Chile", fmt_num(n_pend), "bg-red" if n_pend else "bg-green")
        with c3:
            card("Desviaciones PDI", fmt_num(n_dev_pdi), "bg-red" if n_dev_pdi else "bg-green")

# =========================================================
# APP
# =========================================================
load_checklists()
menu = st.radio("", ["📦 Simulación", "🏭 Fabricación", "🛠️ PDI", "📊 Dashboard", "🔎 Trazabilidad"], horizontal=True)
st.session_state["_current_menu"] = menu
refresh_plan_status()

if menu == "📦 Simulación":
    render_simulacion()
elif menu == "🏭 Fabricación":
    render_fabricacion()
elif menu == "🛠️ PDI":
    render_pdi()
elif menu == "📊 Dashboard":
    render_dashboard()
else:
    render_trazabilidad()
