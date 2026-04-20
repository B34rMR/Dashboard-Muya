import pandas as pd
import numpy as np
import streamlit as st


def tabla_contratos(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    cols = {
        'fecha_str': 'Fecha',
        'sede_cod': 'Sede',
        'Localidad-Contrato-Num_ser': 'Contrato',
        'cod_tipo_necesidad': 'TN',
        'tipo_linea': 'Línea',
        'tipo_producto_clean': 'Producto',
        'capacidad_nicho': 'Capacidad',
        'zona_clean': 'Zona',
        'canal_clean': 'Canal',
        'VTA': 'VTA (S/)',
        'CUI_PAGADA': 'CUI Pagada',
        'pct_inicial_fila': '% Ini',
        'imp_dscto': 'Dscto (S/)',
        'tipo_pago': 'Pago',
        'cuotas': 'Cuotas',
        'es_integral': 'Integral',
        'PERIODO CARENCIA': 'Carencia',
        'dsc_jefeventas': 'Jefe',
        'dsc_supervisor': 'Supervisor',
        'dsc_vendedor': 'Vendedor',
    }

    existing = {k: v for k, v in cols.items() if k in df.columns}
    out = df[list(existing.keys())].copy()
    out.rename(columns=existing, inplace=True)

    if 'VTA (S/)' in out.columns:
        out['VTA (S/)'] = out['VTA (S/)'].apply(lambda x: f"S/ {x:,.0f}" if pd.notna(x) else '—')
    if 'CUI Pagada' in out.columns:
        out['CUI Pagada'] = out['CUI Pagada'].apply(lambda x: f"S/ {x:,.0f}" if pd.notna(x) and x > 0 else '—')
    if 'Dscto (S/)' in out.columns:
        out['Dscto (S/)'] = out['Dscto (S/)'].apply(lambda x: f"S/ {x:,.0f}" if pd.notna(x) and x > 0 else '—')
    if '% Ini' in out.columns:
        out['% Ini'] = out['% Ini'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) and x > 0 else '—')
    if 'Integral' in out.columns:
        out['Integral'] = out['Integral'].map({True: '✓', False: ''})
    if 'Cuotas' in out.columns:
        out['Cuotas'] = out['Cuotas'].apply(lambda x: f"{int(x)}m" if pd.notna(x) and x > 0 else '—')
    if 'Capacidad' in out.columns:
        out['Capacidad'] = out['Capacidad'].replace('', '—')

    return out


def tabla_tipo_producto(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    vta_total = df['VTA'].sum()
    cont_total = df['Localidad-Contrato-Num_ser'].nunique()

    tipos = {
        'DDUU': 'DERECHO DE USO',
        'SSFF': 'SERVICIO FUNERARIO',
        'Serv. Inh.': 'SERVICIOS ADICIONALES',
    }

    rows = []
    subtipos_dict = {}

    for label, tipo_raw in tipos.items():
        d = df[df['Dsc_tipo_Serv'] == tipo_raw]
        if d.empty:
            continue
        vta = d['VTA'].sum()
        cont = d['Localidad-Contrato-Num_ser'].nunique()
        pm = vta / cont if cont else 0
        pct = vta / vta_total * 100 if vta_total else 0

        rows.append({
            'Tipo': label,
            'Contratos': cont,
            'VTA Total': f"S/ {vta:,.0f}",
            'Precio Medio': f"S/ {pm:,.0f}",
            '% VTA': f"{pct:.1f}%",
            '_vta': vta,
            '_pct': pct,
        })

        # Subtipos
        if label == 'DDUU':
            sub_col = 'capacidad_nicho'
        else:
            sub_col = 'SUB_TIPO_PRODUCTO'

        if sub_col in d.columns:
            sub_g = d.groupby(sub_col).agg(
                vta_sub=('VTA', 'sum'),
                cont_sub=('Localidad-Contrato-Num_ser', 'nunique')
            ).reset_index()
            sub_g = sub_g[sub_g[sub_col] != ''].sort_values('vta_sub', ascending=False)
            sub_g['pm'] = sub_g['vta_sub'] / sub_g['cont_sub']
            sub_g['pct'] = sub_g['vta_sub'] / vta * 100
            subtipos_dict[label] = sub_g.rename(columns={sub_col: 'Subtipo'})

    df_out = pd.DataFrame(rows)
    return df_out, subtipos_dict
