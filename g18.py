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
    col_contrato = next((col for col in df.columns if 'contrato' in col.lower()), None)
    
    if not all([col_monto, col_proveedor, col_tipo, col_contrato]):
        st.warning("No se encontraron todas las columnas necesarias")
        return df
    
    # ============================================
    # PASO 1: Agrupar por CONTRATO (sumar productos del mismo contrato)
    # ============================================
    df_contratos = df.groupby(col_contrato).agg({
        col_proveedor: 'first',
        col_monto: 'sum',  # Suma de todas las fases/productos
        col_tipo: lambda x: ', '.join(x.unique()),
        col_depto: 'first'
    }).reset_index()
    
    df_contratos.columns = ['No_Contrato', 'Proveedor', 'Monto_Total', 'Tipos_Estudio', 'Departamento']
    
    # ============================================
    # PASO 2: Detectar proveedores con múltiples CONTRATOS sospechosos
    # ============================================
    proveedor_stats = df_contratos.groupby('Proveedor').agg({
        'Monto_Total': ['count', 'mean', 'std']
    }).round(0)
    
    proveedor_stats.columns = ['num_contratos', 'monto_promedio', 'desviacion']
    proveedor_stats['coeficiente_var'] = proveedor_stats['desviacion'] / proveedor_stats['monto_promedio']
    
    # Un proveedor es riesgoso si:
    # - Tiene 2 o más CONTRATOS DIFERENTES
    # - La variación entre contratos es menor al 20% (montos muy similares)
    proveedores_riesgosos = proveedor_stats[
        (proveedor_stats['num_contratos'] >= 2) & 
        (proveedor_stats['coeficiente_var'] < 0.2)
    ].index.tolist()
    
    # Marcar contratos de proveedores riesgosos
    df_contratos['Proveedor_Riesgoso'] = df_contratos['Proveedor'].apply(
        lambda x: '⚠️ Sí' if x in proveedores_riesgosos else '✅ No'
    )
    
    # ============================================
    # PASO 3: Calcular percentiles por tipo de estudio (a nivel contrato)
    # ============================================
    percentiles_por_tipo = {}
    for tipo in df_contratos['Tipos_Estudio'].unique():
        # Para cada combinación de tipos, calcular percentiles
        montos_tipo = df_contratos[df_contratos['Tipos_Estudio'] == tipo]['Monto_Total']
        if len(montos_tipo) > 0:
            percentiles_por_tipo[tipo] = {
                'p75': montos_tipo.quantile(0.75),
                'p90': montos_tipo.quantile(0.90)
            }
    
    # ============================================
    # PASO 4: Calcular nivel de riesgo por CONTRATO
    # ============================================
    def calcular_riesgo(row):
        riesgo = 0
        
        # Criterio 1: Proveedor con múltiples contratos similares (+2)
        if row['Proveedor_Riesgoso'] == '⚠️ Sí':
            riesgo += 2
        
        # Criterio 2: Monto del contrato en percentil alto (+1 o +2)
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
    
    # Guardar metadata
    df_contratos.attrs['col_monto'] = 'Monto_Total'
    df_contratos.attrs['col_proveedor'] = 'Proveedor'
    df_contratos.attrs['col_tipo'] = 'Tipos_Estudio'
    df_contratos.attrs['col_depto'] = 'Departamento'
    df_contratos.attrs['col_contrato'] = 'No_Contrato'
    df_contratos.attrs['proveedores_riesgosos'] = proveedores_riesgosos
    
    return df_contratos

def main():
    st.title("📊 Dashboard de Control de Proyectos")
    st.markdown("---")
    
    df = load_data()
    
    if df.empty:
        st.warning("No hay datos para mostrar")
        return
    
    col_monto = 'Monto_Total'
    col_proveedor = 'Proveedor'
    col_tipo = 'Tipos_Estudio'
    col_depto = 'Departamento'
    col_contrato = 'No_Contrato'
    
    # Sidebar con filtros
    st.sidebar.header("🔍 Filtros")
    
    if col_depto in df.columns:
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
        st.metric("Total Contratos", len(df_filtrado))
    with col2:
        st.metric("Monto Total", f"Q{df_filtrado[col_monto].sum():,.0f}")
    with col3:
        st.metric("🔴 Alto Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🔴 Alto']))
    with col4:
        st.metric("🟡 Medio Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🟡 Medio']))
    with col5:
        num_proveedores_riesgosos = len(df_filtrado[df_filtrado['Proveedor_Riesgoso'] == '⚠️ Sí'][col_proveedor].unique())
        st.metric("⚠️ Proveedores con Patrón", num_proveedores_riesgosos)
    
    st.markdown("---")
    
    # Proveedores sospechosos (con múltiples contratos similares)
    st.subheader("🚨 Proveedores con Múltiples Contratos de Montos Similares")
    
    proveedores_riesgosos = df_filtrado[df_filtrado['Proveedor_Riesgoso'] == '⚠️ Sí'][col_proveedor].unique()
    
    if len(proveedores_riesgosos) > 0:
        for proveedor in proveedores_riesgosos:
            df_prov = df_filtrado[df_filtrado[col_proveedor] == proveedor]
            
            # Calcular estadísticas
            num_contratos = len(df_prov)
            monto_promedio = df_prov[col_monto].mean()
            monto_min = df_prov[col_monto].min()
            monto_max = df_prov[col_monto].max()
            variacion = (df_prov[col_monto].std() / monto_promedio) if monto_promedio > 0 else 0
            
            st.markdown(f"""
            <div style="background-color: #ffcccc; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                <b>⚠️ {proveedor}</b><br>
                📄 {num_contratos} contratos | 💰 Promedio: Q{monto_promedio:,.0f}<br>
                📉 Rango: Q{monto_min:,.0f} - Q{monto_max:,.0f} | 📊 Variación: {variacion:.1%}
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar los contratos de este proveedor
            st.dataframe(df_prov[[col_contrato, col_monto, col_tipo, col_depto, 'Nivel_Riesgo']])
            st.markdown("---")
    else:
        st.info("✅ No se detectaron proveedores con múltiples contratos de montos muy similares")
    
    # Gráficos
    if col_monto and col_depto in df_filtrado.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Montos por Departamento")
            monto_depto = df_filtrado.groupby(col_depto)[col_monto].sum().sort_values()
            if len(monto_depto) > 0:
                fig = px.bar(x=monto_depto.values, y=monto_depto.index, orientation='h')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Montos por Tipo de Estudio")
            # Simplificar tipos (tomar el primero si hay múltiples)
            df_filtrado['Tipo_Principal'] = df_filtrado[col_tipo].apply(lambda x: x.split(',')[0] if pd.notna(x) else 'Otro')
            monto_tipo = df_filtrado.groupby('Tipo_Principal')[col_monto].sum().sort_values()
            if len(monto_tipo) > 0:
                fig = px.pie(values=monto_tipo.values, names=monto_tipo.index)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de contratos
    st.subheader("📋 Detalle de Contratos")
    
    columnas_mostrar = [col_contrato, col_proveedor, col_tipo, col_depto, col_monto, 'Proveedor_Riesgoso', 'Nivel_Riesgo']
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
    
    if col_monto in tabla_mostrar.columns:
        styled_df = styled_df.format({col_monto: '{:,.0f}'})
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Recomendaciones
    st.markdown("---")
    st.subheader("📋 Recomendaciones para Auditoría")
    
    recomendaciones = []
    
    if len(proveedores_riesgosos) > 0:
        recomendaciones.append(f"🔴 **Auditar a {len(proveedores_riesgosos)} proveedores** que ganaron múltiples contratos con montos muy similares (variación <20%)")
    
    num_alto_riesgo = len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🔴 Alto'])
    if num_alto_riesgo > 0:
        recomendaciones.append(f"🟠 **Revisar {num_alto_riesgo} contratos en alto riesgo** por montos significativamente superiores al percentil 90")
    
    if not recomendaciones:
        st.success("✅ No se detectaron anomalías significativas")
    else:
        for rec in recomendaciones:
            st.markdown(f"- {rec}")

if __name__ == "__main__":
    main()
