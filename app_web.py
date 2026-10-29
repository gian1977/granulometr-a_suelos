import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mecanica de Suelos - Granulometria", layout="wide")
st.title("📊 Ensayo de Granulometria por Tamizado")
st.subheader("Manual de Carreteras v.8.202.3 / Adaptacion NCh 165")

st.sidebar.header("1. Datos del Cuarteo")
masa_total = st.sidebar.number_input("Masa Total de muestra a tamizar (g)", min_value=0.1, value=4500.0, step=1.0)

st.header("2. Configuracion de Tamices y Registro de Pesos")
st.write("Active los tamices que utilizo en el ensayo e ingrese sus pesos retenidos en gramos:")

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

if st.button("Calcular Granulometria", type="primary"):
    if not tamices_activos:
        st.error("❌ Debe seleccionar al menos un tamiz para realizar los calculos.")
    else:
        idx_primer_retenido_completo = -1
        for indice, (ab, nom) in enumerate(serie_completa):
            if pesos_ingresados.get(nom, 0.0) > 0.001:
                idx_primer_retenido_completo = indice
                break
        
        tamices_a_procesar = list(tamices_activos)
        if idx_primer_retenido_completo > 0:
            ab_control, nom_control = serie_completa[idx_primer_retenido_completo - 1]
            existe_en_activos = any(nom == nom_control for ab, nom in tamices_a_procesar)
            if not existe_en_activos:
                tamices_a_procesar.insert(0, (ab_control, nom_control))
                pesos_ingresados[nom_control] = 0.0
        
        tamices_a_procesar = sorted(tamices_a_procesar, key=lambda x: x[0], reverse=True)
        
        lista_dinamica = tamices_a_procesar + [(0.000, 'Residuo')]
        df = pd.DataFrame(lista_dinamica, columns=['Abertura (mm)', 'Tamiz'])
        df['Peso Retenido (g)'] = df['Tamiz'].map(pesos_ingresados).fillna(0.0)
        
        suma_total_retenido = df['Peso Retenido (g)'].sum()
        error_gramos = masa_total - suma_total_retenido
        porcentaje_error = (abs(error_gramos) / masa_total) * 100 if masa_total > 0 else 0.0
        
        df['% Peso Retenido'] = (df['Peso Retenido (g)'] / masa_total) * 100
        df['% Peso Ret. Acumul.'] = df['% Peso Retenido'].cumsum()
        df['% Que Pasa'] = 100.0 - df['% Peso Ret. Acumul.']
        df.loc[df['Tamiz'] == 'Residuo', '% Que Pasa'] = 0.0
        
        registros_muestra = df.to_dict(orient='records')

        tma_mm = 76.200
        tma_nombre = '3"'
        idx_tma_en_procesados = 0
        encontrado_material = False
        
        for idx_p, reg in enumerate(registros_muestra):
            if reg['Abertura (mm)'] > 0.001 and reg['Peso Retenido (g)'] > 0.001:
                encontrado_material = True
                if idx_p == 0:
                    tma_mm = reg['Abertura (mm)']
                    tma_nombre = reg['Tamiz']
                    idx_tma_en_procesados = 0
                else:
                    idx_tma_en_procesados = idx_p - 1
                    tma_mm = registros_muestra[idx_tma_en_procesados]['Abertura (mm)']
                    tma_nombre = registros_muestra[idx_tma_en_procesados]['Tamiz']
                break
                
        if not encontrado_material:
            tma_nombre, tma_mm = 'N° 200', 0.074
            idx_tma_en_procesados = len(registros_muestra) - 1

        tmn_mm = tma_mm
        tmn_nombre = tma_nombre
        
        if idx_tma_en_procesados + 1 < len(registros_muestra):
            reg_inf = registros_muestra[idx_tma_en_procesados + 1]
            if reg_inf['Abertura (mm)'] > 0.001:
                pasa_inf_valor = reg_inf['% Que Pasa']
                if 90.0 <= pasa_inf_valor < 100.0:
                    tmn_mm = reg_inf['Abertura (mm)']
                    tmn_nombre = reg_inf['Tamiz']

        pasa_n4 = 50.0
        pasa_n200 = 0.0
        for reg in registros_muestra:
            if reg['Tamiz'] == 'N° 4': pasa_n4 = reg['% Que Pasa']
            if reg['Tamiz'] == 'N° 200': pasa_n200 = reg['% Que Pasa']
                
        grava_pct = 100.0 - pasa_n4
        arena_pct = pasa_n4 - pasa_n200
        fino_pct = pasa_n200
        
        if fino_pct > 50.0:
            clasificacion_mop = "SUELO FINO (Limos / Arcillas)"
        else:
            if grava_pct > arena_pct:
                clasificacion_mop = f"SUELO GRUESO: GRAVA (Contenido de Finos: {fino_pct:.2f}%)"
            else:
                clasificacion_mop = f"SUELO GRUESO: ARENA (Contenido de Finos: {fino_pct:.2f}%)"

        st.header("3. Matriz de Resultados y Clasificacion")
        col_tma, col_tmn, col_clas = st.columns(3)
        with col_tma: st.metric(label="Tamaño Maximo Absoluto (TMA)", value=f"{tma_nombre}")
        with col_tmn: st.metric(label="Tamaño Maximo Nominal (TMN)", value=f"{tmn_nombre}")
        with col_clas: st.metric(label="Clasificacion del Suelo (MOP)", value=clasificacion_mop)
            
        if porcentaje_error <= 1.0:
            st.success(f"✅ Ensayo Aprobado. Perdida de masa: {error_gramos:.1f} g ({porcentaje_error:.2f}%).")
        else:
            st.error(f"❌ Ensayo Rechazado. Perdida de masa: {error_gramos:.1f} g ({porcentaje_error:.2f}%).")
            
        df_visual = df.copy().round(2)
        st.dataframe(df_visual, use_container_width=True, hide_index=True)

        # Base de datos completa, integra y corregida con ceros reales de la Tabla 8.101.1.B
        diccionario_bandas = {
            "TM-50a": [
                {"abertura": 50.600, "minimo": 100.0, "maximo": 100.0}, {"abertura": 25.400, "minimo": 55.0, "maximo": 100.0},
                {"abertura": 9.525, "minimo": 30.0, "maximo": 75.0}, {"abertura": 4.760, "minimo": 20.0, "maximo": 65.0},
                {"abertura": 2.000, "minimo": 10.0, "maximo": 50.0}, {"abertura": 0.300, "minimo": 5.0, "maximo": 30.0},
                {"abertura": 0.074, "minimo": 0.0, "maximo": 20.0}
            ],
            "TM-50b": [
                {"abertura": 50.600, "minimo": 100.0, "maximo": 100.0}, {"abertura": 38.100, "minimo": 70.0, "maximo": 100.0},
                {"abertura": 25.400, "minimo": 55.0, "maximo": 85.0}, {"abertura": 19.050, "minimo": 45.0, "maximo": 75.0},
                {"abertura": 9.525, "minimo": 35.0, "maximo": 65.0}, {"abertura": 4.760, "minimo": 25.0, "maximo": 55.0},
                {"abertura": 2.000, "minimo": 15.0, "maximo": 45.0}, {"abertura": 0.300, "minimo": 5.0, "maximo": 25.0},
                {"abertura": 0.074, "minimo": 0.0, "maximo": 10.0}
            ],
            "TM-50c": [
                {"abertura": 50.600, "minimo": 100.0, "maximo": 100.0}, {"abertura": 25.400, "minimo": 70.0, "maximo": 100.0},
                {"abertura": 19.050, "minimo": 60.0, "maximo": 90.0}, {"abertura": 9.525, "minimo": 40.0, "maximo": 75.0},
                {"abertura": 4.760, "minimo": 30.0, "maximo": 60.0}, {"abertura": 2.000, "minimo": 15.0, "maximo": 45.0},
                {"abertura": 0.300, "minimo": 10.0, "maximo": 30.0}, {"abertura": 0.074, "minimo": 0.0, "maximo": 15.0}
            ],
            "TM-40a": [
                {"abertura": 38.100, "minimo": 100.0, "maximo": 100.0}, {"abertura": 25.400, "minimo": 70.0, "maximo": 100.0},
                {"abertura": 19.050, "minimo": 50.0, "maximo": 80.0}, {"abertura": 9.525, "minimo": 25.0, "maximo": 50.0},
                {"abertura": 4.760, "minimo": 10.0, "maximo": 30.0}, {"abertura": 2.380, "minimo": 5.0, "maximo": 15.0},
                {"abertura": 0.300, "minimo": 0.0, "maximo": 5.0}, {"abertura": 0.074, "minimo": 0.0, "maximo": 3.0}
            ],
            "TM-40b": [
                {"abertura": 38.100, "minimo": 100.0, "maximo": 100.0}, {"abertura": 25.400, "minimo": 80.0, "maximo": 100.0},
                {"abertura": 9.525, "minimo": 50.0, "maximo": 80.0}, {"abertura": 4.760, "minimo": 35.0, "maximo": 65.0},
                {"abertura": 2.000, "minimo": 25.0, "maximo": 50.0}, {"abertura": 0.300, "minimo": 10.0, "maximo": 30.0},
                {"abertura": 0.074, "minimo": 5.0, "maximo": 15.0}
            ],
            "TM-40c": [
                {"abertura": 38.100, "minimo": 100.0, "maximo": 100.0}, {"abertura": 25.400, "minimo": 80.0, "maximo": 100.0},
                {"abertura": 9.525, "minimo": 50.0, "maximo": 80.0}, {"abertura": 4.760, "minimo": 35.0, "maximo": 65.0},
                {"abertura": 2.000, "minimo": 25.0, "maximo": 50.0}, {"abertura": 0.300, "minimo": 15.0, "maximo": 30.0},
                {"abertura": 0.074, "minimo": 5.0, "maximo": 20.0}
            ],
            "TM-25": [
                {"abertura": 25.400, "minimo": 100.0, "maximo": 100.0}, {"abertura": 19.050, "minimo": 70.0, "maximo": 100.0},
                {"abertura": 9.525, "minimo": 50.0, "maximo": 80.0}, {"abertura": 4.760, "minimo": 35.0, "maximo": 65.0},
                {"abertura": 2.000, "minimo": 25.0, "maximo": 50.0}, {"abertura": 0.300, "minimo": 10.0, "maximo": 30.0},
                {"abertura": 0.074, "minimo": 0.0, "maximo": 15.0}
            ]
        }
        
        # ALGORITMO DE SELECCIÓN INTELIGENTE DE BANDA SEGÚN TMA Y FINOS DE LA MUESTRA
        nombre_banda_activa = "TM-25"
        if tma_mm > 25.405 and tma_mm <= 38.105:
            if pasa_n200 <= 3.05: nombre_banda_activa = "TM-40a"
            elif pasa_n200 <= 15.05: nombre_banda_activa = "TM-40b"
            else: nombre_banda_activa = "TM-40c"
        elif tma_mm > 38.105:
            if pasa_n200 <= 10.05: nombre_banda_activa = "TM-50b"
            elif pasa_n200 <= 15.05: nombre_banda_activa = "TM-50c"
            else: nombre_banda_activa = "TM-50a"
            
        lista_activa = diccionario_bandas[nombre_banda_activa]
            
        st.header(f"4. Curva Granulometrica con Limites Banda Vial {nombre_banda_activa}")
        df_suelos_filtrado = df[df['Abertura (mm)'] > 0].copy()
        df_grafico = df_suelos_filtrado[df_suelos_filtrado['Abertura (mm)'] <= tma_mm].copy()
        
        if not df_grafico.empty:
            fig, ax = plt.subplots(figsize=(11, 5.5))
            ax.plot(df_grafico['Abertura (mm)'], df_grafico['% Que Pasa'], marker='o', markerfacecolor='white', markeredgecolor='black', color='black', linewidth=2, label='Muestra Suelo')
            
            aberturas_b = [item["abertura"] for item in lista_activa]
            minimos_b = [item["minimo"] for item in lista_activa]
            maximos_b = [item["maximo"] for item in lista_activa]
            
            ax.plot(aberturas_b, minimos_b, color='red', linestyle='--', linewidth=1.5, label='Limite Inferior MOP')
            ax.plot(aberturas_b, maximos_b, color='red', linestyle='--', linewidth=1.5, label='Limite Superior MOP')
            ax.fill_between(aberturas_b, minimos_b, maximos_b, color='red', alpha=0.05, label='Zona Conforme')

            ax.plot([4.760, 4.760], [-20, 110], color='mediumvioletred', linewidth=1.5, linestyle='-')
            ax.plot([4.760, 4.760], [-20, 110], marker='o', markersize=5, color='gold', markeredgecolor='darkred', linestyle='')
            ax.plot([0.074, 0.074], [-20, 110], color='indigo', linewidth=1.5, linestyle='-')
            ax.plot([0.074, 0.074], [-20, 110], marker='o', markersize=5, color='gold', markeredgecolor='darkred', linestyle='')

            ax.set_xscale('log')
            lim_izquierdo = 100.0 if tma_mm > 10.0 else 10.0
            ax.set_xlim(lim_izquierdo, 0.01)
            ax.set_ylim(-10, 105)
            
            ax.grid(True, which='both', linestyle='-', linewidth=0.5, color='lightgray')
            ax.set_xlabel("TAMANO DE TAMIZ (MM) - ESC. LOG", fontsize=10, fontweight='bold')
            ax.set_ylabel("% QUE PASA", fontsize=10, fontweight='bold')
            ax.legend(loc='upper right', fontsize=8)
            
            valores_eje_x = [100.0, 10.0, 1.0, 0.1, 0.01]
            ax.set_xticks(valores_eje_x)
            ax.set_xticklabels([f"{x:g}" for x in valores_eje_x])
            st.pyplot(fig)
            
            fuera_de_banda = False
            st.subheader("📋 Evaluacion de Conformidad Vial")
            
            for item_b in lista_activa:
                mm_ref = item_b["abertura"]
                lim_min = item_b["minimo"]
                lim_max = item_b["maximo"]
                for reg in registros_muestra:
                    if reg['Abertura (mm)'] > 0.001 and abs(reg['Abertura (mm)'] - mm_ref) < 0.1:
                        pasa_t = reg['% Que Pasa']
                        if pasa_t < lim_min or pasa_t > lim_max:
                            fuera_de_banda = True
                            st.warning(f"⚠️ El tamiz {reg['Tamiz']} ({mm_ref:.2f} mm) esta fuera de rango: Registra {pasa_t:.2f}%, el permitido es [{lim_min}% - {lim_max}%].")
            
            if not fuera_de_banda:
                st.success(f"🎉 ¡Excelente! Todo el suelo se encuentra dentro de la banda {nombre_banda_activa} exigida por el Manual de Carreteras.")
            else:
                st.error("❌ El material NO cumple con los requisitos del Manual de Carreteras para ser utilizado como Base Granular debido a las desviaciones indicadas.")
        else:
            st.warning("No hay suficientes datos para graficar.")
