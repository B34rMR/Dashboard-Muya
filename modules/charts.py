import pandas as pd
import numpy as np
import plotly.graph_objects as go

PRIMARIO  = '#1A2B3C'
ACENTO    = '#F5C842'
SECUNDARIO= '#2D4A63'
NEUTRO    = '#8E9AAF'
NEUTRO_T  = 'rgba(142,154,175,0.5)'
PRIMARIO_T= 'rgba(26,43,60,0.08)'

MESES_LABEL = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
               7:'Jul',8:'Ago',9:'Set',10:'Oct',11:'Nov',12:'Dic'}


def _layout(title='', height=320):
    return dict(
        title=dict(text=title, font=dict(size=13, color=PRIMARIO), x=0),
        height=height,
        margin=dict(l=10, r=10, t=40 if title else 16, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='system-ui, sans-serif', size=11, color=NEUTRO),
        legend=dict(orientation='h', yanchor='bottom', y=1.02,
                    xanchor='right', x=1, font=dict(size=10)),
        hoverlabel=dict(bgcolor='white', font_size=11, font_color=PRIMARIO),
    )


def graf01_evolucion_ventas(df_act, df_comp, filtros, metrica='vta_total'):
    anio      = filtros['anio']
    anio_comp = filtros['anio_comp']

    def agg(d):
        if d.empty:
            return pd.DataFrame(columns=['mes', 'valor'])
        if metrica == 'vta_total':
            g = d.groupby('mes')['VTA'].sum()
        elif metrica == 'vta_dduu':
            g = d[d['Dsc_tipo_Serv'] == 'DERECHO DE USO'].groupby('mes')['VTA'].sum()
        elif metrica == 'contratos':
            g = d.groupby('mes')['Localidad-Contrato-Num_ser'].nunique()
        else:
            dd = d[d['Dsc_tipo_Serv'] == 'DERECHO DE USO']
            vta = dd.groupby('mes')['VTA'].sum()
            cnt = dd.groupby('mes')['Localidad-Contrato-Num_ser'].nunique()
            g   = (vta / cnt.replace(0, np.nan)).fillna(0)
        return g.reset_index().rename(columns={g.name: 'valor'})

    d26 = agg(df_act)
    d25 = agg(df_comp)
    fig = go.Figure()
    if not d25.empty:
        fig.add_trace(go.Scatter(
            x=[MESES_LABEL.get(int(m), m) for m in d25['mes']],
            y=d25['valor'], name=str(anio_comp), mode='lines+markers',
            line=dict(color=NEUTRO, width=1.5, dash='dash'),
            marker=dict(size=5, color=NEUTRO),
        ))
    if not d26.empty:
        fig.add_trace(go.Scatter(
            x=[MESES_LABEL.get(int(m), m) for m in d26['mes']],
            y=d26['valor'], name=str(anio), mode='lines+markers',
            line=dict(color=PRIMARIO, width=2.5),
            marker=dict(size=7, color=ACENTO,
                        line=dict(color=PRIMARIO, width=1.5)),
            fill='tozeroy', fillcolor=PRIMARIO_T,
        ))
    fig.update_layout(**_layout())
    fig.update_yaxis(tickformat=',.0f', gridcolor='#F0F2F5')
    fig.update_layout(xaxis=dict(showgrid=False)
    return fig


def graf04_plazo_historico(df):
    if df.empty:
        return go.Figure()
    df_fin = df[df['tipo_pago'] == 'FINANCIADO']
    if df_fin.empty:
        return go.Figure()
    plazo = df_fin.groupby('anio')['cuotas'].mean().reset_index()
    plazo.columns = ['anio', 'plazo']
    anio_max = int(plazo['anio'].max())
    colors = [ACENTO if int(a) == anio_max else PRIMARIO for a in plazo['anio']]
    fig = go.Figure(go.Bar(
        x=plazo['anio'].astype(str),
        y=plazo['plazo'].round(1),
        marker=dict(color=colors),
        text=plazo['plazo'].round(1).astype(str) + 'm',
        textposition='outside',
        textfont=dict(size=10),
    ))
    fig.update_layout(**_layout('Plazo medio (meses)', height=280))
    fig.update_yaxis(range=[0, plazo['plazo'].max() * 1.25],
                     showgrid=True, gridcolor='#F0F2F5')
    fig.update_layout(xaxis=dict(showgrid=False)
    return fig


def graf05_ventas_sede(df_act, df_comp, filtros):
    def agg(d):
        return d.groupby('sede_cod')['VTA'].sum().reset_index()
    d26 = agg(df_act)
    d25 = agg(df_comp)
    merged = d26.merge(d25, on='sede_cod', how='outer',
                       suffixes=('_act', '_comp')).fillna(0)
    merged = merged.sort_values('VTA_act', ascending=False)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=str(filtros['anio_comp']),
        x=merged['sede_cod'], y=merged['VTA_comp'],
        marker=dict(color=NEUTRO_T),
    ))
    fig.add_trace(go.Bar(
        name=str(filtros['anio']),
        x=merged['sede_cod'], y=merged['VTA_act'],
        marker=dict(color=PRIMARIO),
    ))
    fig.update_layout(**_layout('Ventas por sede', height=320), barmode='group')
    fig.update_yaxis(tickformat=',.0f', gridcolor='#F0F2F5')
    fig.update_layout(xaxis=dict(showgrid=False)
    return fig


def graf06_canal(df_act, tipo_nec='TODOS'):
    d = df_act.copy()
    if tipo_nec != 'TODOS':
        d = d[d['cod_tipo_necesidad'] == tipo_nec]
    total = d['VTA'].sum()
    if total == 0:
        return go.Figure()
    canal_vta = d.groupby('canal_clean')['VTA'].sum().reset_index()
    canal_vta['pct'] = (canal_vta['VTA'] / total * 100).round(1)
    canal_vta = canal_vta[canal_vta['pct'] > 0].sort_values('pct', ascending=True)
    colors_map = {'FFVV NF': PRIMARIO, 'FFVV NI': SECUNDARIO,
                  'SAC': '#1D9E75', 'TLD': '#BA7517', 'Otros': NEUTRO}
    colors = [colors_map.get(c, NEUTRO) for c in canal_vta['canal_clean']]
    fig = go.Figure(go.Bar(
        x=canal_vta['pct'], y=canal_vta['canal_clean'],
        orientation='h', marker=dict(color=colors),
        text=canal_vta['pct'].astype(str) + '%',
        textposition='outside', textfont=dict(size=10),
        customdata=canal_vta['VTA'],
        hovertemplate='%{y}: %{x}% · S/ %{customdata:,.0f}<extra></extra>',
    ))
    fig.update_layout(**_layout('Participación por canal', height=260))
    fig.update_layout(xaxis=dict(range=[0, canal_vta['pct'].max() * 1.25],
                     showgrid=True, gridcolor='#F0F2F5')
    fig.update_yaxis(showgrid=False)
    return fig


def graf07_mix_nf_ni(df_act):
    if df_act.empty:
        return go.Figure()
    by_sede = (df_act.groupby(['sede_cod', 'cod_tipo_necesidad'])
               ['Localidad-Contrato-Num_ser'].nunique().reset_index())
    by_sede.columns = ['sede', 'tn', 'contratos']
    pivot = by_sede.pivot(index='sede', columns='tn',
                          values='contratos').fillna(0)
    for col in ['NF', 'NI']:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot['total'] = pivot.sum(axis=1)
    pivot['pct_nf'] = pivot['NF'] / pivot['total'] * 100
    pivot['pct_ni'] = pivot['NI'] / pivot['total'] * 100
    pivot = pivot.sort_values('pct_nf', ascending=True).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(name='NI', x=pivot['pct_ni'], y=pivot['sede'],
                         orientation='h', marker=dict(color=NEUTRO_T)))
    fig.add_trace(go.Bar(name='NF', x=pivot['pct_nf'], y=pivot['sede'],
                         orientation='h', marker=dict(color=PRIMARIO)))
    fig.update_layout(
        **_layout('Mix NF / NI por sede', height=320), barmode='stack',
        xaxis=dict(range=[0, 100], ticksuffix='%',
                   showgrid=True, gridcolor='#F0F2F5'),
        yaxis=dict(showgrid=False),
    )
    return fig


def graf08_ranking_jefes(df_act):
    dduu = df_act[df_act['Dsc_tipo_Serv'] == 'DERECHO DE USO']
    if dduu.empty:
        return go.Figure()
    rank = (dduu.groupby('dsc_jefeventas')
            .agg(vta=('VTA', 'sum'),
                 contratos=('Localidad-Contrato-Num_ser', 'nunique'))
            .reset_index().sort_values('vta', ascending=True).tail(12))
    fig = go.Figure(go.Bar(
        x=rank['vta'], y=rank['dsc_jefeventas'], orientation='h',
        marker=dict(color=PRIMARIO),
        text=rank['vta'].apply(
            lambda v: f'S/ {v/1e6:.1f}M' if v >= 1e6 else f'S/ {v/1e3:.0f}K'),
        textposition='outside', textfont=dict(size=10),
        customdata=rank['contratos'],
        hovertemplate='%{y}<br>VTA: S/ %{x:,.0f}<br>Contratos: %{customdata}<extra></extra>',
    ))
    fig.update_layout(**_layout('Ranking jefes · VTA DDUU', height=400))
    fig.update_layout(xaxis=dict(tickformat=',.0f', showgrid=True, gridcolor='#F0F2F5')
    fig.update_yaxis(showgrid=False)
    return fig


def graf09_zonas(df_act, tipo_producto='Todos'):
    dduu = df_act[df_act['Dsc_tipo_Serv'] == 'DERECHO DE USO'].copy()
    if tipo_producto != 'Todos':
        dduu = dduu[dduu['tipo_producto_clean'] == tipo_producto]
    if dduu.empty:
        return go.Figure()
    zona_vta = dduu.groupby('zona_clean')['VTA'].sum().reset_index()
    zona_vta.columns = ['zona', 'vta']
    order = ['ZONA A','ZONA B','ZONA C','ZONA M','ZONA MM','SIN ZONA','Otros']
    zona_vta['order'] = zona_vta['zona'].apply(
        lambda x: order.index(x) if x in order else 99)
    zona_vta = zona_vta.sort_values('order')
    shades = ['#1A2B3C','#2D4A63','#3D6B8E','#6B8FAF','#9AB0C8','#FBBC04',NEUTRO]
    colors = ['#FBBC04' if z == 'SIN ZONA' else shades[min(i, len(shades)-1)]
              for i, z in enumerate(zona_vta['zona'])]
    fig = go.Figure(go.Bar(
        x=zona_vta['zona'], y=zona_vta['vta'],
        marker=dict(color=colors),
        text=zona_vta['vta'].apply(
            lambda v: f'S/ {v/1e6:.1f}M' if v >= 1e6 else f'S/ {v/1e3:.0f}K'),
        textposition='outside', textfont=dict(size=10),
        hovertemplate='%{x}: S/ %{y:,.0f}<extra></extra>',
    ))
    fig.update_layout(**_layout('Distribución por zona · DDUU', height=300))
    fig.update_yaxis(tickformat=',.0f', showgrid=True, gridcolor='#F0F2F5')
    fig.update_layout(xaxis=dict(showgrid=False)
    return fig
