import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la página web
st.set_page_config(page_title="Mecánica de Suelos - Granulometría", layout="wide")

st.title("📊 Ensayo de Granulometría por Tamizado")
st.subheader("Manual de Carreteras v.8.202.3 / Adaptación NCh 165")

# --- 1. SECCIÓN DE DATOS INICIALES ---
st.sidebar.header("1. Datos del Cuarteo")
masa_total = st.sidebar.number_input("Masa Total de muestra a tamizar (g)", min_value=0.1, value=4500.0, step=1.0)

# --- 2. SECCIÓN DE INGRESO DE PESOS RETENIDOS ---
st.header("2. Registro de Pesos Retenidos por Tamiz")
st.write("Ingrese el peso retenido en gramos para cada tamiz correspondiente:")

datos_tamices = [
    (76.200, '3"'), (63.500, '2 1/2"'), (50.600, '2"'), (38.100, '1 1/2"'),
    (25.400, '1"'), (19.050, '3/4"'), (12.700, '1/2"'), (9.525, '3/8"'),
    (6.350, '1/4"'), (4.760, 'N° 4'), (2.380, 'N° 8'), (2.000, 'N° 10'),
    (1.190, 'N° 16'), (0.840, 'N° 20'), (0.590, 'N° 30'), (0.420, 'N° 40'),
    (0.300, 'N° 50'), (0.250, 'N° 60'), (0.180, 'N° 80'), (0.149, 'N° 100'),
    (0.074, 'N° 200')
]

pesos_ingresados = {}
col1, col2, col3 = st.columns(3)

for i, (abertura, tamiz) in enumerate(datos_tamices):
    label = f"{tamiz} ({abertura:.3f} mm)"
    if i % 3 == 0:
        with col1: pesos_ingresados[tamiz] = st.number_input(label, min_value=0.0, value=0.0, step=0.1, key=tamiz)
    elif i % 3 == 1:
        with col2: pesos_ingresados[tamiz] = st.number_input(label, min_value=0.0, value=0.0, step=0.1, key=tamiz)
    else:
        with col3: pesos_ingresados[tamiz] = st.number_input(label, min_value=0.0, value=0.0, step=0.1, key=tamiz)

st.markdown("---")
pesos_ingresados['Residuo'] = st.number_input("Residuo / Fondo (g)", min_value=0.0, value=0.0, step=0.1, key='Residuo')

# --- 3. PROCESAMIENTO Y CÁLCULOS ---
if st.button("Calcular Granulometría", type="primary"):
    lista_completa_tamices = datos_tamices + [(0.000, 'Residuo')]
    df = pd.DataFrame(lista_completa_tamices, columns=['Abertura (mm)', 'Tamiz'])
    df['Peso Retenido (g)'] = df['Tamiz'].map(pesos_ingresados).fillna(0.0)
    
    # Control de pérdida de masa
    suma_total_retenido = df['Peso Retenido (g)'].sum()
    error_gramos = masa_total - suma_total_retenido
    porcentaje_error = (abs(error_gramos) / masa_total) * 100
    
    # Cálculos granulométricos
    df['% Peso Retenido'] = (df['Peso Retenido (g)'] / masa_total) * 100
    df['% Peso Ret. Acumul.'] = df['% Peso Retenido'].cumsum()
    df['% Que Pasa'] = 100 - df['% Peso Ret. Acumul.']
    df.loc[df['Tamiz'] == 'Residuo', '% Que Pasa'] = 0.0
    
    # --- DETERMINACIÓN EXACTA DE TMA Y FILTER PARA GRÁFICO ---
    df_suelos = df[df['Abertura (mm)'] > 0].copy()
    
    # Buscamos el tamiz más grande que retiene material (donde % Que Pasa < 100)
    df_con_material = df_suelos[df_suelos['% Que Pasa'] < 99.99]
    
    if not df_con_material.empty:
        # El TMA real es el tamiz inmediatamente anterior (el más pequeño que tiene 100% que pasa)
        idx_primer_paso = df_con_material.index[0]
        if idx_primer_paso > 0:
            tma_mm = df_suelos.loc[idx_primer_paso - 1, 'Abertura (mm)']
            tma_nombre = df_suelos.loc[idx_primer_paso - 1, 'Tamiz']
        else:
            tma_mm = df_suelos.loc[idx_primer_paso, 'Abertura (mm)']
            tma_nombre = df_suelos.loc[idx_primer_paso, 'Tamiz']
    else:
        tma_mm = 76.200
        tma_nombre = '3"'

    # --- PRESENTACIÓN DE RESULTADOS ---
    st.header("3. Matriz de Resultados")
    st.metric(label="Tamaño Máximo Absoluto (TMA) Detectado", value=f"{tma_nombre} ({tma_mm:.3f} mm)")
        
    if porcentaje_error <= 1.0:
        st.success(f"✅ Ensayo Aprobado. Pérdida de masa: {error_gramos:.1f} g ({porcentaje_error:.2f}%).")
    else:
        st.error(f"❌ Ensayo Rechazado. Pérdida de masa: {error_gramos:.1f} g ({porcentaje_error:.2f}%).")
        
    df_visual = df.copy().round(2)
    st.dataframe(df_visual, use_container_width=True, hide_index=True)
    
    # --- 4. GRÁFICO SEMILOGARÍTMICO REAL CON MATPLOTLIB ---
    st.header("4. Curva Granulométrica Semilogarítmica (Recortada al TMA)")
    
    # Filtramos para graficar estrictamente desde el TMA hacia abajo
    df_grafico = df_suelos[df_suelos['Abertura (mm)'] <= tma_mm].copy()
    
    # Crear figura clásica de laboratorio
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Dibujar la línea
    ax.plot(df_grafico['Abertura (mm)'], df_grafico['% Que Pasa'], marker='o', color='blue', linewidth=2, label='Muestra')
    
    # Forzar Escala Logarítmica e Invertir Eje X
    ax.set_xscale('log')
    ax.set_xlim(tma_mm, 0.074)  # De mayor (TMA) a menor (N°200)
    ax.set_ylim(-5, 105)
    
    # Cuadrículas secundarias logarítmicas de ingeniería
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')
    
    ax.set_xlabel("Diámetro de Partícula (mm) - Escala Logarítmica")
    ax.set_ylabel("Porcentaje que Pasa (%)")
    ax.legend(loc='lower left')
    
    # Colocar los nombres de los tamices reales en el eje X
    ax.set_xticks(df_grafico['Abertura (mm)'])
    ax.set_xticklabels(df_grafico['Tamiz'], rotation=90, fontsize=8)
    
    # Desplegar en Streamlit
    st.pyplot(fig)
