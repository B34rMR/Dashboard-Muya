import pandas as pd
import numpy as np


def _safe_div(a, b):
    return a / b if b and b != 0 else 0.0


def _var_pct(actual, anterior):
    if anterior and anterior != 0:
        return (actual - anterior) / abs(anterior) * 100
    return None


def calcular_kpis(df_act: pd.DataFrame, df_comp: pd.DataFrame,
                  metas: dict, filtros: dict, cfg: dict) -> dict:
    moneda = cfg['empresa']['moneda']

    def dduu(d): return d[d['Dsc_tipo_Serv'] == 'DERECHO DE USO']
    def contratos_unicos(d): return d['Localidad-Contrato-Num_ser'].nunique()

    # --- KPI-01: Ventas totales ---
    vta_act = df_act['VTA'].sum()
    vta_comp = df_comp['VTA'].sum()

    # --- KPI-02: Ventas DDUU ---
    vta_dduu_act = dduu(df_act)['VTA'].sum()
    vta_dduu_comp = dduu(df_comp)['VTA'].sum()

    # --- KPI-03: Contratos ---
    cont_act = contratos_unicos(df_act)
    cont_comp = contratos_unicos(df_comp)

    # --- KPI-04: Precio medio DDUU ---
    cont_dduu_act = contratos_unicos(dduu(df_act))
    cont_dduu_comp = contratos_unicos(dduu(df_comp))
    pm_act = _safe_div(vta_dduu_act, cont_dduu_act)
    pm_comp = _safe_div(vta_dduu_comp, cont_dduu_comp)

    # --- KPI-05: % Inicial real ---
    pct_ini_act = _safe_div(df_act['CUI_PAGADA'].sum(), vta_act) * 100
    pct_ini_comp = _safe_div(df_comp['CUI_PAGADA'].sum(), vta_comp) * 100

    # --- TAR-01: Descuento ---
    dscto_monto = df_act['imp_dscto'].sum()
    dscto_pct = _safe_div(dscto_monto, vta_act) * 100

    # --- TAR-02: Sin carencia ---
    carencia_no = contratos_unicos(df_act[df_act['PERIODO CARENCIA'] == 'NO PASO'])
    carencia_pct = _safe_div(carencia_no, cont_act) * 100

    # --- TAR-03: CUI partida ---
    df_cui = df_act[df_act['Flg_CUO_Part'] == 'SI']
    cui_count = contratos_unicos(df_cui)
    cui_vta = df_cui['VTA'].sum()
    cui_pct_c = _safe_div(cui_count, cont_act) * 100
    cui_pct_v = _safe_div(cui_vta, vta_act) * 100

    # --- TAR-04: Financiamiento ---
    df_fin = df_act[df_act['tipo_pago'] == 'FINANCIADO']
    plazo_medio = df_fin['cuotas'].mean() if len(df_fin) else 0
    # imp_cuota es referencial solamente

    # --- TAR-05: Liquidez ---
    cui_pagada = df_act['CUI_PAGADA'].sum()
    vta_contado = df_act[df_act['tipo_pago'] == 'CONTADO']['VTA'].sum()
    liquidez_monto = cui_pagada + vta_contado
    liquidez_pct = _safe_div(liquidez_monto, vta_act) * 100
    liquidez_cui_pct = _safe_div(cui_pagada, vta_act) * 100
    liquidez_cnt_pct = _safe_div(vta_contado, vta_act) * 100

    cui_pagada_comp = df_comp['CUI_PAGADA'].sum()
    vta_contado_comp = df_comp[df_comp['tipo_pago'] == 'CONTADO']['VTA'].sum()
    liquidez_pct_comp = _safe_div(cui_pagada_comp + vta_contado_comp, df_comp['VTA'].sum()) * 100

    # --- MIX-01: NF/NI ---
    nf_c = contratos_unicos(df_act[df_act['cod_tipo_necesidad'] == 'NF'])
    ni_c = contratos_unicos(df_act[df_act['cod_tipo_necesidad'] == 'NI'])
    pct_nf = _safe_div(nf_c, cont_act) * 100
    pct_ni = _safe_div(ni_c, cont_act) * 100

    # --- MIX-02: Integrales ---
    integrales = contratos_unicos(df_act[df_act['es_integral'] & (df_act['Dsc_tipo_Serv'] == 'DERECHO DE USO')])
    pct_int = _safe_div(integrales, cont_dduu_act) * 100

    # --- MIX-03: Serv. Inh. ---
    df_inh = df_act[df_act['tipo_linea'] == 'Serv. Inh.']
    inh_count = contratos_unicos(df_inh)
    inh_vta = df_inh['VTA'].sum()

    # --- Metas ---
    meta = _obtener_meta(metas, filtros)
    meta_vta = meta.get('vta_total', 0) or 0
    meta_dduu = meta.get('vta_dduu', 0) or 0
    meta_cont = meta.get('contratos', 0) or 0
    meta_pm = meta.get('precio_medio_dduu', 0) or 0
    meta_ini = (meta.get('pct_inicial', 0) or 0) * 100
    meta_plazo = meta.get('plazo_medio', 0) or 0

    alertas = cfg.get('alertas', {})

    return {
        # KPIs
        'vta_total': vta_act, 'vta_total_comp': vta_comp,
        'vta_total_var': _var_pct(vta_act, vta_comp),
        'meta_vta': meta_vta,

        'vta_dduu': vta_dduu_act, 'vta_dduu_comp': vta_dduu_comp,
        'vta_dduu_var': _var_pct(vta_dduu_act, vta_dduu_comp),
        'meta_dduu': meta_dduu,

        'contratos': cont_act, 'contratos_comp': cont_comp,
        'contratos_var': _var_pct(cont_act, cont_comp),
        'meta_contratos': meta_cont,

        'precio_medio': pm_act, 'precio_medio_comp': pm_comp,
        'precio_medio_var': _var_pct(pm_act, pm_comp),
        'meta_pm': meta_pm,

        'pct_inicial': pct_ini_act, 'pct_inicial_comp': pct_ini_comp,
        'pct_inicial_var': pct_ini_act - pct_ini_comp,
        'meta_ini': meta_ini,

        # % Logro DDUU
        'pct_logro_dduu': _safe_div(vta_dduu_act, meta_dduu) * 100 if meta_dduu else None,

        # Tarjetas
        'dscto_monto': dscto_monto, 'dscto_pct': dscto_pct,
        'dscto_umbral': alertas.get('descuento_umbral', 0.05) * 100,
        'dscto_critico': alertas.get('descuento_critico', 0.10) * 100,

        'carencia_no': carencia_no, 'carencia_pct': carencia_pct,

        'cui_count': cui_count, 'cui_vta': cui_vta,
        'cui_pct_c': cui_pct_c, 'cui_pct_v': cui_pct_v,

        'plazo_medio': plazo_medio,
        'meta_plazo': meta_plazo,

        'liquidez_monto': liquidez_monto, 'liquidez_pct': liquidez_pct,
        'liquidez_cui_pct': liquidez_cui_pct, 'liquidez_cnt_pct': liquidez_cnt_pct,
        'liquidez_pct_comp': liquidez_pct_comp,
        'liquidez_pct_var': liquidez_pct - liquidez_pct_comp,
        'cui_pagada': cui_pagada, 'vta_contado': vta_contado,

        # Mix
        'pct_nf': pct_nf, 'pct_ni': pct_ni,
        'pct_integrales': pct_int,
        'inh_count': inh_count, 'inh_vta': inh_vta,

        # Conteo general
        'n_contratos': cont_act,
        'n_lineas': len(df_act),
        'moneda': moneda,
        'anio_comp': filtros['anio_comp'],

        # Umbrales semáforo
        'umbral_critico': alertas.get('cumplimiento_critico', 0.50) * 100,
        'umbral_alerta': alertas.get('cumplimiento_alerta', 0.75) * 100,
    }


def _obtener_meta(metas: dict, filtros: dict) -> dict:
    try:
        sede = filtros.get('sede', 'Todas')
        mes = filtros.get('mes')
        anio = filtros.get('anio')
        canal = filtros.get('canal', 'Todos')

        sheet_key = 'TOTAL' if sede == 'Todas' else sede
        if sheet_key not in metas:
            return {}

        df_m = metas[sheet_key]

        # Verificar que las columnas necesarias existen
        required = ['mes', 'anio', 'canal', 'vta_total', 'vta_dduu']
        if not all(c in df_m.columns for c in required):
            return {}

        canal_key = canal if canal != 'Todos' else 'TODOS'

        mask = (df_m['anio'] == anio) & (df_m['canal'] == canal_key)
        if mes:
            mask = mask & (df_m['mes'] == mes)

        subset = df_m[mask]
        if subset.empty:
            return {}

        return {
            'vta_total': subset['vta_total'].sum(),
            'vta_dduu':  subset['vta_dduu'].sum(),
            'vta_ssff':  subset['vta_ssff'].sum() if 'vta_ssff' in subset.columns else 0,
            'vta_ni':    subset['vta_ni'].sum()    if 'vta_ni'   in subset.columns else 0,
        }
    except Exception:
        return {}


def color_semaforo(pct_logro: float, umbrales: dict) -> str:
    if pct_logro is None:
        return '#8E9AAF'
    if pct_logro < umbrales.get('umbral_critico', 50):
        return '#EA4335'
    if pct_logro < umbrales.get('umbral_alerta', 75):
        return '#FBBC04'
    return '#34A853'
