import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

C = {
    'primario': '#1A2B3C', 'acento': '#F5C842', 'secundario': '#2D4A63',
    'neutro': '#8E9AAF', 'positivo': '#34A853', 'negativo': '#EA4335',
    'alerta': '#FBBC04', 'fondo': '#F0F2F5',
}

MESES_LABEL = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Set',10:'Oct',11:'Nov',12:'Dic'}


def _base_layout(title='', height=320):
    return dict(
        title=dict(text=title, font=dict(size=13, color=C['primario']), x=0),
        height=height,
        margin=dict(l=10, r=10, t=40 if title else 16, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='system-ui, sans-serif', size=11, color=C['neutro']),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    font=dict(size=10)),
        hoverlabel=dict(bgcolor='white', font_size=11, font_color=C['primario']),
    )


def graf01_evolucion_ventas(df_act, df_comp, filtros, metrica='vta_total'):
    anio = filtros['anio']
    anio_comp = filtros['anio_comp']

    metricas = {
        'vta_total': ('VTA Total', 'VTA'),
        'vta_dduu': ('VTA DDUU', 'VTA'),
        'contratos': ('Contratos', 'Contratos'),
        'precio_medio': ('Precio Medio DDUU', 'S/'),
    }
    titulo, unidad = metricas.get(metrica, ('VTA Total', 'VTA'))

    def agg(d, anio_val):
        if d.empty:
            return pd.DataFrame(columns=['mes', 'valor'])
        if metrica == 'vta_total':
            g = d.groupby('mes')['VTA'].sum()
        elif metrica == 'vta_dduu':
            g = d[d['Dsc_tipo_Serv']=='DERECHO DE USO'].groupby('mes')['VTA'].sum()
        elif metrica == 'contratos':
            g = d.groupby('mes')['Localidad-Contrato-Num_ser'].nunique()
        elif metrica == 'precio_medio':
            dduu = d[d['Dsc_tipo_Serv']=='DERECHO DE USO']
            vta = dduu.groupby('mes')['VTA'].sum()
            cnt = dduu.groupby('mes')['Localidad-Contrato-Num_ser'].nunique()
            g = (vta / cnt.replace(0, np.nan)).fillna(0)
        return g.reset_index().rename(columns={g.name if hasattr(g,'name') else 0: 'valor', 'mes':'mes'})

    d_act = agg(df_act, anio)
    d_comp = agg(df_comp, anio_comp)

    fig = go.Figure()

    if not d_comp.empty:
        fig.add_trace(go.Scatter(
            x=[MESES_LABEL.get(m, m) for m in d_comp['mes']],
            y=d_comp['valor'],
            name=str(anio_comp), mode='lines+markers',
            line=dict(color=C['neutro'], width=1.5, dash='dash'),
            marker=dict(size=5, color=C['neutro']),
        ))

    if not d_act.empty:
        fig.add_trace(go.Scatter(
            x=[MESES_LABEL.get(m, m) for m in d_act['mes']],
            y=d_act['valor'],
            name=str(anio), mode='lines+markers',
            line=dict(color=C['primario'], width=2.5),
            marker=dict(size=7, color=C['acento'], line=dict(color=C['primario'], width=1.5)),
            fill='tozeroy', fillcolor=C['primario']+'15',
        ))

    fmt = 'S/ {:,.0f}' if unidad == 'S/' or unidad == 'VTA' else '{:,.0f}'
    fig.update_layout(
        **_base_layout(f'{titulo} · {anio} vs {anio_comp}'),
        yaxis=dict(tickformat=',.0f', gridcolor='#F0F2F5', showgrid=True),
        xaxis=dict(showgrid=False),
    )
    return fig


def graf04_plazo_historico(df):
    if df.empty:
        return go.Figure()
    df_fin = df[df['tipo_pago'] == 'FINANCIADO']
    plazo = df_fin.groupby('anio')['cuotas'].mean().reset_index()
    plazo.columns = ['anio', 'plazo']
    anio_max = plazo['anio'].max()

    colors = [C['acento'] if a == anio_max else C['primario']+'99' for a in plazo['anio']]
    fig = go.Figure(go.Bar(
        x=plazo['anio'].astype(str), y=plazo['plazo'].round(1),
        marker_color=colors, marker_line_width=0,
        text=plazo['plazo'].round(1).astype(str) + 'm',
        textposition='outside', textfont=dict(size=10),
    ))
    fig.update_layout(**_base_layout('Plazo medio (meses)', height=280))
    fig.update_yaxis(range=[0, plazo['plazo'].max() * 1.2], showgrid=True, gridcolor='#F0F2F5')
    fig.update_xaxis(showgrid=False)
    return fig


def graf05_ventas_sede(df_act, df_comp, filtros):
    def agg(d):
        return d.groupby('sede_cod')['VTA'].sum().reset_index()

    d26 = agg(df_act)
    d25 = agg(df_comp)
    merged = d26.merge(d25, on='sede_cod', how='outer', suffixes=('_act', '_comp')).fillna(0)
    merged = merged.sort_values('VTA_act', ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=str(filtros['anio_comp']), x=merged['sede_cod'],
        y=merged['VTA_comp'], marker_color=C['neutro']+'88',
        marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        name=str(filtros['anio']), x=merged['sede_cod'],
        y=merged['VTA_act'], marker_color=C['primario'],
        marker_line_width=0,
    ))
    fig.update_layout(**_base_layout('Ventas por sede', height=320), barmode='group')
    fig.update_yaxis(tickformat=',.0f', gridcolor='#F0F2F5')
    fig.update_xaxis(showgrid=False)
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
    canal_vta = canal_vta.sort_values('pct', ascending=True)

    colors_map = {
        'FFVV NF': C['primario'], 'FFVV NI': C['secundario'],
        'SAC': '#1D9E75', 'TLD': '#BA7517', 'Otros': C['neutro'],
    }
    colors = [colors_map.get(c, C['neutro']) for c in canal_vta['canal_clean']]

    fig = go.Figure(go.Bar(
        x=canal_vta['pct'], y=canal_vta['canal_clean'],
        orientation='h', marker_color=colors, marker_line_width=0,
        text=canal_vta['pct'].astype(str) + '%',
        textposition='outside', textfont=dict(size=10),
        customdata=canal_vta['VTA'],
        hovertemplate='%{y}: %{x}% · S/ %{customdata:,.0f}<extra></extra>',
    ))
    fig.update_layout(**_base_layout('Participación por canal', height=260))
    fig.update_xaxis(range=[0, canal_vta['pct'].max() * 1.2], showgrid=True, gridcolor='#F0F2F5')
    fig.update_yaxis(showgrid=False)
    return fig


def graf07_mix_nf_ni(df_act):
    if df_act.empty:
        return go.Figure()
    by_sede = df_act.groupby(['sede_cod', 'cod_tipo_necesidad'])['Localidad-Contrato-Num_ser'].nunique().reset_index()
    by_sede.columns = ['sede', 'tn', 'contratos']
    pivot = by_sede.pivot(index='sede', columns='tn', values='contratos').fillna(0)
    pivot['total'] = pivot.sum(axis=1)
    for col in ['NF', 'NI']:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot['pct_nf'] = pivot['NF'] / pivot['total'] * 100
    pivot['pct_ni'] = pivot['NI'] / pivot['total'] * 100
    pivot = pivot.sort_values('pct_nf', ascending=True).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='NI', x=pivot['pct_ni'], y=pivot['sede'],
        orientation='h', marker_color=C['neutro']+'88', marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        name='NF', x=pivot['pct_nf'], y=pivot['sede'],
        orientation='h', marker_color=C['primario'], marker_line_width=0,
    ))
    fig.update_layout(
        **_base_layout('Mix NF / NI por sede', height=320),
        barmode='stack',
        xaxis=dict(range=[0, 100], ticksuffix='%', showgrid=True, gridcolor='#F0F2F5'),
        yaxis=dict(showgrid=False),
    )
    return fig


def graf08_ranking_jefes(df_act, por_logro=False, metas_dduu=None):
    dduu = df_act[df_act['Dsc_tipo_Serv'] == 'DERECHO DE USO']
    if dduu.empty:
        return go.Figure()

    rank = dduu.groupby('dsc_jefeventas').agg(
        vta=('VTA', 'sum'),
        contratos=('Localidad-Contrato-Num_ser', 'nunique')
    ).reset_index().sort_values('vta', ascending=True)
    rank = rank.tail(12)

    fig = go.Figure(go.Bar(
        x=rank['vta'], y=rank['dsc_jefeventas'],
        orientation='h',
        marker_color=C['primario'], marker_line_width=0,
        text=rank['vta'].apply(lambda v: f'S/ {v/1e6:.1f}M' if v >= 1e6 else f'S/ {v/1e3:.0f}K'),
        textposition='outside', textfont=dict(size=10),
        customdata=rank['contratos'],
        hovertemplate='%{y}<br>VTA: S/ %{x:,.0f}<br>Contratos: %{customdata}<extra></extra>',
    ))
    fig.update_layout(**_base_layout('Ranking jefes · VTA DDUU', height=380))
    fig.update_xaxis(tickformat=',.0f', showgrid=True, gridcolor='#F0F2F5')
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
    order = ['ZONA A', 'ZONA B', 'ZONA C', 'ZONA M', 'ZONA MM', 'SIN ZONA', 'Otros']
    zona_vta['order'] = zona_vta['zona'].apply(lambda x: order.index(x) if x in order else 99)
    zona_vta = zona_vta.sort_values('order')

    colors = [C['alerta'] if z == 'SIN ZONA' else C['primario'] for z in zona_vta['zona']]
    shades = ['#1A2B3C', '#2D4A63', '#3D6B8E', '#6B8FAF', '#9AB0C8', '#FBBC04', C['neutro']]
    colors = [shades[i] if z != 'SIN ZONA' else C['alerta'] for i, z in enumerate(zona_vta['zona'])]

    fig = go.Figure(go.Bar(
        x=zona_vta['zona'], y=zona_vta['vta'],
        marker_color=colors, marker_line_width=0,
        text=zona_vta['vta'].apply(lambda v: f'S/ {v/1e6:.1f}M' if v >= 1e6 else f'S/ {v/1e3:.0f}K'),
        textposition='outside', textfont=dict(size=10),
        hovertemplate='%{x}: S/ %{y:,.0f}<extra></extra>',
    ))
    fig.update_layout(**_base_layout('Distribución por zona · DDUU', height=300))
    fig.update_yaxis(tickformat=',.0f', showgrid=True, gridcolor='#F0F2F5')
    fig.update_xaxis(showgrid=False)
    return fig
