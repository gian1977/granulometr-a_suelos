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
    
    # --- DETERMINACIÓN DE TMA Y TMN (Normativa Chilena) ---
    # Tamices ordenados de mayor a menor tamaño (excluyendo el Residuo)
    df_suelos = df[df['Abertura (mm)'] > 0].copy()
    
    # TMA (Tamaño Máximo Absoluto): El primer tamiz (de mayor a menor) que retiene material (> 0%)
    tamices_con_retencion = df_suelos[df_suelos['Peso Retenido (g)'] > 0.0]
    
    if not tamices_con_retencion.empty:
        # El primero en la lista (el tamiz más grande con retenido)
        tma_row = tamices_con_retencion.iloc[0]
        tma_nombre = tma_row['Tamiz']
        tma_mm = tma_row['Abertura (mm)']
        
        # Encontrar el índice de ese tamiz en la lista original para saber cuál es el inmediatamente superior
        idx_tma = df_suelos[df_suelos['Tamiz'] == tma_nombre].index[0]
        
        # TMN (Tamaño Máximo Nominal): Es el tamiz inmediatamente inferior al TMA si pasa el 100%
        # o el mismo TMA si ya retiene más del 5%. Estándar simplificado: el inmediatamente inferior en la serie
        if idx_tma + 1 < len(df_suelos):
            tmn_nombre = df_suelos.iloc[idx_tma + 1]['Tamiz']
            tmn_mm = df_suelos.iloc[idx_tma + 1]['Abertura (mm)']
        else:
            tmn_nombre = tma_nombre
            tmn_mm = tma_mm
    else:
        # Si no retiene nada en ningún tamiz superior al N° 200
        tma_nombre, tma_mm = 'N° 200', 0.074
        tmn_nombre, tmn_mm = 'N° 200', 0.074

    # --- PRESENTACIÓN DE RESULTADOS ---
    st.header("3. Matriz de Resultados")
    
    col_tma, col_tmn = st.columns(2)
    with col_tma:
        st.metric(label="Tamaño Máximo Absoluto (TMA)", value=f"{tma_nombre} ({tma_mm:.3f} mm)")
    with col_tmn:
        st.metric(label="Tamaño Máximo Nominal (TMN)", value=f"{tmn_nombre} ({tmn_mm:.3f} mm)")
        
    if porcentaje_error <= 1.0:
        st.success(f"✅ Ensayo Aprobado. Pérdida de masa: {error_gramos:.1f} g ({porcentaje_error:.2f}%). Límite normativo <= 1%.")
    else:
        st.error(f"❌ Ensayo Rechazado. Pérdida de masa: {error_gramos:.1f} g ({porcentaje_error:.2f}%). Supera la tolerancia del 1%.")
        
    # Mostrar tabla formateada
    df_visual = df.copy().round(2)
    st.dataframe(df_visual, use_container_width=True, hide_index=True)
    
    # --- 4. GENERACIÓN DE CURVA GRANULOMÉTRICA CON MATPLOTLIB ---
    st.header("4. Curva Granulométrica Semilogarítmica")
    
    # FILTRADO OPTIMIZADO: Graficar desde el TMA hacia abajo para eliminar el 100% plano redundante
    df_grafico = df_suelos[df_suelos['Abertura (mm)'] <= tma_mm].copy()
    
    # Si por alguna razón da vacío (ej. todo pasó el N°200), graficar la serie completa
    if df_grafico.empty:
        df_grafico = df_suelos.copy()
        
    # Crear la figura clásica de laboratorio usando Matplotlib
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Dibujar la línea granulométrica
    ax.plot(df_grafico['Abertura (mm)'], df_grafico['% Que Pasa'], marker='o', color='blue', linewidth=2, label='Muestra de Ensaye')
    
    # Configuración de escalas y comportamiento del gráfico de suelos
    ax.set_xscale('log')          # Escala estrictamente Logarítmica en X
    ax.set_xlim(tma_mm, 0.074)    # Límites dinámicos: Desde el TMA (Izquierda) hasta el N° 200 (Derecha)
    ax.set_ylim(-5, 105)          # Escala normal en Y de 0 a 100%
    
    # Cuadrícula de ingeniería (Líneas principales y secundarias logarítmicas)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')
    
    # Títulos del gráfico
    ax.set_title("Curva Granulométrica del Suelo (Escala Semilogarítmica)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Diámetro de Partícula (Abertura en mm) - Escala Logarítmica", fontsize=10)
    ax.set_ylabel("Porcentaje acumulado que Pasa (%) - Escala Normal", fontsize=10)
    ax.legend(loc='lower left')
    
    # Forzar etiquetas limpias en el eje X para que muestre los mm reales
    ax.set_xticks(df_grafico['Abertura (mm)'])
    ax.set_xticklabels([f"{x:.3f}" if x < 1 else f"{x:.1f}" for x in df_grafico['Abertura (mm)']], rotation=45, fontsize=8)
    
    # Desplegar la imagen del gráfico en la web de Streamlit
    st.pyplot(fig)
