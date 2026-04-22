import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard de Proyectos", layout="wide")

@st.cache_data
def load_data():
    """Carga el archivo Excel"""
    df = pd.read_excel("DataG18.xlsx", sheet_name=0)
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Identificar columnas importantes (búsqueda flexible)
    col_monto = next((col for col in df.columns if 'monto' in col.lower()), None)
    col_depto = next((col for col in df.columns if 'departamento' in col.lower()), None)
    col_nit = next((col for col in df.columns if 'nit' in col.lower()), None)
    col_revisor = next((col for col in df.columns if 'revisor' in col.lower()), None)
    col_snip = next((col for col in df.columns if 'snip' in col.lower()), None)
    
    # Detectar anomalías
    if col_nit:
        df['Nit_sospechoso'] = df[col_nit].astype(str).apply(
            lambda x: '⚠️ Sí' if (not str(x).replace('-', '').isdigit() or len(str(x).replace('-', '')) < 7) else '✅ No'
        )
    else:
        df['Nit_sospechoso'] = '❓ N/A'
    
    if col_monto:
        df['Monto_redondo'] = df[col_monto].apply(
            lambda x: '⚠️ Sí' if pd.notna(x) and x > 0 and x % 10000 == 0 else '✅ No'
        )
    
    # Calcular nivel de riesgo
    def calcular_riesgo(row):
        riesgo = 0
        if row.get('Nit_sospechoso', '') == '⚠️ Sí':
            riesgo += 2
        if row.get('Monto_redondo', '') == '⚠️ Sí':
            riesgo += 1
        if col_revisor and (pd.isna(row.get(col_revisor)) or row.get(col_revisor) == 'N.D.'):
            riesgo += 1
        if col_snip and (pd.isna(row.get(col_snip)) or str(row.get(col_snip)) == 'NA' or str(row.get(col_snip)) == 'None'):
            riesgo += 1
        
        if riesgo >= 3:
            return '🔴 Alto'
        elif riesgo >= 1:
            return '🟡 Medio'
        else:
            return '🟢 Bajo'
    
    df['Nivel_Riesgo'] = df.apply(calcular_riesgo, axis=1)
    
    # Guardar nombres de columnas para usarlas después
    df.attrs['col_monto'] = col_monto
    df.attrs['col_depto'] = col_depto
    df.attrs['col_nit'] = col_nit
    df.attrs['col_revisor'] = col_revisor
    df.attrs['col_snip'] = col_snip
    
    return df

def main():
    st.title("📊 Dashboard de Control de Proyectos de Infraestructura")
    st.markdown("---")
    
    df = load_data()
    
    # Obtener columnas importantes
    col_monto = df.attrs.get('col_monto')
    col_depto = df.attrs.get('col_depto')
    col_nit = df.attrs.get('col_nit')
    col_revisor = df.attrs.get('col_revisor')
    
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
    
    # ========== KPI CARDS ==========
    st.subheader("📈 Indicadores Clave")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Registros", len(df_filtrado))
    with col2:
        if col_monto:
            st.metric("Monto Total", f"Q{df_filtrado[col_monto].sum():,.0f}")
    with col3:
        st.metric("⚠️ Alto Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🔴 Alto']))
    with col4:
        st.metric("🟡 Medio Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🟡 Medio']))
    with col5:
        st.metric("🟢 Bajo Riesgo", len(df_filtrado[df_filtrado['Nivel_Riesgo'] == '🟢 Bajo']))
    
    st.markdown("---")
    
    # ========== GRÁFICOS ==========
    if col_monto and col_depto:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Montos por Departamento")
            monto_depto = df_filtrado.groupby(col_depto)[col_monto].sum().sort_values(ascending=True)
            fig = px.bar(
                x=monto_depto.values, 
                y=monto_depto.index,
                orientation='h',
                color=monto_depto.values,
                color_continuous_scale='Viridis',
                labels={'x': 'Monto Total (Q)', 'y': 'Departamento'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🚨 Nivel de Riesgo")
            riesgo_counts = df_filtrado['Nivel_Riesgo'].value_counts()
            fig = px.pie(
                values=riesgo_counts.values,
                names=riesgo_counts.index,
                color=riesgo_counts.index,
                color_discrete_map={'🔴 Alto': 'red', '🟡 Medio': 'orange', '🟢 Bajo': 'green'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # ========== SEÑALES DE ALERTA ==========
    st.subheader("⚠️ Señales de Alerta Detectadas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nit_sospechosos = len(df_filtrado[df_filtrado['Nit_sospechoso'] == '⚠️ Sí'])
        st.metric("🔴 NIT Sospechosos", nit_sospechosos)
    
    with col2:
        if col_monto:
            montos_redondos = len(df_filtrado[df_filtrado['Monto_redondo'] == '⚠️ Sí'])
            st.metric("🟠 Montos Redondos", montos_redondos)
    
    with col3:
        if col_revisor:
            sin_revisor = len(df_filtrado[df_filtrado[col_revisor].isna() | (df_filtrado[col_revisor] == 'N.D.')])
            st.metric("🟡 Sin Revisor", sin_revisor)
    
    with col4:
        if col_snip := df.attrs.get('col_snip'):
            sin_snip = len(df_filtrado[df_filtrado[col_snip].isna() | (df_filtrado[col_snip].astype(str) == 'NA')])
            st.metric("📌 Sin SNIP", sin_snip)
    
    st.markdown("---")
    
    # ========== TABLA DE DATOS ==========
    st.subheader("📋 Detalle de Contratos")
    
    # Seleccionar columnas para mostrar
    columnas_mostrar = []
    for col in ['SNIP', 'Proyecto', col_depto, 'Municipio', col_monto, col_revisor, 'Nivel_Riesgo', 'Nit_sospechoso']:
        if col and col in df_filtrado.columns:
            columnas_mostrar.append(col)
    
    # Reemplazar None con strings vacíos para evitar errores
    tabla_mostrar = df_filtrado[columnas_mostrar].copy()
    tabla_mostrar = tabla_mostrar.fillna('')
    
    # Aplicar estilo condicional
    def color_riesgo(val):
        if '🔴 Alto' in str(val):
            return 'background-color: #ffcccc'
        elif '🟡 Medio' in str(val):
            return 'background-color: #fff3cc'
        elif '🟢 Bajo' in str(val):
            return 'background-color: #ccffcc'
        return ''
    
    styled_df = tabla_mostrar.style.applymap(color_riesgo, subset=['Nivel_Riesgo'])
    
    if col_monto:
        styled_df = styled_df.format({col_monto: '{:,.0f}'})
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # ========== RECOMENDACIONES ==========
    st.markdown("---")
    st.subheader("📋 Recomendaciones para Auditoría")
    
    recomendaciones = []
    
    if nit_sospechosos > 0:
        recomendaciones.append("🔴 **Validar NIT sospechosos** - Hay formuladores con NIT que no cumplen el formato estándar guatemalteco")
    
    if col_monto and montos_redondos > 0:
        recomendaciones.append("🟠 **Revisar montos redondos** - Existen montos exactos que podrían indicar sobreprecio")
    
    if col_revisor and sin_revisor > 0:
        recomendaciones.append("🟡 **Identificar revisores no declarados** - Contratos sin revisor asignado")
    
    if col_snip := df.attrs.get('col_snip'):
        if sin_snip > 0:
            recomendaciones.append("📌 **Regularizar proyectos sin SNIP** - Proyectos sin código único de identificación")
    
    for rec in recomendaciones:
        st.markdown(f"- {rec}")
    
    if not recomendaciones:
        st.success("✅ No se detectaron anomalías significativas en los datos filtrados")
    
    # Footer
    st.markdown("---")
    st.caption(f"📅 Última actualización: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
