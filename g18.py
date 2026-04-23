import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap

st.set_page_config(page_title="Dashboard de Proyectos - Guatemala", layout="wide")

# ============================================
# COORDENADAS DE DEPARTAMENTOS DE GUATEMALA
# ============================================
COORDENADAS_DEPARTAMENTOS = {
    'GUATEMALA': [14.6349, -90.5069],
    'EL PROGRESO': [14.8500, -90.0667],
    'SACATEPEQUEZ': [14.5333, -90.7333],
    'CHIMALTENANGO': [14.7000, -90.8167],
    'ESCUINTLA': [14.3000, -90.7833],
    'SANTA ROSA': [14.1667, -90.3500],
    'SOLOLÁ': [14.7667, -91.1833],
    'TOTONICAPÁN': [14.9167, -91.3667],
    'QUETZALTENANGO': [14.8333, -91.5167],
    'SUCHITEPÉQUEZ': [14.5333, -91.5000],
    'RETALHULEU': [14.5333, -91.6833],
    'SAN MARCOS': [14.9667, -91.8000],
    'HUEHUETENANGO': [15.3167, -91.4667],
    'QUICHÉ': [15.3000, -91.0000],
    'BAJA VERAPAZ': [15.1333, -90.3667],
    'ALTA VERAPAZ': [15.5000, -90.3333],
    'PETÉN': [16.9000, -89.9000],
    'IZABAL': [15.5000, -88.5000],
    'ZACAPA': [14.9667, -89.5333],
    'CHIQUIMULA': [14.8000, -89.5333],
    'JALAPA': [14.6333, -89.9833],
    'JUTIAPA': [14.2833, -89.9000],
}

# ============================================
# CARGA DE DATOS
# ============================================
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
        
        # Limpiar nombres de departamentos
        if 'Departamento' in df_contratos.columns:
            df_contratos['Departamento'] = df_contratos['Departamento'].str.upper().str.strip()
            
            mapa_departamentos = {
                'HUEHUETENANGO': 'HUEHUETENANGO', 'QUICHE': 'QUICHÉ', 'QUICHÉ': 'QUICHÉ',
                'SOLOLA': 'SOLOLÁ', 'SOLOLÁ': 'SOLOLÁ', 'TOTONICAPAN': 'TOTONICAPÁN',
                'TOTONICAPÁN': 'TOTONICAPÁN', 'SAN MARCOS': 'SAN MARCOS', 'IZABAL': 'IZABAL',
                'EL PROGRESO': 'EL PROGRESO', 'GUATEMALA': 'GUATEMALA', 'ESCUINTLA': 'ESCUINTLA',
                'SANTA ROSA': 'SANTA ROSA', 'QUETZALTENANGO': 'QUETZALTENANGO'
            }
            df_contratos['Departamento'] = df_contratos['Departamento'].map(mapa_departamentos).fillna(df_contratos['Departamento'])
        
        # Calcular proveedores riesgosos
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
        
        # Calcular percentiles por tipo de estudio
        percentiles_por_tipo = {}
        for tipo in df_contratos['Tipos_Estudio'].unique():
            montos_tipo = df_contratos[df_contratos['Tipos_Estudio'] == tipo]['Monto_Total']
            if len(montos_tipo) >= 3:
                percentiles_por_tipo[tipo] = {
                    'p75': montos_tipo.quantile(0.75),
                    'p90': montos_tipo.quantile(0.90)
                }
        
        # Calcular nivel de riesgo
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

# ============================================
# FUNCIONES DE MAPA
# ============================================
def crear_mapa_burbujas(df, tipo_estudio_filtro=None):
    """Crea un mapa de burbujas con folium"""
    
    if df.empty or 'Departamento' not in df.columns:
        return None
    
    df_mapa = df.copy()
    if tipo_estudio_filtro and tipo_estudio_filtro != 'Todos':
        df_mapa = df_mapa[df_mapa['Tipos_Estudio'].str.contains(tipo_estudio_filtro, case=False, na=False)]
    
    monto_por_depto = df_mapa.groupby('Departamento')['Monto_Total'].sum().reset_index()
    
    if monto_por_depto.empty:
        return None
    
    center_lat = 15.5
    center_lon = -90.25
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8, control_scale=True, tiles='OpenStreetMap')
    
    max_monto = monto_por_depto['Monto_Total'].max()
    min_radius = 15
    max_radius = 50
    
    for _, row in monto_por_depto.iterrows():
        depto = row['Departamento']
        monto = row['Monto_Total']
        
        coords = COORDENADAS_DEPARTAMENTOS.get(depto.upper())
        if not coords:
            continue
        
        radius = min_radius + (monto / max_monto) * (max_radius - min_radius) if max_monto > 0 else min_radius
        
        folium.CircleMarker(
            location=coords,
            radius=radius,
            popup=folium.Popup(f"""
                <b>{depto}</b><br>
                💰 Monto: Q{monto:,.0f}<br>
                📊 Proyectos: {len(df_mapa[df_mapa['Departamento'] == depto])}
            """, max_width=300),
            tooltip=f"{depto}: Q{monto:,.0f}",
            color='#2E86AB',
            fill=True,
            fill_color='#2E86AB',
            fill_opacity=0.6,
            weight=2
        ).add_to(m)
        
        folium.map.Marker(
            coords,
            icon=folium.DivIcon(
                icon_size=(80, 20),
                icon_anchor=(40, -radius - 5),
                html=f'<div style="font-size: 10px; font-weight: bold; background: white; padding: 2px 5px; border-radius: 5px; border: 1px solid #2E86AB;">Q{monto/1000000:.1f}M</div>'
            )
        ).add_to(m)
    
    return m

def crear_mapa_calor(df, tipo_estudio_filtro=None):
    """Crea un mapa de calor con folium"""
    
    if df.empty or 'Departamento' not in df.columns:
        return None
    
    df_mapa = df.copy()
    if tipo_estudio_filtro and tipo_estudio_filtro != 'Todos':
        df_mapa = df_mapa[df_mapa['Tipos_Estudio'].str.contains(tipo_estudio_filtro, case=False, na=False)]
    
    heat_data = []
    for _, row in df_mapa.iterrows():
        depto = row['Departamento']
        monto = row['Monto_Total']
        coords = COORDENADAS_DEPARTAMENTOS.get(depto.upper())
        if coords:
            intensidad = min(100, int(monto / 100000))
            for _ in range(intensidad):
                heat_data.append(coords)
    
    if not heat_data:
        return None
    
    center_lat = 15.5
    center_lon = -90.25
    
    heat_map = folium.Map(location=[center_lat, center_lon], zoom_start=8, control_scale=True, tiles='OpenStreetMap')
    
    HeatMap(heat_data, radius=20, blur=15, min_opacity=0.3, max_zoom=10).add_to(heat_map)
    
    return heat_map

# ============================================
# MAIN
# ============================================
def main():
    st.title("📊 Dashboard de Control de Proyectos de Infraestructura")
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No hay datos para mostrar")
        st.stop()
    
    # ========== SIDEBAR ==========
    st.sidebar.header("🔍 Filtros")
    
    if 'Departamento' in df.columns:
        deptos = st.sidebar.multiselect(
            "Departamento",
            options=sorted(df['Departamento'].dropna().unique()),
            default=sorted(df['Departamento'].dropna().unique())
        )
        df_filtrado = df[df['Departamento'].isin(deptos)] if deptos else df
    else:
        df_filtrado = df
    
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
    
    # ========== GRÁFICOS ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Montos por Departamento")
        monto_depto = df_filtrado.groupby('Departamento')['Monto_Total'].sum().sort_values(ascending=True)
        if not monto_depto.empty:
            fig = px.bar(
                x=monto_depto.values,
                y=monto_depto.index,
                orientation='h',
                color=monto_depto.values,
                color_continuous_scale='Viridis',
                labels={'x': 'Monto Total (Q)', 'y': ''}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🚨 Nivel de Riesgo")
        riesgo_counts = df_filtrado['Nivel_Riesgo'].value_counts()
        if not riesgo_counts.empty:
            fig = px.pie(
                values=riesgo_counts.values,
                names=riesgo_counts.index,
                color=riesgo_counts.index,
                color_discrete_map={'🔴 Alto': 'red', '🟡 Medio': 'orange', '🟢 Bajo': 'green'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========== MAPA ==========
    st.subheader("🗺️ Distribución Geográfica de la Inversión")
    
    tipo_para_mapa = None if tipo_seleccionado == 'Todos' else tipo_seleccionado
    
    tab1, tab2 = st.tabs(["📍 Mapa de Burbujas", "🔥 Mapa de Calor"])
    
    with tab1:
        st.caption("💡 El tamaño de cada burbuja representa el monto total invertido en el departamento")
        mapa_burbujas = crear_mapa_burbujas(df_filtrado, tipo_para_mapa)
        if mapa_burbujas:
            folium_static(mapa_burbujas, width=1200, height=550)
        else:
            st.info("ℹ️ No hay datos suficientes para mostrar el mapa")
    
    with tab2:
        st.caption("💡 Las zonas más calientes indican mayor concentración de inversión")
        mapa_calor = crear_mapa_calor(df_filtrado, tipo_para_mapa)
        if mapa_calor:
            folium_static(mapa_calor, width=1200, height=550)
        else:
            st.info("ℹ️ No hay datos suficientes para el mapa de calor")
    
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
            
            st.dataframe(df_prov[['No_Contrato', 'Monto_Total', 'Tipos_Estudio', 'Departamento', 'Nivel_Riesgo']])
            st.markdown("---")
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
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.caption(f"📅 Última actualización: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
