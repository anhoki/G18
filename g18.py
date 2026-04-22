import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard de Proyectos", layout="wide")

@st.cache_data
def load_data():
    """Carga y prepara los datos"""
    archivos = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
    
    if not archivos:
        st.error("❌ No se encontró ningún archivo Excel")
        return pd.DataFrame()
    
    df = pd.read_excel(archivos[0], sheet_name=0)
    df.columns = df.columns.str.strip()
    
    # Identificar columnas importantes
    col_monto = next((col for col in df.columns if 'monto' in col.lower()), None)
    col_proveedor = next((col for col in df.columns if 'formulador' in col.lower() or 'proveedor' in col.lower()), None)
    col_tipo = next((col for col in df.columns if 'tipo' in col.lower() or 'estudio' in col.lower()), None)
    col_depto = next((col for col in df.columns if 'departamento' in col.lower()), None)
    
    if not all([col_monto, col_proveedor, col_tipo]):
        st.warning("No se encontraron todas las columnas necesarias")
        return df
    
    # 1. Detectar proveedores riesgosos (múltiples contratos con montos similares)
    proveedor_stats = df.groupby(col_proveedor)[col_monto].agg(['count', 'mean', 'std']).round(0)
    proveedor_stats['coeficiente_var'] = proveedor_stats['std'] / proveedor_stats['mean']
    
    proveedores_riesgosos = proveedor_stats[
        (proveedor_stats['count'] >= 2) & 
        (proveedor_stats['coeficiente_var'] < 0.2)
    ].index.tolist()
    
    df['Proveedor_Riesgoso'] = df[col_proveedor].apply(lambda x: '⚠️ Sí' if x in proveedores_riesgosos else '✅ No')
    
    # 2. Calcular percentiles por tipo de estudio
    percentiles_por_tipo = {}
    for tipo in df[col_tipo].unique():
        montos_tipo = df[df[col_tipo] == tipo][col_monto]
        percentiles_por_tipo[tipo] = {
            'p75': montos_tipo.quantile(0.75),
            'p90': montos_tipo.quantile(0.90)
        }
    
    # 3. Contar frecuencia proveedor + tipo de estudio
    conteo_proveedor_tipo = df.groupby([col_proveedor, col_tipo]).size().to_dict()
    
    # 4. Calcular nivel de riesgo
    def calcular_riesgo(row):
        riesgo = 0
        
        # Criterio 1: Proveedor riesgoso
        if row['Proveedor_Riesgoso'] == '⚠️ Sí':
            riesgo += 2
        
        # Criterio 2: Monto en percentil alto
        monto = row[col_monto]
        tipo = row[col_tipo]
        percentiles = percentiles_por_tipo.get(tipo, {})
        
        if monto > percentiles.get('p90', 0):
            riesgo += 2
        elif monto > percentiles.get('p75', 0):
            riesgo += 1
        
        # Criterio 3: Mismo proveedor + mismo tipo repetido
        clave = (row[col_proveedor], row[col_tipo])
        if conteo_proveedor_tipo.get(clave, 0) > 2:
            riesgo += 1
        
        if riesgo >= 3:
            return '🔴 Alto'
        elif riesgo >= 1:
            return '🟡 Medio'
        return '🟢 Bajo'
    
    df['Nivel_Riesgo'] = df.apply(calcular_riesgo, axis=1)
    
    # Guardar metadata
    df.attrs['col_monto'] = col_monto
    df.attrs['col_proveedor'] = col_proveedor
    df.attrs['col_tipo'] = col_tipo
    df.attrs['col_depto'] = col_depto
    df.attrs['proveedores_riesgosos'] = proveedores_riesgosos
    
    return df

def main():
    st.title("📊 Dashboard de Control de Proyectos")
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No hay datos para mostrar")
        return
    
    col_monto = df.attrs.get('col_monto')
    col_proveedor = df.attrs.get('col_proveedor')
    col_tipo = df.attrs.get('col_tipo')
    col_depto = df.attrs.get('col_depto')
    
    # Sidebar con filtros
    st.sidebar.header("🔍 Filtros")
    
    if col_depto:
        deptos = st.sidebar.multiselect(
            "Departamento",
            options=sorted(df[col_depto].dropna().unique()),
            default=sorted(df[col_depto].dropna().unique())
        )
        df_filtrado = df[df[col_depto].isin(deptos)] if deptos else df
    else:
        df_filtrado = df
    
    # KPIs
    st.subheader("📈 Indicadores Clave")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Proyectos", len(df_filtrado))
    with col2:
        st.metric("Monto Total", f"Q{df_filtrado[col_monto].sum():,.0f}")
    with col3:
        st.metric("🔴 Alto Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🔴 Alto']))
    with col4:
        st.metric("🟡 Medio Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🟡 Medio']))
    with col5:
        st.metric("⚠️ Proveedores Riesgosos", len(df_filtrado[df_filtrado['Proveedor_Riesgoso'] == '⚠️ Sí'].drop_duplicates(subset=[col_proveedor])))
    
    st.markdown("---")
    
    # Gráfico de proveedores riesgosos
    st.subheader("🚨 Proveedores con Patrón Sospechoso")
    
    if df_filtrado['Proveedor_Riesgoso'].value_counts().get('⚠️ Sí', 0) > 0:
        proveedores_riesgosos = df_filtrado[df_filtrado['Proveedor_Riesgoso'] == '⚠️ Sí'][col_proveedor].unique()
        
        for proveedor in proveedores_riesgosos:
            df_prov = df_filtrado[df_filtrado[col_proveedor] == proveedor]
            st.markdown(f"""
            <div class="risk-high">
                <b>⚠️ {proveedor}</b><br>
                📊 {len(df_prov)} contratos | 💰 Monto promedio: Q{df_prov[col_monto].mean():,.0f} | 📉 Variación: {df_prov[col_monto].std()/df_prov[col_monto].mean():.1%}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ No se detectaron proveedores con patrón sospechoso")
    
    st.markdown("---")
    
    # Gráficos
    if col_monto and col_depto:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Montos por Departamento")
            monto_depto = df_filtrado.groupby(col_depto)[col_monto].sum().sort_values()
            fig = px.bar(x=monto_depto.values, y=monto_depto.index, orientation='h')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Montos por Tipo de Estudio")
            monto_tipo = df_filtrado.groupby(col_tipo)[col_monto].sum().sort_values()
            fig = px.pie(values=monto_tipo.values, names=monto_tipo.index)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de datos
    st.subheader("📋 Detalle de Contratos")
    
    columnas_mostrar = []
    for col in [col_proveedor, col_tipo, col_depto, col_monto, 'Proveedor_Riesgoso', 'Nivel_Riesgo']:
        if col and col in df_filtrado.columns:
            columnas_mostrar.append(col)
    
    tabla_mostrar = df_filtrado[columnas_mostrar].copy()
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
    
    if col_monto:
        styled_df = styled_df.format({col_monto: '{:,.0f}'})
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Recomendaciones
    st.markdown("---")
    st.subheader("📋 Recomendaciones para Auditoría")
    
    recomendaciones = []
    
    proveedores_riesgosos_lista = df_filtrado[df_filtrado['Proveedor_Riesgoso'] == '⚠️ Sí'][col_proveedor].unique()
    if len(proveedores_riesgosos_lista) > 0:
        recomendaciones.append(f"🔴 **Auditar a {len(proveedores_riesgosos_lista)} proveedores** que ganaron múltiples contratos con montos muy similares")
    
    proyectos_alto_riesgo = df_filtrado[df_filtrado['Nivel_Riesgo'] == '🔴 Alto']
    if len(proyectos_alto_riesgo) > 0:
        recomendaciones.append(f"🟠 **Revisar {len(proyectos_alto_riesgo)} proyectos en alto riesgo** por montos significativamente superiores al promedio")
    
    if not recomendaciones:
        st.success("✅ No se detectaron anomalías significativas")
    
    for rec in recomendaciones:
        st.markdown(f"- {rec}")

if __name__ == "__main__":
    main()
