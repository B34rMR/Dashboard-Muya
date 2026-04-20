import pandas as pd
import numpy as np
import streamlit as st

SEDE_MAP = {
    'SEDE SAN ANTONIO': 'SAN', 'SEDE CORONA DEL FRAILE': 'COR',
    'SEDE CUSCO I': 'REE', 'SEDE CUSCO II': 'JDL',
    'SEDE AREQUIPA': 'AQP', 'SEDE CHICLAYO': 'CIX',
    'SEDE LAMBAYEQUE': 'LAM', 'SEDE CAÑETE': 'CNT',
    'SEDE PISCO': 'PIS', 'SEDE PIURA': 'PIU',
    'SEDE LURIN': 'LUR', 'SEDE CHIMBOTE': 'CHM',
}

ZONAS_VALIDAS = {'ZONA A', 'ZONA B', 'ZONA C', 'ZONA M', 'ZONA MM', 'SIN ZONA'}
CANAL_MAP = {
    'TELEDIGITAL': 'TLD', 'SAC-PARQ-ADM': 'SAC',
    'FFVV NF': 'FFVV NF', 'FFVV NI': 'FFVV NI',
    1: 'Otros', 0: 'Otros', '1': 'Otros', '0': 'Otros',
}


def _tipo_producto_clean(tipo):
    if pd.isna(tipo):
        return tipo
    t = str(tipo).upper().strip()
    if t in ('NICHOS', 'NICHO DOBLE', 'NICHO TRIPLE', 'NICHO CUADRUPLE'):
        return 'NICHO'
    return t


def _capacidad_nicho(tipo, subtipo):
    tipo = str(tipo).upper().strip() if pd.notna(tipo) else ''
    subtipo = str(subtipo).upper().strip() if pd.notna(subtipo) else ''
    if tipo == 'NICHOS':
        for c in ('CUADRUPLE', 'TRIPLE', 'DOBLE', 'SIMPLE'):
            if c in subtipo:
                return c
        return 'SIMPLE'
    elif tipo == 'NICHO DOBLE':
        return 'DOBLE'
    elif tipo == 'NICHO TRIPLE':
        return 'TRIPLE'
    elif tipo == 'NICHO CUADRUPLE':
        return 'CUADRUPLE'
    elif tipo == 'NICHO':
        for c in ('CUADRUPLE', 'TRIPLE', 'DOBLE'):
            if c in subtipo:
                return c
        return 'SIMPLE'
    return ''


def _fila_nicho(tipo, subtipo):
    tipo = str(tipo).upper().strip() if pd.notna(tipo) else ''
    subtipo = str(subtipo).upper().strip() if pd.notna(subtipo) else ''
    for fila in ('FILA A', 'FILA B', 'FILA C', 'FILA D', 'FILA E', 'FILA F'):
        if fila in subtipo:
            return fila
    return 'SIN FILA'


@st.cache_data(show_spinner=False)
def cargar_datos(ruta: str) -> pd.DataFrame:
    df = pd.read_excel(ruta)

    # --- Exclusiones permanentes ---
    df = df[df['dsc_tipo_venta'] != 'DONACION']
    df = df[df['TIPO PRODUCTO'] != 'SIN NIVELES']
    mask_sa = (
        (df['Dsc_tipo_Serv'] == 'SERVICIOS ADICIONALES') &
        ~((df['flg_derecho_inhumacion'] == 'SI') & (df['cod_tipo_necesidad'] == 'NF'))
    )
    df = df[~mask_sa]
    mask_crem = (df['TIPO PRODUCTO'] == 'CREMACION') & (df['Dsc_tipo_Serv'] != 'DERECHO DE USO')
    df = df[~mask_crem]

    # --- Fechas ---
    df['fch_activacion'] = pd.to_datetime(df['fch_activacion'], errors='coerce')
    df['fch_generacion'] = pd.to_datetime(df['fch_generacion'], errors='coerce')

    def _fecha_venta(row):
        if row['cod_tipo_necesidad'] == 'NF':
            return row['fch_activacion']
        return row['fch_generacion']

    df['fecha_venta'] = df.apply(_fecha_venta, axis=1)
    df['anio'] = df['fecha_venta'].dt.year
    df['mes'] = df['fecha_venta'].dt.month
    df['fecha_str'] = df['fecha_venta'].dt.strftime('%d/%m/%Y')

    # --- Sede ---
    df['sede_cod'] = df['dsc_localidad'].map(SEDE_MAP).fillna('OTR')

    # --- Canal ---
    df['canal_clean'] = df['dsc_canal'].map(CANAL_MAP).fillna(
        df['dsc_canal'].apply(lambda x: 'Otros' if pd.isna(x) else str(x))
    )

    # --- Zonas ---
    df['zona_clean'] = df['ZONAS'].apply(
        lambda x: x.strip() if pd.notna(x) and str(x).strip() in ZONAS_VALIDAS else 'Otros'
    )

    # --- Estandarización nichos ---
    df['tipo_producto_clean'] = df['TIPO PRODUCTO'].apply(_tipo_producto_clean)
    df['capacidad_nicho'] = df.apply(
        lambda r: _capacidad_nicho(r['TIPO PRODUCTO'], r['SUB_TIPO_PRODUCTO']), axis=1
    )
    df['fila_nicho'] = df.apply(
        lambda r: _fila_nicho(r['TIPO PRODUCTO'], r['SUB_TIPO_PRODUCTO']), axis=1
    )

    # --- Integrales ---
    contratos_dduu = set(df[df['Dsc_tipo_Serv'] == 'DERECHO DE USO']['Localidad-Contrato-Num_ser'])
    contratos_ssff = set(df[df['Dsc_tipo_Serv'] == 'SERVICIO FUNERARIO']['Localidad-Contrato-Num_ser'])
    integrales = contratos_dduu & contratos_ssff
    df['es_integral'] = df['Localidad-Contrato-Num_ser'].isin(integrales)

    # --- Jerarquía ---
    df['dsc_jefeventas'] = df['dsc_jefeventas'].fillna('Sin asignar')
    df['dsc_supervisor'] = df['dsc_supervisor'].fillna('Sin asignar')
    df['dsc_vendedor'] = df['dsc_vendedor'].fillna('Sin asignar')

    # --- % inicial por fila ---
    df['pct_inicial_fila'] = np.where(
        df['VTA'] > 0,
        (df['CUI_PAGADA'] / df['VTA'] * 100).round(1),
        0.0
    )

    # --- Tipo línea abreviado ---
    linea_map = {
        'DERECHO DE USO': 'DDUU',
        'SERVICIO FUNERARIO': 'SSFF',
        'SERVICIOS ADICIONALES': 'Serv. Inh.',
    }
    df['tipo_linea'] = df['Dsc_tipo_Serv'].map(linea_map).fillna(df['Dsc_tipo_Serv'])

    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def cargar_metas(ruta: str) -> dict:
    xl = pd.ExcelFile(ruta)
    metas = {}
    for sheet in xl.sheet_names:
        df = pd.read_excel(ruta, sheet_name=sheet, header=2)
        df.columns = ['mes','anio','mes_nombre','canal','vta_total','vta_dduu','vta_ssff','vta_ni']
        df = df[pd.to_numeric(df['mes'], errors='coerce').notna()].copy()
        df['mes']  = df['mes'].astype(int)
        df['anio'] = pd.to_numeric(df['anio'], errors='coerce').fillna(2026).astype(int)
        for col in ['vta_total','vta_dduu','vta_ssff','vta_ni']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        metas[sheet] = df
    return metas
