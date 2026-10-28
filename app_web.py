import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuración del título de la página web
st.set_page_config(page_title="Mecánica de Suelos - Granulometría", layout="wide")

st.title("📊 Ensayo de Granulometría por Tamizado")
st.subheader("Manual de Carreteras v.8.202.3 / Adaptación NCh 165")

# --- 1. SECCIÓN DE DATOS INICIALES (CUARTEO) ---
st.sidebar.header("1. Datos del Cuarteo")
tma = st.sidebar.number_input("TMA muestra de ensaye (mm)", min_value=0.0, value=19.05, step=0.1)
masa_total = st.sidebar.number_input("Masa Total de muestra a tamizar (g)", min_value=0.1, value=4500.0, step=1.0)

# --- 2. SECCIÓN DE INGRESO DE PESOS RETENIDOS ---
st.header("2. Registro de Pesos Retenidos por Tamiz")
st.write("Ingrese el peso retenido en gramos para cada tamiz correspondiente:")

# Lista de tamices según tu planilla
datos_tamices = [
    (76.200, '3"'), (63.500, '2 1/2"'), (50.600, '2"'), (38.100, '1 1/2"'),
    (25.400, '1"'), (19.050, '3/4"'), (12.700, '1/2"'), (9.525, '3/8"'),
    (6.350, '1/4"'), (4.760, 'N° 4'), (2.380, 'N° 8'), (2.000, 'N° 10'),
    (1.190, 'N° 16'), (0.840, 'N° 20'), (0.590, 'N° 30'), (0.420, 'N° 40'),
    (0.300, 'N° 50'), (0.250, 'N° 60'), (0.180, 'N° 80'), (0.149, 'N° 100'),
    (0.074, 'N° 200')
]

pesos_ingresados = {}

# Distribuimos los campos de entrada en 3 columnas
col1, col2, col3 = st.columns(3)

for i, (abertura, tamiz) in enumerate(datos_tamices):
    label = f"{tamiz} ({abertura:.3f} mm)"
    if i % 3 == 0:
        with col1:
            pesos_ingresados[tamiz] = st.number_input(label, min_value=0.0, value=0.0, step=0.1, key=tamiz)
    elif i % 3 == 1:
        with col2:
            pesos_ingresados[tamiz] = st.number_input(label, min_value=0.0, value=0.0, step=0.1, key=tamiz)
    else:
        with col3:
            pesos_ingresados[tamiz] = st.number_input(label, min_value=0.0, value=0.0, step=0.1, key=tamiz)

st.markdown("---")
pesos_ingresados['Residuo'] = st.number_input("Residuo / Fondo (g)", min_value=0.0, value=0.0, step=0.1, key='Residuo')

# --- 3. PROCESAMIENTO Y CÁLCULOS ---
if st.button("Calcular Granulometría", type="primary"):
    # Agregar el Residuo a la lista completa para armar el DataFrame final
    lista_completa_tamices = datos_tamices + [(0.000, 'Residuo')]
    df = pd.DataFrame(lista_completa_tamices, columns=['Abertura (mm)', 'Tamiz'])
    
    # Asignar los pesos ingresados
    df['Peso Retenido (g)'] = df['Tamiz'].map(pesos_ingresados).fillna(0.0)
    
    # Control de pérdida de masa
    suma_total_retenido = df['Peso Retenido (g)'].sum()
    error_gramos = masa_total - suma_total_retenido
    porcentaje_error = (abs(error_gramos) / masa_total) * 100
    
    # Cálculos de columnas
    df['% Peso Retenido'] = (df['Peso Retenido (g)'] / masa_total) * 100
    df['% Peso Ret. Acumul.'] = df['% Peso Retenido'].cumsum()
    df['% Que Pasa'] = 100 - df['% Peso Ret. Acumul.']
    df.loc[df['Tamiz'] == 'Residuo', '% Que Pasa'] = 0.0
    
    # Redondeos para visualización de la tabla
    df_visual = df.copy()
    df_visual['% Peso Retenido'] = df_visual['% Peso Retenido'].round(2)
    df_visual['% Peso Ret. Acumul.'] = df_visual['% Peso Ret. Acumul.'].round(2)
    df_visual['% Que Pasa'] = df_visual['% Que Pasa'].round(2)
    
    # --- 4. PRESENTACIÓN DE RESULTADOS ---
    st.header("3. Matriz de Resultados")
    
    if porcentaje_error <= 1.0:
        st.success(f"✅ Ensayo Aprobado. Pérdida de masa: {error_gramos:.1f} g ({porcentaje_error:.2f}%). Límite normativo <= 1%.")
    else:
        st.error(f"❌ Ensayo Rechazado. Pérdida de masa: {error_gramos:.1f} g ({porcentaje_error:.2f}%). Supera la tolerancia del 1%.")
        
    st.dataframe(df_visual, use_container_width=True, hide_index=True)
    
    # --- 5. GENERACIÓN DE CURVA GRANULOMÉTRICA (SEMILOGARÍTMICA) ---
    st.header("4. Curva Granulométrica")
    
    # Filtramos para el gráfico: eliminamos el Residuo (0 mm) para evitar errores logarítmicos en eje X
    df_grafico = df[df['Abertura (mm)'] > 0].copy()
    
    # Creamos la figura interactiva
    fig = go.Figure()
    
    # Agregar la línea de la muestra
    fig.add_trace(go.Scatter(
        x=df_grafico['Abertura (mm)'],
        y=df_grafico['% Que Pasa'],
        mode='lines+markers',
        name='Muestra Ensaye',
        line=dict(color='blue', width=3),
        marker=dict(size=6, symbol='circle')
    ))
    
    # Configuración de los ejes según mecánica de suelos
    fig.update_layout(
        title="Curva Granulométrica del Suelo",
        xaxis=dict(
            title="Tamaño de Partícula (Abertura en mm) - Escala Logarítmica",
            type="log",                  # Eje X en escala Logarítmica
            autorange="reverse",         # Invierte el eje X (Grava a la izquierda, finos a la derecha)
            dtick=1,                     # Intervalo de cuadrícula logarítmica principales
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="Porcentaje que Pasa (%) - Escala Normal",
            range=[-5, 105],             # Rango fijo corregido de 0% a 100% con holgura visual
            gridcolor='lightgray',
            dtick=10                     # Línea cada 10%
        ),
        plot_bgcolor='white',
        height=600,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    # Desplegar gráfico en la web
    st.plotly_chart(fig, use_container_width=True)
