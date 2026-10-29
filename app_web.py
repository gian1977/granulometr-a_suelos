import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as OpenpyxlImage

st.set_page_config(page_title="Mecanica de Suelos - Granulometria", layout="wide")
st.title("📊 Ensayo de Granulometria por Tamizado")
st.subheader("Manual de Carreteras v.8.202.3 / Adaptacion NCh 165")

# Inicialización de estados de sesión para asegurar transferencia inmune de datos al Excel
if "df_calculado" not in st.session_state:
    st.session_state.df_calculado = None
if "fig_grafico" not in st.session_state:
    st.session_state.fig_grafico = None
if "meta_calculos" not in st.session_state:
    st.session_state.meta_calculos = {"tma": '3"', "tmn": '3"', "error": 0.0, "banda": "TM-25", "clasificacion": "Sin Calcular"}

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
            
            # --- GUARDADO PERSISTENTE EN SESSION STATE ---
            st.session_state.df_calculado = df.copy()
            st.session_state.fig_grafico = fig
            st.session_state.meta_calculos = {
                "tma": tma_nombre,
                "tmn": tmn_nombre,
                "error": porcentaje_error,
                "banda": nombre_banda_activa,
                "clasificacion": clasificacion_mop,
                "masa_ini": masa_total
            }
            
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

# =============================================================================
# MÓDULO DE EXPORTACIÓN RIGIDA A EXCEL (DISEÑO ESPECÍFICO LISTO PARA IMPRIMIR)
# =============================================================================
st.markdown("---")
st.subheader("📄 Módulo de Reporte Oficial")

if "excel_descarga" not in st.session_state:
    st.session_state.excel_descarga = None
if "num_certificado" not in st.session_state:
    st.session_state.num_certificado = "002"

with st.container():
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        cert_input = st.text_input("Certificado de ensaye N°:", value=st.session_state.num_certificado)
        camino = st.text_input("Camino u Obra:", "Ruta 5 Norte - Ampliación Terceras Pistas")
        operador = st.text_input("Responsable ensaye:", "Prof. Mecánica de Suelos")
    with c_m2:
        f_m = st.date_input("Fecha de muestreo:")
        f_e = st.date_input("Fecha de ensaye:")
        jefe = st.text_input("V°B° Jefe Laboratorio:", "Ing. Control de Calidad")

if st.button("📊 Compilar y Generar Planilla Oficial de Laboratorio"):
    st.session_state.num_certificado = cert_input
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Granulometría MOP"
    
    try:
        ws.views.sheetView.showGridLines = True
    except Exception:
        pass
        
    f_logo = Font(name="Arial", size=14, bold=True, color="000000")
    f_tit = Font(name="Arial", size=10, bold=True)
    f_sub = Font(name="Arial", size=8, bold=True)
    f_body = Font(name="Arial", size=8)
    f_form = Font(name="Arial", size=8, italic=True)
    
    fill_h = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    border_fino = Border(
        left=Side(style='thin', color='000000'), right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'), bottom=Side(style='thin', color='000000')
    )
    
    al_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    al_left = Alignment(horizontal='left', vertical='center')
    al_right = Alignment(horizontal='right', vertical='center')
    
    # AJUSTE AJUSTED EN ESPEJO DEL ENCABEZADO (Mapeo estricto del PDF)
    ws.merge_cells('B1:C3')
    ws['B1'] = "inacap"
    ws['B1'].font = f_logo
    ws['B1'].alignment = al_center
    ws['B1'].border = border_fino
    
    # Título centralizado combinando las columnas D, E y F
    ws.merge_cells('D1:F3')
    ws['D1'] = "ENSAYO GRANULOMÉTRICO DE SUELOS\n\n8.102.1.A"
    ws['D1'].font = f_tit
    ws['D1'].alignment = al_center
    ws['D1'].border = border_fino
    
    # Columna G (Última de la tabla) recibe de manera exclusiva los datos de vialidad del MOP
    ws['G1'] = "MANUAL DE CARRETERAS"
    ws['G2'] = "VOL. N° 8"
    ws['G3'] = f"PAG. 1 de 1 / Ver. {cert_input}"
    
    for r in range(1, 4):
        for c in range(2, 8):
            ws.cell(row=r, column=c).border = border_fino
            if c == 7:
                ws.cell(row=r, column=c).font = f_sub
                ws.cell(row=r, column=c).alignment = al_center

    # Datos Generales y Cuarteo
    ws['B5'] = "Certificado de ensaye N°:"
    ws['C5'] = cert_input
    ws['F5'] = "Fecha de muestreo:"
    ws['G5'] = str(f_m)
    
    ws['B6'] = "Fecha de ensaye:"
    ws['C6'] = str(f_e)
    ws['F6'] = "Camino u Obra:"
    ws['G6'] = camino
    
    ws['B8'] = "1. Cuarteo:"
    ws['B8'].font = f_tit
    
    ws['B9'] = "TMA muestra de ensaye:"
    ws['C9'] = f"{st.session_state.meta_calculos['tma']}"
    ws['F9'] = "Masa Total de muestra a tamizar:"
    ws['G9'] = st.session_state.meta_calculos.get('masa_ini', 0.0)
    ws['G9'].number_format = '0.0'

    for r in range(5, 10):
        if r != 7:
            ws.cell(row=r, column=2).font = f_sub
            ws.cell(row=r, column=3).font = f_body
            ws.cell(row=r, column=6).font = f_sub
            ws.cell(row=r, column=7).font = f_body

    # Estructura del Tamizado (Fila 11)
    ws['B11'] = "2. Granulometría"
    ws['B11'].font = f_tit
    
    headers = ["Abertura\nmm", "Tamiz", "Masa\n(g)", "% Retenido", "% Acumulado", "% Que\nPasa"]
    for idx, h in enumerate(headers, start=2):
        cell = ws.cell(row=12, column=idx, value=h)
        cell.font = f_sub
        cell.fill = fill_h
        cell.alignment = al_center
        cell.border = border_fino

    row_actual = 13
    if st.session_state.df_calculado is not None:
        for idx, row_df in st.session_state.df_calculado.iterrows():
            ws.cell(row=row_actual, column=2, value=row_df.iloc[0]).alignment = al_center
            ws.cell(row=row_actual, column=3, value=str(row_df.iloc[1])).alignment = al_center
            ws.cell(row=row_actual, column=4, value=row_df.iloc[2]).alignment = al_right
            ws.cell(row=row_actual, column=5, value=row_df.iloc[3]).alignment = al_right
            ws.cell(row=row_actual, column=6, value=row_df.iloc[4]).alignment = al_right
            ws.cell(row=row_actual, column=7, value=row_df.iloc[5]).alignment = al_right
            
            for c in range(2, 8):
                ws.cell(row=row_actual, column=c).font = f_body
                ws.cell(row=row_actual, column=c).border = border_fino
                if c >= 4:
                    ws.cell(row=row_actual, column=c).number_format = '0.0'
            row_actual += 1

    ws.cell(row=row_actual, column=3, value="Totales:").font = f_sub
    if st.session_state.df_calculado is not None:
        ws.cell(row=row_actual, column=4, value=f"=SUM(D13:D{row_actual-1})").font = f_sub
    else:
        ws.cell(row=row_actual, column=4, value=0.0).font = f_sub
    ws.cell(row=row_actual, column=4).border = border_fino
    ws.cell(row=row_actual, column=4).number_format = '0.0'
    
    row_actual += 1
    ws.cell(row=row_actual, column=3, value="% Error:").font = f_sub
    ws.cell(row=row_actual, column=4, value=st.session_state.meta_calculos['error']).font = f_body
    ws.cell(row=row_actual, column=4).border = border_fino
    ws.cell(row=row_actual, column=4).number_format = '0.00'
    
    # COMPACTACIÓN ESTRECHA DE FÓRMULAS DE DOS PISOS (Centradas al ancho de la tabla)
    row_actual += 2
    ws.cell(row=row_actual, column=2, value="                                   𝑴𝒂𝒔𝒂 𝑻𝒐𝒕𝒂𝒍 𝒅𝒆 𝒎𝒖𝒆𝒔𝒕𝒓𝒂  −  𝑻𝒐𝒕𝒂𝒍 𝑹𝒆𝒕𝒆𝒏𝒊𝒅𝒐").font = f_form
    row_actual += 1
    ws.cell(row=row_actual, column=2, value="  % 𝜺  =  𝑽𝒂𝒍𝒐𝒓 𝑨𝒃𝒔𝒐𝒍𝒖𝒕𝒐 ( ─────────────────────────────────────────── ) 𝒙 𝟏𝟎𝟎 (%)").font = f_form
    row_actual += 1
    ws.cell(row=row_actual, column=2, value="                                                 𝑴𝒂𝒔𝒂 𝑻𝒐𝒕𝒂𝒍 𝒅𝒆 𝒎𝒖𝒆𝒔𝒕𝒓𝒂").font = f_form
    
    row_actual += 2
    ws.cell(row=row_actual, column=2, value="                               𝑴𝒂𝒔𝒂  𝑹𝒆𝒕𝒆𝒏.  𝒄𝒐𝒓𝒓𝒆𝒈𝒊𝒅𝒂").font = f_form
    row_actual += 1
    ws.cell(row=row_actual, column=2, value="  % 𝑹𝒆𝒕𝒆𝒏𝒊𝒅𝒐  =  ─────────────────────────────────────────── 𝒙 𝟏𝟎𝟎").font = f_form
    row_actual += 1
    ws.cell(row=row_actual, column=2, value="                         𝑴𝒂𝒔𝒂 𝑻𝒐𝒕𝒂𝒍 𝒅𝒆 𝑴𝒖𝒆𝒔𝒕𝒓𝒂 𝒄𝒐𝒓𝒓𝒆𝒈𝒊𝒅𝒂").font = f_form
    
    row_actual += 2
    ws.cell(row=row_actual, column=2, value="  % 𝑹𝒆𝒕𝒆𝒏𝒊𝒅𝒐 𝒂𝒄𝒖𝒎𝒖𝒍𝒂𝒅𝒐  =  % 𝒓𝒆𝒕𝒆𝒏𝒊𝒅𝒐 𝒆𝒏 𝒕𝒂𝒎𝒊𝒛  +  % 𝒓𝒆𝒕𝒆𝒏𝒊𝒅𝒐 𝒂𝒄𝒖𝒎𝒖𝒍. 𝒂𝒏𝒕𝒆𝒓𝒊𝒐𝒓").font = f_form
    row_actual += 2
    ws.cell(row=row_actual, column=2, value="  % 𝑨𝒄𝒖𝒎𝒖𝒍𝒂𝒅𝒐 𝒒𝒖𝒆 𝑷𝒂𝒔𝒂  =  𝟏𝟎𝟎  −  % 𝑹𝒆𝒕𝒆𝒏. 𝑨𝒄𝒖𝒎𝒖𝒍. 𝒆𝒏 𝒕𝒂𝒎𝒊𝒛").font = f_form

    # REDUCCIÓN RIGIDA DE LA GRÁFICA PARA CORRESPONDER A HOJA CARTA / A4 VERTICAL
    row_actual += 2
    ws.cell(row=row_actual, column=2, value="Curva Granulométrica Oficial").font = f_tit
    
    if st.session_state.fig_grafico is not None:
        img_buf = io.BytesIO()
        st.session_state.fig_grafico.savefig(img_buf, format='png', dpi=110, bbox_inches='tight')
        img_buf.seek(0)
        xl_img = OpenpyxlImage(img_buf)
        ws.add_image(xl_img, f'B{row_actual + 1}')
        row_actual += 20  # Avance proporcional exacto al nuevo tamaño reducido
        
    row_actual += 2
    ws.cell(row=row_actual, column=2, value=f"Responsable ensaye: {operador}").font = f_body
    ws.cell(row=row_actual+2, column=2, value=f"V°B° Jefe Laboratorio: {jefe}").font = f_body

    # Anchos fijos optimizados para una sola hoja vertical limpia
    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 12  # Abertura
    ws.column_dimensions['C'].width = 12  # Tamiz
    ws.column_dimensions['D'].width = 15  # Masa
    ws.column_dimensions['E'].width = 13  # % Ret
    ws.column_dimensions['F'].width = 13  # % Acum
    ws.column_dimensions['G'].width = 24  # % Pasa / Info MOP

    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    st.session_state.excel_descarga = excel_file.getvalue()
    st.toast("✅ ¡Planilla optimizada para impresión generada con éxito!", icon="📊")

if st.session_state.excel_descarga is not None:
    st.info("🎉 El informe oficial optimizado para impresión A4/Carta está listo.")
    st.download_button(
        label="📥 Descargar Planilla Excel Certificada",
        data=st.session_state.excel_descarga,
        file_name=f"Informe_Granulometria_MOP_{st.session_state.num_certificado}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
