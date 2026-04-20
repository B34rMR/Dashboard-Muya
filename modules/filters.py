import pandas as pd
import streamlit as st


MESES_LABEL = {
    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
    5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
    9: 'Set', 10: 'Oct', 11: 'Nov', 12: 'Dic',
}
MESES_INV = {v: k for k, v in MESES_LABEL.items()}

SEDES_DISPLAY = ['Todas', 'CUS', 'REE', 'JDL', 'AQP', 'CIX', 'LAM', 'PIU', 'LUR', 'CNT', 'PIS', 'SAN', 'COR', 'CHM']
CANALES = ['Todos', 'FFVV NF', 'FFVV NI', 'SAC', 'TLD', 'Otros']
TIPOS_NEC = ['Todos', 'NF', 'NI']
TIPOS_LINEA = ['Todos', 'DDUU', 'SSFF', 'Serv. Inh.']


def render_sidebar(df: pd.DataFrame) -> dict:
    st.sidebar.markdown(
        """
        <div style='padding:8px 0 16px;'>
            <div style='font-size:10px;font-weight:600;color:#8E9AAF;text-transform:uppercase;
                        letter-spacing:.08em;margin-bottom:12px;'>Nivel 0 · Filtros</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    anios_disp = sorted(df['anio'].dropna().unique().astype(int).tolist(), reverse=True)
    anio_sel = st.sidebar.selectbox('Año', anios_disp, index=0)

    meses_disp_num = sorted(df[df['anio'] == anio_sel]['mes'].dropna().unique().astype(int).tolist())
    meses_disp_lbl = ['Todos'] + [MESES_LABEL[m] for m in meses_disp_num if m in MESES_LABEL]
    mes_sel_lbl = st.sidebar.selectbox('Mes', meses_disp_lbl, index=0)
    mes_sel = None if mes_sel_lbl == 'Todos' else MESES_INV.get(mes_sel_lbl)

    sede_sel = st.sidebar.selectbox('Sede', SEDES_DISPLAY, index=0)

    # Cascada: jefes según sede
    if sede_sel == 'Todas':
        d_sede = df
    elif sede_sel == 'CUS':
        d_sede = df[df['sede_cod'].isin(['REE', 'JDL'])]
    else:
        d_sede = df[df['sede_cod'] == sede_sel]

    jefes_disp = ['Todos'] + sorted(
        d_sede[d_sede['anio'] == anio_sel]['dsc_jefeventas']
        .dropna().unique().tolist()
    )
    jefe_sel = st.sidebar.selectbox('Jefe de ventas', jefes_disp, index=0)

    canal_sel = st.sidebar.selectbox('Canal', CANALES, index=0)
    tn_sel = st.sidebar.selectbox('Tipo de necesidad', TIPOS_NEC, index=0)
    linea_sel = st.sidebar.selectbox('Tipo de línea', TIPOS_LINEA, index=0)

    st.sidebar.divider()

    anios_comp = [a for a in anios_disp if a != anio_sel]
    anio_comp = st.sidebar.selectbox(
        'Año de comparación',
        anios_comp if anios_comp else [anio_sel - 1],
        index=0,
    )

    if st.sidebar.button('Limpiar filtros', use_container_width=True):
        st.rerun()

    return {
        'anio': anio_sel,
        'mes': mes_sel,
        'mes_lbl': mes_sel_lbl,
        'sede': sede_sel,
        'jefe': jefe_sel,
        'canal': canal_sel,
        'tn': tn_sel,
        'linea': linea_sel,
        'anio_comp': anio_comp,
    }


def aplicar_filtros(df: pd.DataFrame, filtros: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    def _filtrar(d, anio, mes, sede, jefe, canal, tn, linea):
        d = d[d['anio'] == anio]
        if mes:
            d = d[d['mes'] == mes]
        if sede != 'Todas':
            if sede == 'CUS':
                d = d[d['sede_cod'].isin(['REE', 'JDL'])]
            else:
                d = d[d['sede_cod'] == sede]
        if jefe != 'Todos':
            d = d[d['dsc_jefeventas'] == jefe]
        if canal != 'Todos':
            d = d[d['canal_clean'] == canal]
        if tn != 'Todos':
            d = d[d['cod_tipo_necesidad'] == tn]
        if linea != 'Todos':
            d = d[d['tipo_linea'] == linea]
        return d

    df_act = _filtrar(
        df,
        filtros['anio'], filtros['mes'], filtros['sede'],
        filtros['jefe'], filtros['canal'], filtros['tn'], filtros['linea'],
    )

    # Periodo de comparación: mismo mes(es) del año de comparación
    df_comp = _filtrar(
        df,
        filtros['anio_comp'], filtros['mes'], filtros['sede'],
        filtros['jefe'], filtros['canal'], filtros['tn'], filtros['linea'],
    )

    return df_act, df_comp
