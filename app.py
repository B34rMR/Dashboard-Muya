import streamlit as st
import pandas as pd
import yaml
import os
import sys

st.set_page_config(
    page_title='Grupo Muya · Dashboard',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded',
)

sys.path.insert(0, os.path.dirname(__file__))
from modules.loader import cargar_datos, cargar_metas
from modules.filters import render_sidebar, aplicar_filtros
from modules.kpis import calcular_kpis, color_semaforo
from modules import charts, tables

# ---- Config ----
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
moneda = cfg['empresa']['moneda']

# ---- CSS mínimo ----
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #F0F2F5; }
[data-testid="stSidebar"] { background: #fff; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ---- Datos ----
with st.spinner('Cargando datos...'):
    df    = cargar_datos('data/DATA_ACTIVOS_2026.xlsx')
    metas = cargar_metas('data/metas.xlsx')

# ---- Sidebar ----
with st.sidebar:
    try:
        st.image('assets/GM_Logotipo2401.jpg', width=160)
    except Exception:
        st.markdown('### Grupo Muya')
    st.markdown('---')

filtros          = render_sidebar(df)
df_act, df_comp  = aplicar_filtros(df, filtros)
kpis             = calcular_kpis(df_act, df_comp, metas, filtros, cfg)

# ---- HEADER ----
c1, c2, c3 = st.columns([3, 2, 1])
with c1:
    periodo = (f"{filtros['mes_lbl']} {filtros['anio']}"
               if filtros['mes'] else f"Ene–Dic {filtros['anio']}")
    st.markdown(f"## Dashboard Comercial")
    st.caption(f"{periodo} · vs mismo periodo {filtros['anio_comp']}")
with c3:
    st.metric('Contratos', f"{kpis['n_contratos']:,}")
    st.caption(f"{kpis['n_lineas']:,} líneas")

st.divider()

# ================================================================
# NIVEL 1 — EJECUTIVO
# ================================================================
st.markdown('### Nivel 1 · Vista ejecutiva')
st.caption('Fila A — KPIs principales')

def var_str(val, pp=False):
    if val is None: return ''
    sym = '▲' if val > 0 else '▼'
    unit = 'pp' if pp else '%'
    return f"{sym} {abs(val):.1f}{unit}"

def meta_str(actual, meta):
    if not meta or meta == 0:
        return 'Meta pendiente'
    pct = actual / meta * 100
    return f"{pct:.1f}% de meta · {moneda} {meta:,.0f}"

# KPIs fila A
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric(
        label='Ventas totales',
        value=f"{moneda} {kpis['vta_total']/1e6:.2f}M",
        delta=var_str(kpis['vta_total_var']),
        help='Todas las líneas'
    )
    st.caption(meta_str(kpis['vta_total'], kpis['meta_vta']))

with k2:
    st.metric(
        label='Ventas DDUU',
        value=f"{moneda} {kpis['vta_dduu']/1e6:.2f}M",
        delta=var_str(kpis['vta_dduu_var']),
        help='Solo Derecho de Uso'
    )
    st.caption(meta_str(kpis['vta_dduu'], kpis['meta_dduu']))

with k3:
    st.metric(
        label='Contratos únicos',
        value=f"{kpis['contratos']:,}",
        delta=var_str(kpis['contratos_var']),
    )
    st.caption(meta_str(kpis['contratos'], kpis['meta_contratos']))

with k4:
    st.metric(
        label='Precio medio DDUU',
        value=f"{moneda} {kpis['precio_medio']:,.0f}",
        delta=var_str(kpis['precio_medio_var']),
    )
    st.caption(meta_str(kpis['precio_medio'], kpis['meta_pm']))

with k5:
    st.metric(
        label='% Inicial real',
        value=f"{kpis['pct_inicial']:.1f}%",
        delta=var_str(kpis['pct_inicial_var'], pp=True),
        help='SUM(CUI_PAGADA) / SUM(VTA)'
    )
    st.caption(meta_str(kpis['pct_inicial'], kpis['meta_ini']))

with k6:
    if kpis['pct_logro_dduu'] is not None:
        st.metric(
            label='% Logro DDUU',
            value=f"{kpis['pct_logro_dduu']:.1f}%",
            delta='✓ En meta' if kpis['pct_logro_dduu'] >= 75
                  else '⚠ Atención' if kpis['pct_logro_dduu'] >= 50 else '✗ Crítico',
        )
    else:
        st.info('% Logro DDUU\nSe activa al cargar meta')

st.markdown('---')
st.caption('Fila B — Tarjetas de contexto')

t1, t2, t3, t4, t5 = st.columns(5)

with t1:
    alerta = '🔴' if kpis['dscto_pct'] > kpis['dscto_critico'] else '🟡' if kpis['dscto_pct'] > kpis['dscto_umbral'] else '🟢'
    st.metric('Descuento aplicado',
              f"{moneda} {kpis['dscto_monto']:,.0f}",
              f"{alerta} {kpis['dscto_pct']:.1f}% sobre VTA")

with t2:
    color = '🔴' if kpis['carencia_no'] > 0 else '🟢'
    st.metric('Sin carencia',
              f"{kpis['carencia_no']} contrato{'s' if kpis['carencia_no'] != 1 else ''}",
              f"{color} {kpis['carencia_pct']:.2f}% del total")

with t3:
    st.metric('CUI partida',
              f"{kpis['cui_count']} contratos",
              f"{moneda} {kpis['cui_vta']:,.0f} VTA")
    st.caption(f"{kpis['cui_pct_c']:.1f}% ctr · {kpis['cui_pct_v']:.1f}% VTA")

with t4:
    st.metric('Financiamiento',
              f"{kpis['plazo_medio']:.1f} meses",
              'plazo medio')
    st.caption('imp_cuota es referencial — no es caja real')

with t5:
    var_liq = kpis['liquidez_pct_var']
    sym = '▲' if var_liq > 0 else '▼'
    st.metric('Liquidez del periodo',
              f"{moneda} {kpis['liquidez_monto']:,.0f}",
              f"{sym} {abs(var_liq):.1f}pp vs {filtros['anio_comp']}")
    st.caption(f"{kpis['liquidez_pct']:.1f}% caja real · "
               f"CUI {kpis['liquidez_cui_pct']:.1f}% · "
               f"Ctdo {kpis['liquidez_cnt_pct']:.1f}%")

st.markdown('---')
st.caption('Fila C — Mix rápido')

m1, m2, m3 = st.columns(3)
with m1:
    st.metric('Mix NF / NI',
              f"NF {kpis['pct_nf']:.1f}%",
              f"NI {kpis['pct_ni']:.1f}%")
with m2:
    st.metric('% Integrales',
              f"{kpis['pct_integrales']:.1f}%",
              'de contratos DDUU')
with m3:
    if filtros['sede'] in ('Todas', 'PIU', 'LUR'):
        st.metric('Serv. Inhumación',
                  f"{kpis['inh_count']} contratos",
                  f"{moneda} {kpis['inh_vta']:,.0f} · PIU/LUR")

st.divider()

# ================================================================
# NIVEL 2 — ANALÍTICO
# ================================================================
st.markdown('### Nivel 2 · Vista analítica')

st.caption('Sección A — Evolución temporal')
metrica_opts = {
    'VTA Total': 'vta_total',
    'VTA DDUU': 'vta_dduu',
    'Contratos': 'contratos',
    'Precio Medio': 'precio_medio'
}
metrica_sel = st.radio('Ver:', list(metrica_opts.keys()), horizontal=True)

col_g1, col_g2 = st.columns([2, 1])
with col_g1:
    st.plotly_chart(
        charts.graf01_evolucion_ventas(df_act, df_comp, filtros, metrica_opts[metrica_sel]),
        use_container_width=True
    )
with col_g2:
    st.plotly_chart(
        charts.graf04_plazo_historico(df),
        use_container_width=True
    )

st.caption('Sección B — Comparativas')

col_g5, col_g6 = st.columns(2)
with col_g5:
    st.plotly_chart(charts.graf05_ventas_sede(df_act, df_comp, filtros),
                    use_container_width=True)
with col_g6:
    tn_canal = st.radio('Tipo necesidad:', ['TODOS', 'NF', 'NI'],
                        horizontal=True, key='tn_canal')
    st.plotly_chart(charts.graf06_canal(df_act, tn_canal),
                    use_container_width=True)

col_g7, col_g9 = st.columns(2)
with col_g7:
    st.plotly_chart(charts.graf07_mix_nf_ni(df_act), use_container_width=True)
with col_g9:
    tipo_zona = st.selectbox('Producto:', ['Todos', 'SEPULTURA', 'NICHO', 'CREMACION'])
    st.plotly_chart(charts.graf09_zonas(df_act, tipo_zona), use_container_width=True)

st.plotly_chart(charts.graf08_ranking_jefes(df_act), use_container_width=True)

st.divider()

# ================================================================
# NIVEL 3 — OPERATIVO
# ================================================================
st.markdown('### Nivel 3 · Vista operativa')

# Tabla 7.4
st.caption('Tabla 7.4 — Por tipo de producto')
df74, subtipos = tables.tabla_tipo_producto(df_act)
if not df74.empty:
    col_a, col_b = st.columns([1, 2])
    with col_a:
        tipo_sel = st.selectbox('Ver desglose:', df74['Tipo'].tolist())
        st.dataframe(df74[['Tipo','Contratos','VTA Total','Precio Medio','% VTA']],
                     hide_index=True, use_container_width=True)
    with col_b:
        if tipo_sel in subtipos:
            sub = subtipos[tipo_sel].copy()
            sub_disp = sub[['Subtipo','vta_sub','cont_sub','pm','pct']].copy()
            sub_disp.columns = ['Subtipo','VTA','Contratos','PM','% dentro']
            sub_disp['VTA'] = sub_disp['VTA'].apply(lambda v: f"S/ {v:,.0f}")
            sub_disp['PM']  = sub_disp['PM'].apply(lambda v: f"S/ {v:,.0f}")
            sub_disp['% dentro'] = sub_disp['% dentro'].apply(lambda v: f"{v:.1f}%")
            st.dataframe(sub_disp, hide_index=True, use_container_width=True)

st.markdown('---')

# Tabla 7.3
st.caption('Tabla 7.3 — Detalle de contratos')
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    f_linea = st.selectbox('Tipo línea', ['Todos','DDUU','SSFF','Serv. Inh.'])
with fc2:
    f_tn    = st.selectbox('Tipo necesidad', ['Todos','NF','NI'])
with fc3:
    f_pago  = st.selectbox('Pago', ['Todos','FINANCIADO','CONTADO'])
with fc4:
    busq    = st.text_input('Buscar contrato / vendedor', placeholder='Ej: J. GARCIA')

df73 = df_act.copy()
if f_linea != 'Todos': df73 = df73[df73['tipo_linea'] == f_linea]
if f_tn    != 'Todos': df73 = df73[df73['cod_tipo_necesidad'] == f_tn]
if f_pago  != 'Todos': df73 = df73[df73['tipo_pago'] == f_pago]
if busq:
    b = busq.upper()
    df73 = df73[
        df73['Localidad-Contrato-Num_ser'].astype(str).str.upper().str.contains(b, na=False) |
        df73['dsc_vendedor'].astype(str).str.upper().str.contains(b, na=False) |
        df73['sede_cod'].astype(str).str.upper().str.contains(b, na=False)
    ]

st.caption(f"Mostrando {len(df73):,} registros · ordenados por fecha desc")

df73_disp = tables.tabla_contratos(
    df73.sort_values('fecha_venta', ascending=False), cfg
)

pg = cfg['tabla_operativa']['filas_por_pagina']
st.dataframe(df73_disp.head(pg), hide_index=True,
             use_container_width=True,
             height=min(len(df73_disp.head(pg)) * 35 + 50, 600))

if len(df73_disp) > pg:
    st.caption(f"Mostrando primeros {pg} de {len(df73_disp):,}. Exporta para ver todos.")

csv = df73_disp.to_csv(index=False).encode('utf-8-sig')
st.download_button('Exportar CSV', data=csv,
                   file_name=f"muya_{filtros['anio']}.csv", mime='text/csv')

st.caption('Grupo Muya · Dashboard Comercial · DATA_ACTIVOS_2026.xlsx')
