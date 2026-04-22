import streamlit as st
import pandas as pd


st.set_page_config(page_title="Dashboard", layout="wide")

@st.cache_data
def load_data():
    """Carga el archivo Excel"""
    df = pd.read_excel("DataG18.xlsx", sheet_name=0)
    return df  # ← Este return DENTRO de la función

def main():
    st.title("📊 Dashboard de Proyectos")
    
    try:
        df = load_data()
        st.success(f"✅ Datos cargados: {len(df)} filas")
        
        # Vista previa
        st.subheader("Vista previa")
        st.dataframe(df.head(10))
        
        # Métricas básicas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Proyectos", len(df))
        with col2:
            if 'Monto' in df.columns:
                st.metric("Monto Total", f"Q{df['Monto'].sum():,.0f}")
        with col3:
            if 'Departamento' in df.columns:
                st.metric("Departamentos", df['Departamento'].nunique())
        
        # Gráfico simple con matplotlib
        if 'Departamento' in df.columns and 'Monto' in df.columns:
            st.subheader("Montos por Departamento")
            monto_depto = df.groupby('Departamento')['Monto'].sum().sort_values()
            fig, ax = plt.subplots()
            monto_depto.plot(kind='barh', ax=ax)
            ax.set_xlabel('Monto (Q)')
            st.pyplot(fig)
            
    except Exception as e:
        st.error(f"Error: {e}")

if __name__ == "__main__":
    main()  # ← Esto llama a la función main
