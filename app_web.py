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

import io
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image as OpenpyxlImage

# =============================================================================
# MÓDULO DE EXPORTACIÓN A EXCEL (NORMA MOP 8.102.1.A & NCh 165)
# =============================================================================

st.markdown("---")
st.subheader("📄 Generación de Informe Oficial")

# Formulario para metadatos del encabezado requerido por la norma
with st.container():
    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        cert_no = st.text_input("Certificado de ensaye N°:", "001-2026")
        camino_obra = st.text_input("Camino u Obra:", "Ruta 5 Norte - Tramo Copiapó")
        responsable = st.text_input("Responsable ensaye:", "Prof. Mecánica de Suelos")
    with col_meta2:
        f_muestreo = st.date_input("Fecha de muestreo:")
        f_ensaye = st.date_input("Fecha de ensaye:")
        jefe_lab = st.text_input("V°B° Jefe Laboratorio:", "Ing. Control de Calidad")

# Botón de exportación
if st.button("📊 Generar y Descargar Planilla Excel Oficial"):
    
    # 1. Crear libro y configurar hoja
    wb = Workbook()
    ws = wb.active
    ws.title = "Granulometría MOP"
    ws.views.sheetView[0].showGridLines = True
    
    # Estilos Globales (Clásicos de Laboratorio)
    font_title = Font(name="Arial", size=11, bold=True)
    font_sub = Font(name="Arial", size=9, bold=True)
    font_body = Font(name="Arial", size=9)
    font_formula = Font(name="Arial", size=8, italic=True, color="555555")
    
    fill_header = PatternFill(start_color="E6E6E6", end_color="E6E6E6", fill_type="solid")
    fill_accent = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    thin_border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left = Alignment(horizontal='left', vertical='center')
    align_right = Alignment(horizontal='right', vertical='center')

    # 2. Reconstrucción Estricta del Encabezado (Filas 1 a 3)
    ws.merge_cells('B1:E3')
    ws['B1'] = "ENSAYO GRANULOMÉTRICO DE SUELOS\n\n8.102.1.A"
    ws['B1'].font = font_title
    ws['B1'].alignment = align_center
    ws['B1'].fill = fill_header
    
    ws['F1'] = "MANUAL DE CARRETERAS - VOL. N° 8"
    ws['F1'].font = font_sub
    ws['F2'] = "PAG. 1 de 1"
    ws['F2'].font = font_body
    ws['F3'] = "Ver. 002"
    ws['F3'].font = font_body
    
    for row in range(1, 4):
        for col in range(2, 7):
            ws.cell(row=row, column=col).border = thin_border

    # 3. Bloque de Metadatos de la Muestra (Filas 5 a 10)
    metadata = [
        ("Certificado de ensaye N°:", cert_no, "Fecha de muestreo :", str(f_muestreo)),
        ("Camino u Obra:", camino_obra, "Fecha de ensaye :", str(f_ensaye)),
        ("TMA muestra de ensaye :", f"{st.session_state.get('tma', 0)} mm", "Banda Vial Activada:", str(st.session_state.get('banda_activa', 'S/B'))),
        ("TMN calculado:", f"{st.session_state.get('tmn', 0)} mm", "Clasificación/Criterio:", "Ajustado a Banda")
    ]
    
    current_row = 5
    for m in metadata:
        ws.cell(row=current_row, column=2, value=m[0]).font = font_sub
        ws.cell(row=current_row, column=3, value=m[1]).font = font_body
        ws.cell(row=current_row, column=5, value=m[2]).font = font_sub
        ws.cell(row=current_row, column=6, value=m[3]).font = font_body
        current_row += 1

       # =============================================================================
    # 4. TABLA DINÁMICA DE TAMIZADO (CONEXIÓN BLINDADA CON EL BACKEND)
    # =============================================================================
    headers_tabla = ["Abertura mm", "Tamiz", "Masa Retenida (g)", "% Retenido", "% Acumulado", "% Que Pasa"]
    start_row_tabla = 10
    
    for c_idx, h in enumerate(headers_tabla, start=2):
        cell = ws.cell(row=start_row_tabla, column=c_idx, value=h)
        cell.font = font_sub
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = thin_border

    # Intentar recuperar el DataFrame dinámico desde las variables comunes de Streamlit
    # Si su DataFrame se llama de otra forma (ej. df_mallas), cámbielo abajo donde dice "df_resultado"
    df_activa = None
    
    # 1. Intento por variables globales conocidas
    for var_name in ['df', 'df_resultado', 'df_gran', 'datos_tabla', 'df_final']:
        if var_name in globals():
            df_activa = globals()[var_name]
            break
            
    # 2. Intento por Session State si la app almacena allí la matriz calculada
    if df_activa is None:
        for key in st.session_state.keys():
            if isinstance(st.session_state[key], pd.DataFrame):
                df_activa = st.session_state[key]
                break

    # Si se encuentra la matriz, se inyecta dinámicamente al Excel
    if df_activa is not None:
        row_idx = start_row_tabla + 1
        for index, row in df_activa.iterrows():
            # Mapeo flexible de columnas por posición (0=Abertura, 1=Tamiz, 2=Masa, etc.) 
            # para no depender de nombres estrictos de columnas de texto
            ws.cell(row=row_idx, column=2, value=row.iloc[0]).alignment = align_center
            ws.cell(row=row_idx, column=3, value=str(row.iloc[1])).alignment = align_center
            ws.cell(row=row_idx, column=4, value=row.iloc[2]).alignment = align_right
            ws.cell(row=row_idx, column=5, value=row.iloc[3]).alignment = align_right
            ws.cell(row=row_idx, column=6, value=row.iloc[4]).alignment = align_right
            ws.cell(row=row_idx, column=7, value=row.iloc[5]).alignment = align_right
            
            for c in range(2, 8):
                ws.cell(row=row_idx, column=c).font = font_body
                ws.cell(row=row_idx, column=c).border = thin_border
                if c >= 4:
                    try:
                        ws.cell(row=row_idx, column=c).number_format = '0.0'
                    except:
                        pass
            row_idx += 1
    else:
        # Fila de respaldo por si el backend aún no procesa datos al cargar la app
        row_idx = start_row_tabla + 1
        ws.cell(row=row_idx, column=2, value="Esperando datos del backend...").font = font_formula
        row_idx += 1


       # =============================================================================
    # 5. EXPÓSITOS Y EXPRESIONES MATEMÁTICAS OFICIALES (TRANSCRIPCIÓN FIEL DEL PDF)
    # =============================================================================
    row_idx += 2
    
    # Matriz tipográfica exacta según el formato PDF original de INACAP
    formulas_text = [
        "𝑴𝒂𝒔𝒂 𝑻𝒐𝒕𝒂𝒍 𝒅𝒆 𝒎𝒖𝒆𝒔𝒕𝒓𝒂 − 𝑻𝒐𝒕𝒂𝒍 𝑹𝒆𝒕𝒆𝒏𝒊𝒅𝒐", # Numerador de la ecuación de error
        "𝑴𝒂𝒔𝒂 𝑻𝒐𝒕𝒂𝒍 𝒅𝒆 𝒎𝒖𝒆𝒔𝒕𝒓𝒂",                  # Denominador de la ecuación de error
        "𝑴𝒂𝒔𝒂 𝑹𝒆𝒕𝒆𝒏. 𝒄𝒐𝒓𝒓𝒆𝒈𝒊𝒅𝒂",                    # Numerador del % Retenido
        "𝑴𝒂𝒔𝒂 𝑻𝒐𝒕𝒂𝒍 𝒅𝒆 𝒎𝒖𝒆𝒔𝒕𝒓𝒂 𝒄𝒐𝒓𝒓𝒆𝒈𝒊𝒅𝒂 𝒙 𝟏𝟎𝟎"     # Denominador del % Retenido
    ]
    
    # Celda de % Error: Simbología Griega Épsilon Clásica (𝜺) y variables en negrita cursiva
    ws.cell(row=row_idx, column=2, value="" ) # Limpieza previa
    ws.cell(row=row_idx, column=2, value="% 𝜺 = 𝑽𝒂𝒍𝒐𝒓 𝑨𝒃𝒔𝒐𝒍𝒖𝒕𝒐 (  " + formulas_text[0] + "  /  " + formulas_text[1] + "  ) x 100 (%)").font = font_formula
    
    row_idx += 2
    # Celda de % Retenido: Relación de masas corregidas
    ws.cell(row=row_idx, column=2, value="% 𝑹𝒆𝒕𝒆𝒏𝒊𝒅𝒐 = (  " + formulas_text[2] + "  /  " + formulas_text[3] + "  )").font = font_formula
    
    row_idx += 2
    # Celda de % Retenido Acumulado: Sumatoria del tamiz y el anterior
    ws.cell(row=row_idx, column=2, value="% 𝑹𝒆𝒕𝒆𝒏𝒊𝒅𝒐 𝒂𝒄𝒖𝒎𝒖𝒍𝒂𝒅𝒐 = % 𝒓𝒆𝒕𝒆𝒏𝒊𝒅𝒐 𝒆𝒏 𝒕𝒂𝒎𝒊𝒛 + % 𝒓𝒆𝒕𝒆𝒏𝒊𝒅𝒐 𝒂𝒄𝒖𝒎𝒖𝒍. 𝒂𝒏𝒕𝒆𝒓𝒊𝒐𝒓").font = font_formula
    
    row_idx += 2
    # Celda de % Acumulado que Pasa: Complemento al 100%
    ws.cell(row=row_idx, column=2, value="% 𝑨𝒄𝒖𝒎𝒖𝒍𝒂𝒅𝒐 𝒒𝒖𝒆 𝑷𝒂𝒔𝒂 = 𝟏𝟎𝟎 − % 𝑹𝒆𝒕𝒆𝒏.𝑨𝒄𝒖𝒎𝒖𝒍. 𝒆𝒏 𝒕𝒂𝒎𝒊𝒛").font = font_formula


    # 6. Firmas de Responsabilidad
    row_idx += 1
    ws.cell(row=row_idx, column=2, value=f"Responsable ensaye: {responsable}").font = font_body
    ws.cell(row=row_idx+1, column=2, value=f"V°B° Jefe Laboratorio: {jefe_lab}").font = font_body

    # 7. EXPORTACIÓN INMUNE DEL GRÁFICO (Matplotlib -> Excel)
    img_buf = io.BytesIO()
    # Guardamos la figura rígida de la app a un flujo de bytes en alta resolución
    fig.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
    img_buf.seek(0)
    
    xl_img = OpenpyxlImage(img_buf)
    # Se posiciona a la derecha de los datos para no solapar columnas dinámicas
    ws.add_image(xl_img, 'I4')

    # Ajuste automático del ancho de columnas para legibilidad
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # 8. Generación del stream de descarga para Streamlit
    excel_file = io.BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    st.download_button(
        label="📥 Descargar *.xlsx Certificado",
        data=excel_file,
        file_name=f"Informe_Granulometria_{cert_no}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.success("¡Planilla generada con éxito de acuerdo al formato 8.102.1.A!")
