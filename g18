# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from io import BytesIO
import base64

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Proyectos de Infraestructura",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado
st.markdown("""
<style>
    .stAlert {
        border-radius: 10px;
    }
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    .risk-high {
        background-color: #ffcccc;
        padding: 10px;
        border-radius: 10px;
        border-left: 5px solid red;
    }
    .risk-medium {
        background-color: #fff3cc;
        padding: 10px;
        border-radius: 10px;
        border-left: 5px solid orange;
    }
    .risk-low {
        background-color: #ccffcc;
        padding: 10px;
        border-radius: 10px;
        border-left: 5px solid green;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CARGA Y LIMPIEZA DE DATOS
# ============================================

@st.cache_data
def load_data():
    """Carga y limpia los datos del Excel"""
    
    # Datos extraídos del archivo (primeras filas como muestra)
    # En producción, usar: pd.read_excel('Informe Grupo 18.xlsx')
    
    data = {
        'SNIP': [358282, 358282, 61755, 61755, 317391, 'NA', 'NA', 317628, 317628, 343772, 343772, 359337, 359337, 242011, 242011, 359312, 359312, 359340, 359340, 331396],
        'Proyecto': [
            'REPOSICION CENTRO DE SALUD SANTO TOMAS DE CASTILLA',
            'REPOSICION CENTRO DE SALUD SANTO TOMAS DE CASTILLA',
            'CONSTRUCCION HOSPITAL CABECERA MUNICIPAL DE SAN PEDRO NECTA',
            'CONSTRUCCION HOSPITAL CABECERA MUNICIPAL DE SAN PEDRO NECTA',
            'MEJORAMIENTO INSTITUTO BASICO INEB JUSTO RUFINO BARRIOS',
            'REMOZAMIENTO COPB ANEXO A EORM CASERÍO BOCA ANCHA',
            'REMOZAMIENTO EORM ALDEA EL BONGO',
            'REPOSICION CENTRO DE ATENCION PERMANENTE (CAP)',
            'REPOSICION CENTRO DE ATENCION PERMANENTE (CAP)',
            'MEJORAMIENTO ESCUELA OFICIAL RURAL MIXTA',
            'MEJORAMIENTO ESCUELA OFICIAL RURAL MIXTA',
            'REPOSICION PUESTO DE SALUD',
            'REPOSICION PUESTO DE SALUD',
            'CONSTRUCCION INSTITUTO MIXTO DIVERSIFICADO',
            'CONSTRUCCION INSTITUTO MIXTO DIVERSIFICADO',
            'MEJORAMIENTO INSTITUTO NACIONAL DE EDUCACIÓN BÁSICA',
            'MEJORAMIENTO INSTITUTO NACIONAL DE EDUCACIÓN BÁSICA',
            'MEJORAMIENTO INEB ADSCRITO',
            'MEJORAMIENTO INEB ADSCRITO',
            'MEJORAMIENTO ESCUELA OFICIAL URBANA MIXTA'
        ],
        'Municipio': ['PUERTO BARRIOS', 'PUERTO BARRIOS', 'SAN PEDRO NECTA', 'SAN PEDRO NECTA', 'SAN MARCOS', 'EL ESTOR', 'EL ESTOR', 'PAJAPITA', 'PAJAPITA', 'IXCAN', 'IXCAN', 'SANTA MARIA CHIQUIMULA', 'SANTA MARIA CHIQUIMULA', 'IXCAN', 'IXCAN', 'HUEHUETENANGO', 'HUEHUETENANGO', 'ESCUINTLA', 'ESCUINTLA', 'SAN ANTONIO HUISTA'],
        'Departamento': ['IZABAL', 'IZABAL', 'HUEHUETENANGO', 'HUEHUETENANGO', 'SAN MARCOS', 'IZABAL', 'IZABAL', 'SAN MARCOS', 'SAN MARCOS', 'QUICHE', 'QUICHE', 'TOTONICAPAN', 'TOTONICAPAN', 'QUICHE', 'QUICHE', 'HUEHUETENANGO', 'HUEHUETENANGO', 'ESCUINTLA', 'ESCUINTLA', 'HUEHUETENANGO'],
        'No_Contrato': ['01-2025-181-UCEE', '01-2025-181-UCEE', '02-2025-181-UCEE', '02-2025-181-UCEE', '03-2025-181-UCEE', '04-2025-181-UCEE', '04-2025-181-UCEE', '06-2025-181-UCEE', '06-2025-181-UCEE', '07-2025-181-UCEE', '07-2025-181-UCEE', '08-2025-181-UCEE', '08-2025-181-UCEE', '09-2025-181-UCEE', '09-2025-181-UCEE', '10-2025-181-UCEE', '10-2025-181-UCEE', '11-2025-181-UCEE', '11-2025-181-UCEE', '12-2025-181-UCEE'],
        'Formulador': ['OCHOA OROZCO WENER ARMANDO', 'OCHOA OROZCO WENER ARMANDO', 'MONTERROSO NAJERA FERNANDO RAFAEL', 'MONTERROSO NAJERA FERNANDO RAFAEL', 'TENÍ POP WILMER DAN', 'CALDERÓN DE LEÓN PAÚL ALBERTO', 'CALDERÓN DE LEÓN PAÚL ALBERTO', 'RODRÍGUEZ FLORES MARCO LEONEL', 'RODRÍGUEZ FLORES MARCO LEONEL', 'ENRÍQUEZ ADOLFO DAVID ESTUARDO', 'ENRÍQUEZ ADOLFO DAVID ESTUARDO', 'ARA DONIS IVÁN ABISAI', 'ARA DONIS IVÁN ABISAI', 'CALDERÓN RODAS FEDEDMAN FEIDER', 'CALDERÓN RODAS FEDEDMAN FEIDER', 'SAQUIC LÓPEZ MYNOR OSWALDO', 'SAQUIC LÓPEZ MYNOR OSWALDO', 'BOROR HERNÁNDEZ LUIS PEDRO', 'BOROR HERNÁNDEZ LUIS PEDRO', 'ALONZO LÓPEZ GUILLERMO GEOVANI'],
        'Nit': ['87017679', '87017679', '19089414', '19089414', '8321167', '1267866K', '1267866K', '35768274', '35768274', '1967760K', '1967760K', '67781217', '67781217', '15765873', '15765873', '67717802', '67717802', '94924171', '94924171', '18184685'],
        'Producto': [
            'ESTUDIO GEOTÉCNICO (LICUEFACCION)',
            'ESTUDIO HIDROLÓGICO',
            'ESTUDIO HIDROLOGICO',
            'ESTUDIO GEOTECNICO (ESTABILIDAD DE LADERA)',
            'ESTUDIO GEOTÉCNICO TIPO II',
            'Fase A: Remozamiento',
            'Fase B: Remozamiento',
            'FASE A: Planificación',
            'FASE B: Planificación',
            'FASE A: Planificación',
            'FASE B: Planificación',
            'FASE A: Planificación',
            'FASE B: Planificación',
            'FASE A: Planificación',
            'FASE B: Planificación',
            'FASE A: Planificación',
            'FASE B: Planificación',
            'FASE A: Planificación',
            'FASE B: Planificación',
            'FASE A: Planificación'
        ],
        'Fecha_Informe': ['2025-03-31', '2025-05-30', '2025-05-26', '2025-05-30', '2025-04-30', '2025-08-31', '2025-08-31', '2025-07-31', '2025-10-31', '2025-07-31', '2025-09-30', '2025-07-31', '2025-09-30', '2025-07-31', '2025-09-30', '2025-07-31', '2025-09-30', '2025-07-31', '2025-09-30', '2025-07-31'],
        'Fecha_Factura': ['2025-04-07', '2025-05-31', '2025-05-31', '2025-05-31', '2025-04-30', '2025-08-31', '2025-08-31', '2025-08-31', '2025-10-31', '2025-08-31', '2025-10-31', '2025-08-31', '2025-10-31', '2025-08-31', '2025-10-31', '2025-08-31', '2025-10-31', '2025-08-31', '2025-10-31', '2025-08-31'],
        'Monto': [75000, 88000, 89000, 170000, 69000, 112000, 151200, 201600, 563360, 226800, 453600, 106400, 392000, 224000, 448000, 151200, 425600, 229600, 497280, 218400],
        'Revisor': ['Ing. Juan Carlos Amado', 'Ing. Juan Carlos Amado', 'Ing. Juan Carlos Amado', 'Ing. Juan Carlos Amado', 'Ing. Juan Carlos Amado', 'N.D.', 'N.D.', 'ARQ. JULIO MONTENEGRO', '', 'ARQ. ANDREA CESETE VASQUEZ', 'ARQ. ANDREA CESETE VASQUEZ', 'ING. BYRON MELVIN TUL VELÁSQUEZ', 'ING. BYRON MELVIN TUL VELÁSQUEZ', 'N.D.', 'N.D.', 'ARQ. DIEGO FELIPE MEJÍA GUZMÁN', 'N.D.', 'ING. BYRON MELVIN TUL VELÁSQUEZ', 'N.D.', 'ARQ. MARÍA JOSÉ VILLAR FRANCO'],
        'Tipo_Estudio': ['Geotecnico', 'Hidrologico', 'Hidrologico', 'Geotecnico', 'Geotecnico', 'Remozamiento', 'Remozamiento', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion', 'Planificacion']
    }
    
    df = pd.DataFrame(data)
    
    # Convertir fechas
    df['Fecha_Informe'] = pd.to_datetime(df['Fecha_Informe'])
    df['Fecha_Factura'] = pd.to_datetime(df['Fecha_Factura'])
    
    # Calcular días entre informe y factura
    df['Dias_entrega'] = (df['Fecha_Factura'] - df['Fecha_Informe']).dt.days
    
    # Detectar anomalías en NIT
    df['Nit_sospechoso'] = df['Nit'].apply(
        lambda x: 'Sí' if (not str(x).isdigit() or len(str(x)) < 8) else 'No'
    )
    
    # Detectar montos redondos
    df['Monto_redondo'] = df['Monto'].apply(
        lambda x: 'Sí' if x % 1000 == 0 else 'No'
    )
    
    # Crear columna de riesgo
    def calcular_riesgo(row):
        riesgo = 0
        if row['Nit_sospechoso'] == 'Sí':
            riesgo += 2
        if row['Monto_redondo'] == 'Sí' and row['Monto'] in [90000, 60000, 30000]:
            riesgo += 2
        if row['Revisor'] == 'N.D.' or row['Revisor'] == '':
            riesgo += 1
        if row['Dias_entrega'] == 0:
            riesgo += 1
        if row['SNIP'] == 'NA':
            riesgo += 1
        
        if riesgo >= 3:
            return 'Alto'
        elif riesgo >= 1:
            return 'Medio'
        else:
            return 'Bajo'
    
    df['Nivel_Riesgo'] = df.apply(calcular_riesgo, axis=1)
    
    return df

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def descargar_excel(df):
    """Genera archivo Excel para descarga"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Datos', index=False)
    processed_data = output.getvalue()
    return processed_data

def resaltar_riesgo(val):
    """Resalta celdas según nivel de riesgo"""
    if val == 'Alto':
        return 'background-color: #ffcccc'
    elif val == 'Medio':
        return 'background-color: #fff3cc'
    elif val == 'Bajo':
        return 'background-color: #ccffcc'
    return ''

# ============================================
# DASHBOARD PRINCIPAL
# ============================================

def main():
    st.title("📊 Dashboard de Control de Proyectos de Infraestructura")
    st.markdown("---")
    
    # Cargar datos
    df = load_data()
    
    # Sidebar - Filtros
    st.sidebar.header("🔍 Filtros")
    
    # Filtros multiselect
    deptos = st.sidebar.multiselect(
        "Departamento",
        options=sorted(df['Departamento'].unique()),
        default=sorted(df['Departamento'].unique())
    )
    
    tipos = st.sidebar.multiselect(
        "Tipo de Estudio",
        options=sorted(df['Tipo_Estudio'].unique()),
        default=sorted(df['Tipo_Estudio'].unique())
    )
    
    riesgo_filtro = st.sidebar.multiselect(
        "Nivel de Riesgo",
        options=['Alto', 'Medio', 'Bajo'],
        default=['Alto', 'Medio', 'Bajo']
    )
    
    # Aplicar filtros
    df_filtrado = df[
        (df['Departamento'].isin(deptos)) &
        (df['Tipo_Estudio'].isin(tipos)) &
        (df['Nivel_Riesgo'].isin(riesgo_filtro))
    ]
    
    # ========== KPI CARDS ==========
    st.subheader("📈 Indicadores Clave")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Contratos", df_filtrado['No_Contrato'].nunique())
    with col2:
        st.metric("Monto Total", f"Q{df_filtrado['Monto'].sum():,.0f}")
    with col3:
        st.metric("Monto Promedio", f"Q{df_filtrado['Monto'].mean():,.0f}")
    with col4:
        riesgo_alto = len(df_filtrado[df_filtrado['Nivel_Riesgo'] == 'Alto'])
        st.metric("⚠️ Contratos Alto Riesgo", riesgo_alto)
    with col5:
        st.metric("📅 Días Promedio Entrega", f"{df_filtrado['Dias_entrega'].mean():.0f}")
    
    st.markdown("---")
    
    # ========== GRÁFICOS PRINCIPALES ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Montos por Departamento")
        monto_depto = df_filtrado.groupby('Departamento')['Monto'].sum().sort_values(ascending=True)
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
        st.subheader("📊 Distribución por Tipo de Estudio")
        tipo_counts = df_filtrado['Tipo_Estudio'].value_counts()
        fig = px.pie(
            values=tipo_counts.values,
            names=tipo_counts.index,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== GRÁFICO DE RIESGO ==========
    st.subheader("🚨 Análisis de Riesgos por Contrato")
    
    col1, col2 = st.columns(2)
    
    with col1:
        riesgo_counts = df_filtrado['Nivel_Riesgo'].value_counts()
        fig = px.bar(
            x=riesgo_counts.index,
            y=riesgo_counts.values,
            color=riesgo_counts.index,
            color_discrete_map={'Alto': 'red', 'Medio': 'orange', 'Bajo': 'green'},
            labels={'x': 'Nivel de Riesgo', 'y': 'Cantidad de Registros'}
        )
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Montos por nivel de riesgo
        monto_riesgo = df_filtrado.groupby('Nivel_Riesgo')['Monto'].sum().reset_index()
        fig = px.pie(
            monto_riesgo,
            values='Monto',
            names='Nivel_Riesgo',
            color='Nivel_Riesgo',
            color_discrete_map={'Alto': 'red', 'Medio': 'orange', 'Bajo': 'green'},
            title='Monto Total por Nivel de Riesgo'
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== SEÑALES DE ALERTA ==========
    st.subheader("⚠️ Señales de Alerta Detectadas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nit_sospechosos = len(df_filtrado[df_filtrado['Nit_sospechoso'] == 'Sí'])
        st.metric("🔴 NIT Sospechosos", nit_sospechosos)
    
    with col2:
        montos_redondos = len(df_filtrado[df_filtrado['Monto_redondo'] == 'Sí'])
        st.metric("🟠 Montos Redondos", montos_redondos)
    
    with col3:
        sin_revisor = len(df_filtrado[(df_filtrado['Revisor'] == 'N.D.') | (df_filtrado['Revisor'] == '')])
        st.metric("🟡 Sin Revisor Declarado", sin_revisor)
    
    with col4:
        entrega_mismo_dia = len(df_filtrado[df_filtrado['Dias_entrega'] == 0])
        st.metric("📅 Facturación Mismo Día", entrega_mismo_dia)
    
    # ========== TABLA DE DATOS CON RIESGO ==========
    st.subheader("📋 Detalle de Contratos")
    
    # Preparar tabla para mostrar
    tabla_mostrar = df_filtrado[[
        'SNIP', 'Proyecto', 'Municipio', 'Departamento', 
        'No_Contrato', 'Formulador', 'Monto', 'Revisor', 
        'Tipo_Estudio', 'Nivel_Riesgo', 'Nit_sospechoso', 
        'Monto_redondo', 'Dias_entrega'
    ]].copy()
    
    # Renombrar columnas para mejor visualización
    tabla_mostrar.columns = [
        'SNIP', 'Proyecto', 'Municipio', 'Departamento',
        'No. Contrato', 'Formulador', 'Monto (Q)', 'Revisor',
        'Tipo Estudio', 'Nivel Riesgo', 'NIT Sospechoso',
        'Monto Redondo', 'Días Entrega'
    ]
    
    # Aplicar estilo condicional
    styled_df = tabla_mostrar.style.applymap(
        resaltar_riesgo, subset=['Nivel Riesgo']
    ).format({'Monto (Q)': '{:,.0f}'})
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # ========== BOTONES DE DESCARGA ==========
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df_filtrado.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name="proyectos_filtrados.csv",
            mime="text/csv"
        )
    
    with col2:
        excel_data = descargar_excel(df_filtrado)
        st.download_button(
            label="📊 Descargar Excel",
            data=excel_data,
            file_name="proyectos_filtrados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    with col3:
        st.info(f"📌 Mostrando {len(df_filtrado)} registros")
    
    # ========== ANÁLISIS DETALLADO POR CONTRATO ==========
    st.markdown("---")
    st.subheader("🔍 Análisis Detallado por Contrato")
    
    # Selector de contrato
    contratos = sorted(df_filtrado['No_Contrato'].unique())
    contrato_seleccionado = st.selectbox("Seleccionar Contrato", contratos)
    
    if contrato_seleccionado:
        df_contrato = df_filtrado[df_filtrado['No_Contrato'] == contrato_seleccionado]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Información del Contrato:**
            - 📄 Número: `{contrato_seleccionado}`
            - 🏢 SNIP: `{df_contrato['SNIP'].iloc[0]}`
            - 📍 Departamento: `{df_contrato['Departamento'].iloc[0]}`
            - 🏘️ Municipio: `{df_contrato['Municipio'].iloc[0]}`
            - 👤 Formulador: `{df_contrato['Formulador'].iloc[0]}`
            - 🔍 Revisor: `{df_contrato['Revisor'].iloc[0]}`
            - ⚠️ Nivel Riesgo: `{df_contrato['Nivel_Riesgo'].iloc[0]}`
            """)
        
        with col2:
            st.markdown(f"""
            **Resumen Económico:**
            - 💰 Monto Total: `Q{df_contrato['Monto'].sum():,.0f}`
            - 📊 Promedio por Producto: `Q{df_contrato['Monto'].mean():,.0f}`
            - 🧾 Cantidad de Productos: `{len(df_contrato)}`
            - 📅 Días Promedio Entrega: `{df_contrato['Dias_entrega'].mean():.0f}`
            """)
        
        # Mostrar productos del contrato
        st.markdown("**Productos / Fases:**")
        st.dataframe(
            df_contrato[['Producto', 'Monto', 'Fecha_Informe', 'Fecha_Factura', 'Dias_entrega']],
            use_container_width=True
        )
    
    # ========== RECOMENDACIONES ==========
    st.markdown("---")
    st.subheader("📋 Recomendaciones para Auditoría")
    
    # Generar recomendaciones basadas en datos
    alertas = []
    
    if len(df_filtrado[df_filtrado['Nit_sospechoso'] == 'Sí']) > 0:
        alertas.append("🔴 **Validar NIT sospechosos** - Hay formuladores con NIT que no cumplen el formato estándar guatemalteco")
    
    if len(df_filtrado[df_filtrado['Monto'].isin([90000, 60000, 30000])]) > 0:
        alertas.append("🟠 **Revisar montos redondos repetidos** - Existen múltiples contratos por Q90,000, Q60,000 y Q30,000")
    
    if len(df_filtrado[df_filtrado['Revisor'] == 'N.D.']) > 0:
        alertas.append("🟡 **Identificar revisores no declarados** - Varios contratos no tienen revisor asignado")
    
    if len(df_filtrado[df_filtrado['SNIP'] == 'NA']) > 0:
        alertas.append("📌 **Regularizar proyectos sin SNIP** - Proyectos sin código único de identificación")
    
    if len(df_filtrado[df_filtrado['Dias_entrega'] == 0]) > 0:
        alertas.append("⏰ **Investigar facturaciones el mismo día** - Imposible facturar el mismo día de la entrega del informe")
    
    for alerta in alertas:
        st.markdown(f"- {alerta}")
    
    if not alertas:
        st.success("✅ No se detectaron anomalías significativas en los datos filtrados")
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.caption(f"📅 Última actualización: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} | Dashboard de Control de Proyectos")

if __name__ == "__main__":
    main()
