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

# --- 2. SECCIÓN DE SELECCIÓN E INGRESO DE PESOS RETENIDOS ---
st.header("2. Configuración de Tamices y Registro de Pesos")
st.write("Active los tamices que utilizó en el ensayo e ingrese sus pesos retenidos en gramos:")

# Serie completa ASTM de referencia
serie_completa = [
    (76.200, '3"'), (63.500, '2 1/2"'), (50.600, '2"'), (38.100, '1 1/2"'),
    (25.400, '1"'), (19.050, '3/4"'), (12.700, '1/2"'), (9.525, '3/8"'),
    (6.350, '1/4"'), (4.760, 'N° 4'), (2.380, 'N° 8'), (2.000, 'N° 10'),
    (1.190, 'N° 16'), (0.840, 'N° 20'), (0.590, 'N° 30'), (0.420, 'N° 40'),
    (0.300, 'N° 50'), (0.250, 'N° 60'), (0.180, 'N° 80'), (0.149, 'N° 100'),
    (0.074, 'N° 200')
]

pesos_ingresados = {}
tamices_activos = []

# Distribución visual en 3 columnas
col1, col2, col3 = st.columns(3)

for i, (abertura, tamiz) in enumerate(serie_completa):
    label_check = f"Utilizar {tamiz} ({abertura:.3f} mm)"
    label_peso = f"Retenido {tamiz} (g)"
    
    if i % 3 == 0:
        with col1:
            activo = st.checkbox(label_check, value=True, key=f"check_{tamiz}")
            peso = st.number_input(label_peso, min_value=0.0, value=0.0, step=0.1, key=f"peso_{tamiz}") if activo else 0.0
    elif i % 3 == 1:
        with col2:
            activo = st.checkbox(label_check, value=True, key=f"check_{tamiz}")
            peso = st.number_input(label_peso, min_value=0.0, value=0.0, step=0.1, key=f"peso_{tamiz}") if activo else 0.0
    else:
        with col3:
            activo = st.checkbox(label_check, value=True, key=f"check_{tamiz}")
            peso = st.number_input(label_peso, min_value=0.0, value=0.0, step=0.1, key=f"peso_{tamiz}") if activo else 0.0
            
    if activo:
        tamices_activos.append((abertura, tamiz))
        pesos_ingresados[tamiz] = peso

st.markdown("---")
pesos_ingresados['Residuo'] = st.number_input("Residuo / Fondo (g)", min_value=0.0, value=0.0, step=0.1, key='Residuo')

# --- 3. PROCESAMIENTO Y CÁLCULOS ---
if st.button("Calcular Granulometría", type="primary"):
    if not tamices_activos:
        st.error("❌ Debe seleccionar al menos un tamiz para realizar los cálculos.")
    else:
        # Estructurar DataFrame dinámico
        lista_dinamica = tamices_activos + [(0.000, 'Residuo')]
        df = pd.DataFrame(lista_dinamica, columns=['Abertura (mm)', 'Tamiz'])
        df['Peso Retenido (g)'] = df['Tamiz'].map(pesos_ingresados).fillna(0.0)
        
        # Control de calidad
        suma_total_retenido = df['Peso Retenido (g)'].sum()
        error_gramos = masa_total - suma_total_retenido
        porcentaje_error = (abs(error_gramos) / masa_total) * 100
        
        # Cálculos de columnas
        df['% Peso Retenido'] = (df['Peso Retenido (g)'] / masa_total) * 100
        df['% Peso Ret. Acumul.'] = df['% Peso Retenido'].cumsum()
        df['% Que Pasa'] = 100 - df['% Peso Ret. Acumul.']
        df.loc[df['Tamiz'] == 'Residuo', '% Que Pasa'] = 0.0
        
        # --- LÓGICA CORREGIDA DE TMA Y TMN (Normativa Chilena) ---
        df_suelos = df[df['Abertura (mm)'] > 0].copy().reset_index(drop=True)
        
        # Buscamos el PRIMER tamiz de la serie activa que registra retención de material
        df_con_material = df_suelos[df_suelos['Peso Retenido (g)'] > 0.001]
        
        if not df_con_material.empty:
            # Obtenemos el índice posicional correcto del primer tamiz con material
            idx_primer_retenido = df_con_material.index[0]
            
            # Si el primer tamiz con retención es el más grande de los ACTIVOS, el TMA será ese mismo
            if idx_primer_retenido == 0:
                tma_mm = df_suelos.loc[idx_primer_retenido, 'Abertura (mm)']
                tma_nombre = df_suelos.loc[idx_primer_retenido, 'Tamiz']
                idx_tma_real = 0
            else:
                # Normativa: El TMA es el menor tamiz por el que pasa el 100% (el inmediatamente superior al que retiene)
                idx_tma_real = idx_primer_retenido - 1
                tma_mm = df_suelos.loc[idx_tma_real, 'Abertura (mm)']
                tma_nombre = df_suelos.loc[idx_tma_real, 'Tamiz']
            
            # Determinar TMN: Evaluamos el tamiz inmediatamente inferior al TMA en la serie activa
            if idx_tma_real + 1 < len(df_suelos):
                idx_inferior = idx_tma_real + 1
                pasa_inferior = df_suelos.loc[idx_inferior, '% Que Pasa']
                
                # Criterio estricto solicitado: inmediato inferior si pasa entre 90% y 99.9%
                if 90.0 <= pasa_inferior < 100.0:
                    tmn_mm = df_suelos.loc[idx_inferior, 'Abertura (mm)']
                    tmn_nombre = df_suelos.loc[idx_inferior, 'Tamiz']
                else:
                    # Si el % que pasa es menor al 90%, el TMN es igual al TMA
                    tmn_mm = tma_mm
                    tmn_nombre = tma_nombre
            else:
                tmn_mm = tma_mm
                tmn_nombre = tma_nombre
        else:
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
            
        df_visual = df.copy().round(2)
        st.dataframe(df_visual, use_container_width=True, hide_index=True)
        
        # --- 4. GRÁFICO SEMILOGARÍTMICO REAL RECORTADO AL TMA ---
        st.header("4. Curva Granulométrica Semilogarítmica")
        
        df_grafico = df_suelos[df_suelos['Abertura (mm)'] <= tma_mm].copy()
        
        if not df_grafico.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df_grafico['Abertura (mm)'], df_grafico['% Que Pasa'], marker='o', color='blue', linewidth=2, label='Muestra')
            
            ax.set_xscale('log')
            xlim_max = tma_mm if tma_mm > 0.074 else 0.1
            ax.set_xlim(xlim_max, 0.074)
            ax.set_ylim(-5, 105)
            
            ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')
            ax.set_xlabel("Diámetro de Partícula (mm) - Escala Logarítmica")
            ax.set_ylabel("Porcentaje que Pasa (%)")
            ax.legend(loc='lower left')
            
            ax.set_xticks(df_grafico['Abertura (mm)'])
            ax.set_xticklabels(df_grafico['Tamiz'], rotation=90, fontsize=8)
            
            st.pyplot(fig)
        else:
            st.warning("No hay suficientes datos para graficar con el recorte.")
