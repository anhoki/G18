import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard de Proyectos", layout="wide")

# Diccionario de departamentos de Guatemala con coordenadas aproximadas
DEPARTAMENTOS_GUATEMALA = {
    'GUATEMALA': {'lat': 14.6349, 'lon': -90.5069},
    'EL PROGRESO': {'lat': 14.8500, 'lon': -90.0667},
    'SACATEPEQUEZ': {'lat': 14.5333, 'lon': -90.7333},
    'CHIMALTENANGO': {'lat': 14.7000, 'lon': -90.8167},
    'ESCUINTLA': {'lat': 14.3000, 'lon': -90.7833},
    'SANTA ROSA': {'lat': 14.1667, 'lon': -90.3500},
    'SOLOLÁ': {'lat': 14.7667, 'lon': -91.1833},
    'TOTONICAPÁN': {'lat': 14.9167, 'lon': -91.3667},
    'QUETZALTENANGO': {'lat': 14.8333, 'lon': -91.5167},
    'SUCHITEPÉQUEZ': {'lat': 14.5333, 'lon': -91.5000},
    'RETALHULEU': {'lat': 14.5333, 'lon': -91.6833},
    'SAN MARCOS': {'lat': 14.9667, 'lon': -91.8000},
    'HUEHUETENANGO': {'lat': 15.3167, 'lon': -91.4667},
    'QUICHÉ': {'lat': 15.3000, 'lon': -91.0000},
    'BAJA VERAPAZ': {'lat': 15.1333, 'lon': -90.3667},
    'ALTA VERAPAZ': {'lat': 15.5000, 'lon': -90.3333},
    'PETÉN': {'lat': 16.9000, 'lon': -89.9000},
    'IZABAL': {'lat': 15.5000, 'lon': -88.5000},
    'ZACAPA': {'lat': 14.9667, 'lon': -89.5333},
    'CHIQUIMULA': {'lat': 14.8000, 'lon': -89.5333},
    'JALAPA': {'lat': 14.6333, 'lon': -89.9833},
    'JUTIAPA': {'lat': 14.2833, 'lon': -89.9000},
}

@st.cache_data
def load_data():
    """Carga y prepara los datos"""
    archivos = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
    
    if not archivos:
        st.error("❌ No se encontró ningún archivo Excel")
        return pd.DataFrame()
    
    df = pd.read_excel(archivos[0], sheet_name=0)
    df.columns = df.columns.str.strip()
    
    # Identificar columnas
    col_monto = next((col for col in df.columns if 'monto' in col.lower()), None)
    col_proveedor = next((col for col in df.columns if 'formulador' in col.lower()), None)
    col_tipo = next((col for col in df.columns if 'tipo' in col.lower() or 'estudio' in col.lower()), None)
    col_depto = next((col for col in df.columns if 'departamento' in col.lower()), None)
    col_contrato = next((col for col in df.columns if 'contrato' in col.lower() and 'no' in col.lower()), None)
    
    if not col_contrato:
        for col in df.columns:
            if 'contrato' in col.lower() and df[col].iloc[0] != 'Contrato Administrativo':
                col_contrato = col
                break
    
    # Limpiar datos
    if col_contrato:
        df = df[df[col_contrato] != 'Contrato Administrativo']
        df = df.dropna(subset=[col_contrato])
    
    # Agrupar por contrato
    if all([col_monto, col_proveedor, col_tipo, col_contrato]):
        df_contratos = df.groupby(col_contrato).agg({
            col_proveedor: 'first',
            col_monto: 'sum',
            col_tipo: lambda x: ', '.join(x.unique()),
            col_depto: 'first' if col_depto else lambda x: 'N/A'
        }).reset_index()
        
        df_contratos.columns = ['No_Contrato', 'Proveedor', 'Monto_Total', 'Tipos_Estudio', 'Departamento']
        
        # Limpiar nombres de departamentos (mayúsculas para coincidir con el diccionario)
        if 'Departamento' in df_contratos.columns:
            df_contratos['Departamento'] = df_contratos['Departamento'].str.upper().str.strip()
            
            # Mapear nombres que puedan tener variaciones
            mapa_departamentos = {
                'HUEHUETENANGO': 'HUEHUETENANGO',
                'HUEHUETENANGO ': 'HUEHUETENANGO',
                'QUICHE': 'QUICHÉ',
                'QUICHÉ': 'QUICHÉ',
                'SOLOLA': 'SOLOLÁ',
                'SOLOLÁ': 'SOLOLÁ',
                'TOTONICAPAN': 'TOTONICAPÁN',
                'TOTONICAPÁN': 'TOTONICAPÁN',
                'SAN MARCOS': 'SAN MARCOS',
                'IZABAL': 'IZABAL',
                'EL PROGRESO': 'EL PROGRESO',
                'GUATEMALA': 'GUATEMALA',
                'ESCUINTLA': 'ESCUINTLA',
                'SANTA ROSA': 'SANTA ROSA',
                'QUETZALTENANGO': 'QUETZALTENANGO'
            }
            df_contratos['Departamento'] = df_contratos['Departamento'].map(mapa_departamentos).fillna(df_contratos['Departamento'])
        
        # Calcular riesgo
        proveedor_stats = df_contratos.groupby('Proveedor').agg({
            'Monto_Total': ['count', 'mean', 'std']
        }).round(0)
        
        proveedor_stats.columns = ['num_contratos', 'monto_promedio', 'desviacion']
        proveedor_stats['coeficiente_var'] = proveedor_stats['desviacion'] / proveedor_stats['monto_promedio']
        
        proveedores_riesgosos = proveedor_stats[
            (proveedor_stats['num_contratos'] >= 2) & 
            (proveedor_stats['coeficiente_var'] < 0.2)
        ].index.tolist()
        
        df_contratos['Proveedor_Riesgoso'] = df_contratos['Proveedor'].apply(
            lambda x: '⚠️ Sí' if x in proveedores_riesgosos else '✅ No'
        )
        
        # Calcular percentiles
        percentiles_por_tipo = {}
        for tipo in df_contratos['Tipos_Estudio'].unique():
            montos_tipo = df_contratos[df_contratos['Tipos_Estudio'] == tipo]['Monto_Total']
            if len(montos_tipo) >= 3:
                percentiles_por_tipo[tipo] = {
                    'p75': montos_tipo.quantile(0.75),
                    'p90': montos_tipo.quantile(0.90)
                }
        
        def calcular_riesgo(row):
            riesgo = 0
            if row['Proveedor_Riesgoso'] == '⚠️ Sí':
                riesgo += 2
            
            monto = row['Monto_Total']
            tipo = row['Tipos_Estudio']
            percentiles = percentiles_por_tipo.get(tipo, {})
            
            if monto > percentiles.get('p90', float('inf')):
                riesgo += 2
            elif monto > percentiles.get('p75', float('inf')):
                riesgo += 1
            
            if riesgo >= 3:
                return '🔴 Alto'
            elif riesgo >= 1:
                return '🟡 Medio'
            return '🟢 Bajo'
        
        df_contratos['Nivel_Riesgo'] = df_contratos.apply(calcular_riesgo, axis=1)
        
        return df_contratos
    
    return pd.DataFrame()

def crear_mapa(df, tipo_estudio_filtro=None):
    """Crea un mapa de calor de Guatemala con los montos por departamento"""
    
    if df.empty or 'Departamento' not in df.columns:
        return None
    
    # Filtrar por tipo de estudio si se especifica
    df_mapa = df.copy()
    if tipo_estudio_filtro and tipo_estudio_filtro != 'Todos':
        df_mapa = df_mapa[df_mapa['Tipos_Estudio'].str.contains(tipo_estudio_filtro, case=False, na=False)]
    
    # Agrupar por departamento
    monto_por_depto = df_mapa.groupby('Departamento')['Monto_Total'].sum().reset_index()
    monto_por_depto.columns = ['Departamento', 'Monto_Total']
    
    # Agregar coordenadas
    monto_por_depto['lat'] = monto_por_depto['Departamento'].map(lambda x: DEPARTAMENTOS_GUATEMALA.get(x, {}).get('lat', 15.5))
    monto_por_depto['lon'] = monto_por_depto['Departamento'].map(lambda x: DEPARTAMENTOS_GUATEMALA.get(x, {}).get('lon', -90.5))
    monto_por_depto['text'] = monto_por_depto.apply(
        lambda x: f"<b>{x['Departamento']}</b><br>💰 Q{x['Monto_Total']:,.0f}", axis=1
    )
    
    # Crear mapa de burbujas (tamaño proporcional al monto)
    fig = px.scatter_geo(
        monto_por_depto,
        lat='lat',
        lon='lon',
        size='Monto_Total',
        color='Monto_Total',
        text='Departamento',
        hover_name='Departamento',
        hover_data={'Monto_Total': ':,.0f', 'lat': False, 'lon': False},
        size_max=50,
        color_continuous_scale='Viridis',
        title=f'Distribución de Inversión por Departamento<br>{tipo_estudio_filtro if tipo_estudio_filtro and tipo_estudio_filtro != "Todos" else "Todos los tipos de estudio"}',
        projection='natural earth'
    )
    
    fig.update_traces(
        marker=dict(sizeref=2.*max(monto_por_depto['Monto_Total'])/(50**2)),
        hovertemplate='<b>%{hovertext}</b><br>💰 Monto: Q%{customdata[0]:,.0f}<extra></extra>'
    )
    
    fig.update_geos(
        showcountries=True,
        countrycolor='LightGray',
        showcoastlines=True,
        coastlinecolor='Gray',
        showland=True,
        landcolor='rgb(243, 243, 243)',
        showocean=True,
        oceancolor='LightBlue',
        showframe=False,
        fitbounds='locations',
        visible=True,
        resolution=50
    )
    
    fig.update_layout(
        height=550,
        margin={"r":0, "t":50, "l":0, "b":0},
        coloraxis_colorbar=dict(title="Monto (Q)")
    )
    
    return fig

def crear_mapa_barras(df, tipo_estudio_filtro=None):
    """Crea un gráfico de barras geográfico alternativo (si el mapa no funciona)"""
    
    if df.empty or 'Departamento' not in df.columns:
        return None
    
    df_mapa = df.copy()
    if tipo_estudio_filtro and tipo_estudio_filtro != 'Todos':
        df_mapa = df_mapa[df_mapa['Tipos_Estudio'].str.contains(tipo_estudio_filtro, case=False, na=False)]
    
    monto_por_depto = df_mapa.groupby('Departamento')['Monto_Total'].sum().reset_index()
    monto_por_depto = monto_por_depto.sort_values('Monto_Total', ascending=True)
    
    fig = px.bar(
        monto_por_depto,
        x='Monto_Total',
        y='Departamento',
        orientation='h',
        color='Monto_Total',
        color_continuous_scale='Viridis',
        title=f'Inversión por Departamento<br>{tipo_estudio_filtro if tipo_estudio_filtro and tipo_estudio_filtro != "Todos" else "Todos los tipos"}',
        labels={'Monto_Total': 'Monto (Q)', 'Departamento': ''}
    )
    
    fig.update_layout(height=500)
    fig.update_traces(texttemplate='Q%{x:,.0f}', textposition='outside')
    
    return fig

def main():
    st.title("📊 Dashboard de Control de Proyectos")
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No hay datos para mostrar")
        st.stop()
    
    # ========== SIDEBAR ==========
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de departamento
    if 'Departamento' in df.columns:
        deptos = st.sidebar.multiselect(
            "Departamento",
            options=sorted(df['Departamento'].dropna().unique()),
            default=sorted(df['Departamento'].dropna().unique())
        )
        df_filtrado = df[df['Departamento'].isin(deptos)] if deptos else df
    else:
        df_filtrado = df
    
    # Filtro de tipo de estudio
    tipos_estudio = ['Todos'] + sorted(df['Tipos_Estudio'].unique().tolist())
    tipo_seleccionado = st.sidebar.selectbox("Tipo de Estudio", tipos_estudio)
    
    # ========== KPIs ==========
    st.subheader("📈 Indicadores Clave")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Contratos", len(df_filtrado))
    with col2:
        st.metric("Monto Total", f"Q{df_filtrado['Monto_Total'].sum():,.0f}")
    with col3:
        st.metric("🔴 Alto Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🔴 Alto']))
    with col4:
        st.metric("🟡 Medio Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🟡 Medio']))
    with col5:
        num_prov_riesgosos = len(df_filtrado[df_filtrado['Proveedor_Riesgoso'] == '⚠️ Sí']['Proveedor'].unique())
        st.metric("⚠️ Proveedores Riesgosos", num_prov_riesgosos)
    
    st.markdown("---")
    
    # ========== MAPA INTERACTIVO ==========
    st.subheader("🗺️ Distribución Geográfica de la Inversión")
    
    tipo_para_mapa = None if tipo_seleccionado == 'Todos' else tipo_seleccionado
    
    # Intentar crear el mapa
    fig_mapa = crear_mapa(df_filtrado, tipo_para_mapa)
    
    if fig_mapa:
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        # Fallback: gráfico de barras
        st.info("No se pudo cargar el mapa. Mostrando gráfico de barras alternativo.")
        fig_barras = crear_mapa_barras(df_filtrado, tipo_para_mapa)
        if fig_barras:
            st.plotly_chart(fig_barras, use_container_width=True)
    
    st.markdown("---")
    
    # ========== TABLA RESUMEN POR DEPARTAMENTO ==========
    st.subheader("📊 Resumen de Inversión por Departamento")
    
    if 'Departamento' in df_filtrado.columns:
        resumen_depto = df_filtrado.groupby('Departamento').agg({
            'Monto_Total': ['sum', 'count', 'mean'],
            'Nivel_Riesgo': lambda x: (x == '🔴 Alto').sum()
        }).round(0)
        
        resumen_depto.columns = ['Monto_Total', 'Número_Contratos', 'Monto_Promedio', 'Contratos_Alto_Riesgo']
        resumen_depto = resumen_depto.sort_values('Monto_Total', ascending=False).reset_index()
        resumen_depto['Monto_Total'] = resumen_depto['Monto_Total'].apply(lambda x: f"Q{x:,.0f}")
        resumen_depto['Monto_Promedio'] = resumen_depto['Monto_Promedio'].apply(lambda x: f"Q{x:,.0f}")
        
        st.dataframe(resumen_depto, use_container_width=True)
    
    st.markdown("---")
    
    # ========== PROVEEDORES SOSPECHOSOS ==========
    st.subheader("🚨 Proveedores con Múltiples Contratos de Montos Similares")
    
    proveedores_riesgosos = df_filtrado[df_filtrado['Proveedor_Riesgoso'] == '⚠️ Sí']['Proveedor'].unique()
    
    if len(proveedores_riesgosos) > 0:
        for proveedor in proveedores_riesgosos:
            df_prov = df_filtrado[df_filtrado['Proveedor'] == proveedor]
            st.markdown(f"""
            <div style="background-color: #ffcccc; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                <b>⚠️ {proveedor}</b><br>
                📄 {len(df_prov)} contratos | 💰 Promedio: Q{df_prov['Monto_Total'].mean():,.0f}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ No se detectaron proveedores con múltiples contratos de montos muy similares")
    
    st.markdown("---")
    
    # ========== TABLA DE CONTRATOS ==========
    st.subheader("📋 Detalle de Contratos")
    
    columnas_mostrar = ['No_Contrato', 'Proveedor', 'Tipos_Estudio', 'Departamento', 'Monto_Total', 'Proveedor_Riesgoso', 'Nivel_Riesgo']
    columnas_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]
    
    tabla_mostrar = df_filtrado[columnas_existentes].copy()
    tabla_mostrar = tabla_mostrar.fillna('')
    
    def color_riesgo(val):
        if '🔴 Alto' in str(val):
            return 'background-color: #ffcccc'
        elif '🟡 Medio' in str(val):
            return 'background-color: #fff3cc'
        elif '🟢 Bajo' in str(val):
            return 'background-color: #ccffcc'
        return ''
    
    styled_df = tabla_mostrar.style.map(color_riesgo, subset=['Nivel_Riesgo'])
    styled_df = styled_df.format({'Monto_Total': '{:,.0f}'})
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # ========== RECOMENDACIONES ==========
    st.markdown("---")
    st.subheader("📋 Recomendaciones para Auditoría")
    
    recomendaciones = []
    
    if len(proveedores_riesgosos) > 0:
        recomendaciones.append(f"🔴 **Auditar a {len(proveedores_riesgosos)} proveedores** que ganaron múltiples contratos con montos muy similares")
    
    num_alto_riesgo = len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🔴 Alto'])
    if num_alto_riesgo > 0:
        recomendaciones.append(f"🟠 **Revisar {num_alto_riesgo} contratos en alto riesgo** por montos significativamente superiores al promedio")
    
    if not recomendaciones:
        st.success("✅ No se detectaron anomalías significativas")
    else:
        for rec in recomendaciones:
            st.markdown(f"- {rec}")

if __name__ == "__main__":
    main()
