import streamlit as st
import pandas as pd
import yaml
import os

# ---- Config página ----
st.set_page_config(
    page_title='Grupo Muya · Dashboard',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ---- Estilos ----
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #F0F2F5; }
[data-testid="stSidebar"] { background: #fff; border-right: .5px solid #E2E5EA; }
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
.metric-card {
    background: #fff; border: .5px solid #E2E5EA; border-radius: 12px;
    padding: 14px 16px; height: 100%;
}
.metric-card.accent { border-top: 3px solid #F5C842; }
.metric-card.normal { border-top: 3px solid #1A2B3C; }
.metric-card.liq { border-top: 3px solid #2D4A63; }
.metric-label { font-size: 11px; color: #8E9AAF; margin-bottom: 2px; }
.metric-sub { font-size: 10px; color: #8E9AAF; margin-bottom: 8px; font-style: italic; }
.metric-value { font-size: 22px; font-weight: 500; color: #1A2B3C; line-height: 1.1; margin-bottom: 6px; }
.metric-var { font-size: 11px; display: flex; align-items: center; gap: 6px; }
.badge { display: inline-block; font-size: 10px; font-weight: 500; padding: 2px 7px; border-radius: 20px; }
.badge-up { background: #EAF3DE; color: #27500A; }
.badge-down { background: #FCEBEB; color: #791F1F; }
.badge-neutral { background: #F1EFE8; color: #444441; }
.prog-track { height: 4px; border-radius: 2px; background: #E2E5EA; overflow: hidden; margin: 8px 0 4px; }
.prog-fill { height: 100%; border-radius: 2px; transition: width .4s; }
.tar-card {
    background: #fff; border: .5px solid #E2E5EA;
    border-left: 3px solid #8E9AAF; border-radius: 0 12px 12px 0;
    padding: 14px 16px; height: 100%;
}
.tar-card.alerta { border-left-color: #EA4335; border-color: #EA4335; }
.tar-card.liq { border-left-color: #2D4A63; }
.section-header {
    font-size: 11px; font-weight: 600; color: #8E9AAF;
    text-transform: uppercase; letter-spacing: .07em;
    padding-bottom: 6px; border-bottom: .5px solid #E2E5EA;
    margin-bottom: 12px;
}
.level-header {
    display: flex; align-items: center; gap: 10px; margin-bottom: 16px;
}
.level-bar { width: 3px; height: 20px; background: #F5C842; border-radius: 2px; }
.level-title { font-size: 11px; font-weight: 600; color: #1A2B3C; text-transform: uppercase; letter-spacing: .07em; }
.level-sub { font-size: 11px; color: #8E9AAF; }
.meta-pending { font-size: 10px; background: #FAEEDA; color: #633806; padding: 2px 10px; border-radius: 20px; }
div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ---- Imports módulos ----
import sys
sys.path.insert(0, os.path.dirname(__file__))
from modules.loader import cargar_datos, cargar_metas
from modules.filters import render_sidebar, aplicar_filtros
from modules.kpis import calcular_kpis, color_semaforo
from modules import charts, tables

# ---- Cargar config ----
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)

moneda = cfg['empresa']['moneda']

# ---- Cargar datos ----
with st.spinner('Cargando datos...'):
    df = cargar_datos('data/DATA_ACTIVOS_2026.xlsx')
    metas = cargar_metas('data/metas.xlsx')

# ---- Sidebar / Filtros ----
with st.sidebar:
    try:
        st.image('assets/GM_Logotipo2401.jpg', width=160)
    except Exception:
        st.markdown("### Grupo Muya")
    st.markdown("---")

filtros = render_sidebar(df)
df_act, df_comp = aplicar_filtros(df, filtros)
kpis = calcular_kpis(df_act, df_comp, metas, filtros, cfg)

# ---- HEADER ----
col_h1, col_h2, col_h3 = st.columns([3, 2, 1])
with col_h1:
    periodo = f"{filtros['mes_lbl']} {filtros['anio']}" if filtros['mes'] else f"Ene–Dic {filtros['anio']}"
    st.markdown(f"""
    <div style='padding:8px 0;'>
        <div style='font-size:18px;font-weight:500;color:#1A2B3C;'>Dashboard Comercial</div>
        <div style='font-size:12px;color:#8E9AAF;'>{periodo} · vs mismo periodo {filtros['anio_comp']}</div>
    </div>""", unsafe_allow_html=True)
with col_h3:
    st.markdown(f"""
    <div style='text-align:right;padding-top:8px;'>
        <div style='font-size:11px;color:#8E9AAF;'>Mostrando</div>
        <div style='font-size:14px;font-weight:500;color:#1A2B3C;'>{kpis['n_contratos']:,} contratos</div>
        <div style='font-size:10px;color:#8E9AAF;'>{kpis['n_lineas']:,} líneas</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ================================================================
# NIVEL 1 — EJECUTIVO
# ================================================================
st.markdown("""<div class='level-header'>
    <div class='level-bar'></div>
    <span class='level-title'>Nivel 1 · Vista ejecutiva</span>
</div>""", unsafe_allow_html=True)

st.markdown("<div class='section-header'>Fila A — KPIs principales</div>", unsafe_allow_html=True)


def badge_var(val, unit='%', pp=False):
    if val is None:
        return ''
    sym = '▲' if val > 0 else '▼'
    cls = 'badge-up' if val > 0 else 'badge-down'
    label = f"{sym} {abs(val):.1f}{'pp' if pp else unit}"
    return f"<span class='badge {cls}'>{label}</span>"


def progreso_html(actual, meta, umbrales):
    if not meta or meta == 0:
        return "<div style='font-size:10px;color:#8E9AAF;margin-top:8px;'>Meta pendiente</div>"
    pct = min(actual / meta * 100, 100)
    color = color_semaforo(pct, umbrales)
    return f"""
    <div class='prog-track'>
        <div class='prog-fill' style='width:{pct:.1f}%;background:{color};'></div>
    </div>
    <div style='display:flex;justify-content:space-between;'>
        <span style='font-size:10px;color:#8E9AAF;'>{pct:.1f}% de meta</span>
        <span style='font-size:10px;color:#8E9AAF;'>{moneda} {meta:,.0f}</span>
    </div>"""


cols_kpi = st.columns(6)

# KPI-01
with cols_kpi[0]:
    st.markdown(f"""<div class='metric-card accent'>
    <div class='metric-label'>Ventas totales</div>
    <div class='metric-sub'>Todas las líneas</div>
    <div class='metric-value'>{moneda} {kpis['vta_total']/1e6:.2f}M</div>
    <div class='metric-var'>{badge_var(kpis['vta_total_var'])} <span style='font-size:10px;color:#8E9AAF;'>vs {filtros['anio_comp']}</span></div>
    {progreso_html(kpis['vta_total'], kpis['meta_vta'], kpis)}
    </div>""", unsafe_allow_html=True)

# KPI-02
with cols_kpi[1]:
    st.markdown(f"""<div class='metric-card normal'>
    <div class='metric-label'>Ventas DDUU</div>
    <div class='metric-sub'>Solo Derecho de Uso</div>
    <div class='metric-value'>{moneda} {kpis['vta_dduu']/1e6:.2f}M</div>
    <div class='metric-var'>{badge_var(kpis['vta_dduu_var'])} <span style='font-size:10px;color:#8E9AAF;'>vs {filtros['anio_comp']}</span></div>
    {progreso_html(kpis['vta_dduu'], kpis['meta_dduu'], kpis)}
    </div>""", unsafe_allow_html=True)

# KPI-03
with cols_kpi[2]:
    st.markdown(f"""<div class='metric-card normal'>
    <div class='metric-label'>Contratos</div>
    <div class='metric-sub'>Contratos únicos</div>
    <div class='metric-value'>{kpis['contratos']:,}</div>
    <div class='metric-var'>{badge_var(kpis['contratos_var'])} <span style='font-size:10px;color:#8E9AAF;'>vs {filtros['anio_comp']}</span></div>
    {progreso_html(kpis['contratos'], kpis['meta_contratos'], kpis)}
    </div>""", unsafe_allow_html=True)

# KPI-04
with cols_kpi[3]:
    st.markdown(f"""<div class='metric-card normal'>
    <div class='metric-label'>Precio medio</div>
    <div class='metric-sub'>DDUU únicamente</div>
    <div class='metric-value'>{moneda} {kpis['precio_medio']:,.0f}</div>
    <div class='metric-var'>{badge_var(kpis['precio_medio_var'])} <span style='font-size:10px;color:#8E9AAF;'>vs {filtros['anio_comp']}</span></div>
    {progreso_html(kpis['precio_medio'], kpis['meta_pm'], kpis)}
    </div>""", unsafe_allow_html=True)

# KPI-05
with cols_kpi[4]:
    st.markdown(f"""<div class='metric-card normal'>
    <div class='metric-label'>% Inicial real</div>
    <div class='metric-sub'>CUI pagada / Venta</div>
    <div class='metric-value'>{kpis['pct_inicial']:.1f}%</div>
    <div class='metric-var'>{badge_var(kpis['pct_inicial_var'], pp=True)} <span style='font-size:10px;color:#8E9AAF;'>vs {filtros['anio_comp']}</span></div>
    {progreso_html(kpis['pct_inicial'], kpis['meta_ini'] if kpis['meta_ini'] else None, kpis)}
    </div>""", unsafe_allow_html=True)

# KPI-06 (% Logro — solo si hay meta)
with cols_kpi[5]:
    if kpis['pct_logro_dduu'] is not None:
        logro = kpis['pct_logro_dduu']
        color_logro = color_semaforo(logro, kpis)
        st.markdown(f"""<div class='metric-card normal'>
        <div class='metric-label'>% Logro DDUU</div>
        <div class='metric-sub'>Avance sobre meta</div>
        <div class='metric-value' style='color:{color_logro};'>{logro:.1f}%</div>
        <div class='metric-var'><span style='font-size:11px;color:{color_logro};font-weight:500;'>{"✓ En meta" if logro >= 75 else "⚠ Atención" if logro >= 50 else "✗ Crítico"}</span></div>
        {progreso_html(kpis['vta_dduu'], kpis['meta_dduu'], kpis)}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class='metric-card' style='border-top:3px dashed #E2E5EA;background:#F8F9FA;
            display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;min-height:120px;'>
            <div style='font-size:11px;color:#8E9AAF;text-align:center;'>% Logro DDUU</div>
            <div style='font-size:11px;color:#8E9AAF;text-align:center;margin-top:6px;'>Se activa al cargar<br>meta DDUU</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---- FILA B: TARJETAS ----
st.markdown("<div class='section-header'>Fila B — Tarjetas de contexto</div>", unsafe_allow_html=True)
cols_tar = st.columns(5)

# TAR-01: Descuento
with cols_tar[0]:
    dscto_alerta = kpis['dscto_pct'] > kpis['dscto_critico']
    dscto_warn = kpis['dscto_pct'] > kpis['dscto_umbral']
    cls = 'alerta' if dscto_alerta else ''
    color_d = '#EA4335' if dscto_alerta else '#FBBC04' if dscto_warn else '#8E9AAF'
    msg = '⚠ Supera umbral crítico' if dscto_alerta else '⚠ Supera umbral' if dscto_warn else 'Dentro de umbral'
    st.markdown(f"""<div class='tar-card {cls}' style='border-left-color:{color_d};'>
    <div class='metric-label' style='color:{color_d};font-weight:500;'>Descuento aplicado</div>
    <div class='metric-value' style='font-size:18px;color:{color_d};'>{moneda} {kpis['dscto_monto']:,.0f}</div>
    <div style='font-size:12px;color:#8E9AAF;'>{kpis['dscto_pct']:.1f}% sobre VTA total</div>
    <div style='font-size:10px;color:{color_d};margin-top:6px;'>{msg}</div>
    </div>""", unsafe_allow_html=True)

# TAR-02: Carencia
with cols_tar[1]:
    cls = 'alerta' if kpis['carencia_no'] > 0 else ''
    color_c = '#EA4335' if kpis['carencia_no'] > 0 else '#34A853'
    st.markdown(f"""<div class='tar-card {cls}' style='border-left-color:{color_c};'>
    <div class='metric-label' style='color:{color_c};font-weight:500;'>Sin carencia</div>
    <div class='metric-value' style='font-size:18px;color:{color_c};'>{kpis['carencia_no']} contrato{'s' if kpis['carencia_no']!=1 else ''}</div>
    <div style='font-size:12px;color:#8E9AAF;'>{kpis['carencia_pct']:.2f}% sobre total</div>
    </div>""", unsafe_allow_html=True)

# TAR-03: CUI partida
with cols_tar[2]:
    st.markdown(f"""<div class='tar-card'>
    <div class='metric-label'>CUI partida</div>
    <div class='metric-value' style='font-size:18px;'>{kpis['cui_count']} contratos</div>
    <div style='font-size:12px;color:#8E9AAF;'>{moneda} {kpis['cui_vta']:,.0f} VTA</div>
    <div style='font-size:10px;color:#8E9AAF;margin-top:4px;'>{kpis['cui_pct_c']:.1f}% contratos · {kpis['cui_pct_v']:.1f}% VTA</div>
    </div>""", unsafe_allow_html=True)

# TAR-04: Financiamiento
with cols_tar[3]:
    plazo_color = '#EA4335' if kpis['plazo_medio'] > kpis['meta_plazo'] and kpis['meta_plazo'] else '#1A2B3C'
    st.markdown(f"""<div class='tar-card'>
    <div class='metric-label'>Financiamiento</div>
    <div class='metric-value' style='font-size:18px;color:{plazo_color};'>{kpis['plazo_medio']:.1f} meses</div>
    <div style='font-size:12px;color:#8E9AAF;'>plazo medio</div>
    <div style='font-size:10px;color:#8E9AAF;margin-top:4px;font-style:italic;'>imp_cuota es referencial · no refleja caja real</div>
    </div>""", unsafe_allow_html=True)

# TAR-05: Liquidez
with cols_tar[4]:
    var_liq = kpis['liquidez_pct_var']
    st.markdown(f"""<div class='tar-card liq'>
    <div class='metric-label' style='color:#2D4A63;font-weight:500;'>Liquidez del periodo</div>
    <div style='display:flex;align-items:baseline;gap:8px;'>
        <div class='metric-value' style='font-size:17px;color:#2D4A63;'>{moneda} {kpis['liquidez_monto']:,.0f}</div>
        <span style='font-size:16px;font-weight:500;color:#2D4A63;'>{kpis['liquidez_pct']:.1f}%</span>
    </div>
    <div style='font-size:11px;color:#8E9AAF;'>caja real sobre VTA total</div>
    <div class='prog-track'><div class='prog-fill' style='width:{min(kpis["liquidez_pct"],100):.1f}%;background:#2D4A63;'></div></div>
    <div style='font-size:10px;color:#8E9AAF;'>CUI: {kpis['liquidez_cui_pct']:.1f}% · Contado: {kpis['liquidez_cnt_pct']:.1f}%</div>
    <div style='margin-top:6px;'>{badge_var(var_liq, pp=True)} <span style='font-size:10px;color:#8E9AAF;'>vs {filtros['anio_comp']}</span></div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---- FILA C: MIX ----
st.markdown("<div class='section-header'>Fila C — Mix rápido</div>", unsafe_allow_html=True)
cols_mix = st.columns(3)

with cols_mix[0]:
    st.markdown(f"""<div class='metric-card' style='border:0.5px solid #E2E5EA;'>
    <div style='font-size:10px;color:#8E9AAF;font-weight:500;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>Mix NF / NI</div>
    <div style='display:flex;align-items:center;gap:8px;'>
        <div style='flex:1;text-align:center;'>
            <div style='font-size:22px;font-weight:500;color:#1A2B3C;'>{kpis['pct_nf']:.1f}%</div>
            <div style='font-size:11px;color:#8E9AAF;'>NF</div>
        </div>
        <div style='width:1px;background:#E2E5EA;height:40px;'></div>
        <div style='flex:1;text-align:center;'>
            <div style='font-size:22px;font-weight:500;color:#8E9AAF;'>{kpis['pct_ni']:.1f}%</div>
            <div style='font-size:11px;color:#8E9AAF;'>NI</div>
        </div>
    </div>
    <div class='prog-track' style='height:6px;border-radius:3px;margin-top:12px;'>
        <div class='prog-fill' style='width:{kpis["pct_nf"]:.1f}%;background:#1A2B3C;border-radius:3px;'></div>
    </div>
    </div>""", unsafe_allow_html=True)

with cols_mix[1]:
    st.markdown(f"""<div class='metric-card' style='border:0.5px solid #E2E5EA;'>
    <div style='font-size:10px;color:#8E9AAF;font-weight:500;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>% Integrales</div>
    <div style='font-size:22px;font-weight:500;color:#1A2B3C;'>{kpis['pct_integrales']:.1f}%</div>
    <div style='font-size:11px;color:#8E9AAF;margin-top:4px;'>de contratos DDUU son integrales</div>
    </div>""", unsafe_allow_html=True)

with cols_mix[2]:
    sede_sel = filtros['sede']
    mostrar_inh = sede_sel in ('Todas', 'PIU', 'LUR')
    if mostrar_inh:
        st.markdown(f"""<div class='metric-card' style='border:0.5px solid #E2E5EA;'>
        <div style='font-size:10px;color:#8E9AAF;font-weight:500;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>Serv. Inhumación · PIU / LUR</div>
        <div style='font-size:22px;font-weight:500;color:#1A2B3C;'>{kpis['inh_count']}</div>
        <div style='font-size:11px;color:#8E9AAF;margin-top:4px;'>contratos · {moneda} {kpis['inh_vta']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ================================================================
# NIVEL 2 — ANALÍTICO
# ================================================================
st.markdown("""<div class='level-header'>
    <div class='level-bar'></div>
    <span class='level-title'>Nivel 2 · Vista analítica</span>
</div>""", unsafe_allow_html=True)

# --- Sección A: Evolución temporal ---
st.markdown("<div class='section-header'>Sección A — Evolución temporal</div>", unsafe_allow_html=True)

metrica_opts = {'VTA Total': 'vta_total', 'VTA DDUU': 'vta_dduu', 'Contratos': 'contratos', 'Precio Medio': 'precio_medio'}
metrica_sel = st.radio('Ver en gráfico de líneas:', list(metrica_opts.keys()), horizontal=True, key='metrica_evol')

col_g1, col_g2 = st.columns([2, 1])
with col_g1:
    fig01 = charts.graf01_evolucion_ventas(df_act, df_comp, filtros, metrica_opts[metrica_sel])
    st.plotly_chart(fig01, use_container_width=True)
with col_g2:
    fig04 = charts.graf04_plazo_historico(df)
    st.plotly_chart(fig04, use_container_width=True)

# --- Sección B: Comparativas ---
st.markdown("<div class='section-header'>Sección B — Comparativas</div>", unsafe_allow_html=True)

col_g5, col_g6 = st.columns(2)
with col_g5:
    fig05 = charts.graf05_ventas_sede(df_act, df_comp, filtros)
    st.plotly_chart(fig05, use_container_width=True)
with col_g6:
    tn_canal = st.radio('Tipo necesidad:', ['TODOS', 'NF', 'NI'], horizontal=True, key='tn_canal')
    fig06 = charts.graf06_canal(df_act, tn_canal)
    st.plotly_chart(fig06, use_container_width=True)

col_g7, col_g9 = st.columns(2)
with col_g7:
    fig07 = charts.graf07_mix_nf_ni(df_act)
    st.plotly_chart(fig07, use_container_width=True)
with col_g9:
    tipo_zona = st.selectbox('Producto:', ['Todos', 'SEPULTURA', 'NICHO', 'CREMACION'], key='tipo_zona')
    fig09 = charts.graf09_zonas(df_act, tipo_zona)
    st.plotly_chart(fig09, use_container_width=True)

# --- GRAF-08: Ranking jefes ---
st.markdown("<div class='section-header'>Ranking jefes de ventas — DDUU</div>", unsafe_allow_html=True)
fig08 = charts.graf08_ranking_jefes(df_act)
st.plotly_chart(fig08, use_container_width=True)

st.markdown("---")

# ================================================================
# NIVEL 3 — OPERATIVO
# ================================================================
st.markdown("""<div class='level-header'>
    <div class='level-bar'></div>
    <span class='level-title'>Nivel 3 · Vista operativa</span>
</div>""", unsafe_allow_html=True)

# --- Tabla 7.4: Por tipo de producto ---
st.markdown("<div class='section-header'>Tabla 7.4 — Análisis por tipo de producto</div>", unsafe_allow_html=True)

df74, subtipos = tables.tabla_tipo_producto(df_act)
if not df74.empty:
    tipo_sel = st.selectbox('Ver desglose de:', df74['Tipo'].tolist(), key='tipo74')
    col_74a, col_74b = st.columns([1, 2])
    with col_74a:
        st.dataframe(
            df74[['Tipo', 'Contratos', 'VTA Total', 'Precio Medio', '% VTA']],
            hide_index=True, use_container_width=True,
        )
    with col_74b:
        if tipo_sel in subtipos:
            sub_df = subtipos[tipo_sel]
            sub_disp = sub_df[['Subtipo', 'vta_sub', 'cont_sub', 'pm', 'pct']].copy()
            sub_disp.columns = ['Subtipo', 'VTA', 'Contratos', 'PM', '% dentro']
            sub_disp['VTA'] = sub_disp['VTA'].apply(lambda v: f"S/ {v:,.0f}")
            sub_disp['PM'] = sub_disp['PM'].apply(lambda v: f"S/ {v:,.0f}")
            sub_disp['% dentro'] = sub_disp['% dentro'].apply(lambda v: f"{v:.1f}%")
            st.dataframe(sub_disp, hide_index=True, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Tabla 7.3: Detalle contratos ---
st.markdown("<div class='section-header'>Tabla 7.3 — Detalle de contratos</div>", unsafe_allow_html=True)

col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    filt_linea = st.selectbox('Tipo línea', ['Todos', 'DDUU', 'SSFF', 'Serv. Inh.'], key='f_linea')
with col_f2:
    filt_tn = st.selectbox('Tipo necesidad', ['Todos', 'NF', 'NI'], key='f_tn')
with col_f3:
    filt_pago = st.selectbox('Modalidad pago', ['Todos', 'FINANCIADO', 'CONTADO'], key='f_pago')
with col_f4:
    busqueda = st.text_input('Buscar contrato / vendedor', placeholder='Ej: J. GARCIA o 00001-...', key='busq')

df73 = df_act.copy()
if filt_linea != 'Todos':
    df73 = df73[df73['tipo_linea'] == filt_linea]
if filt_tn != 'Todos':
    df73 = df73[df73['cod_tipo_necesidad'] == filt_tn]
if filt_pago != 'Todos':
    df73 = df73[df73['tipo_pago'] == filt_pago]
if busqueda:
    b = busqueda.upper()
    df73 = df73[
        df73['Localidad-Contrato-Num_ser'].astype(str).str.upper().str.contains(b, na=False) |
        df73['dsc_vendedor'].astype(str).str.upper().str.contains(b, na=False) |
        df73['sede_cod'].astype(str).str.upper().str.contains(b, na=False)
    ]

st.caption(f"Mostrando {len(df73):,} registros · Ordenados por fecha desc")

df73_disp = tables.tabla_contratos(
    df73.sort_values('fecha_venta', ascending=False), cfg
)

# Highlight carencia NO PASO
def highlight_carencia(row):
    if 'Carencia' in row.index and row['Carencia'] == 'NO PASO':
        return ['background-color: #FFF0F0'] * len(row)
    return [''] * len(row)

filas_pg = cfg['tabla_operativa']['filas_por_pagina']
st.dataframe(
    df73_disp.head(filas_pg),
    hide_index=True,
    use_container_width=True,
    height=min(len(df73_disp.head(filas_pg)) * 35 + 50, 600),
)

if len(df73_disp) > filas_pg:
    st.caption(f"Mostrando primeros {filas_pg} de {len(df73_disp):,} registros. Exporta para ver todos.")

col_exp1, col_exp2 = st.columns([1, 5])
with col_exp1:
    csv = df73_disp.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label='Exportar CSV',
        data=csv,
        file_name=f'muya_contratos_{filtros["anio"]}.csv',
        mime='text/csv',
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;font-size:10px;color:#8E9AAF;padding:12px 0;'>"
    "Grupo Muya · Dashboard Comercial · Datos: DATA_ACTIVOS_2026.xlsx · Metas: metas.xlsx"
    "</div>",
    unsafe_allow_html=True,
)
