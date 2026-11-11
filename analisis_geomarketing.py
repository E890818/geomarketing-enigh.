# Importación de la librería pandas para la manipulación y análisis de tablas
import pandas as pd

# Definición del nombre del archivo fuente que contiene los microdatos
archivo_real = 'concentradohogar (1).csv'

# Mensajes informativos en consola para dar seguimiento al inicio del proceso
print(f"¡Base de datos localizada con éxito: '{archivo_real}'!")
print("Cargando archivo de geomarketing... Por favor espera unos segundos.")

try:
    # Carga del archivo CSV en un DataFrame de pandas.
    # Se especifica sep=';' porque el archivo usa punto y coma como delimitador.
    # on_bad_lines='skip' evita que el programa se detenga si hay filas corruptas.
    df = pd.read_csv(archivo_real, sep=';', engine='python', on_bad_lines='skip')
    print("¡Archivo cargado con éxito en la memoria de Python!\n")
    
    # Definición de las variables clave del estudio
    COL_NSE = 'NSESintetico'          # Columna de Nivel Socioeconómico
    COL_FE = 'factor'                 # Columna del Factor de Expansión muestral
    producto_seleccionado = 'transporte'  # Categoría de gasto a analizar

    # Detección automática de la columna de Estado (en ENIGH suele ser 'entidad' o 'ubica_geo')
    col_estado = None
    for posible_col in ['entidad', 'ENTIDAD', 'estado', 'ESTADO', 'cve_ent', 'ubica_geo']:
        if posible_col in df.columns:
            col_estado = posible_col
            break

    # Validación: comprobamos que todas las columnas necesarias existan en el archivo
    if producto_seleccionado in df.columns and COL_FE in df.columns and COL_NSE in df.columns:
        
        # Limpieza de datos: convertimos gasto y factor a valores numéricos.
        # Si existen textos o valores nulos, se reemplazan por 0 con fillna(0).
        df[producto_seleccionado] = pd.to_numeric(df[producto_seleccionado], errors='coerce').fillna(0)
        df[COL_FE] = pd.to_numeric(df[COL_FE], errors='coerce').fillna(0)

        # Cálculo del gasto expandido a nivel poblacional multiplicando factor por gasto
        df['gasto_expandido'] = df[COL_FE] * df[producto_seleccionado]
        
        # Cálculo del gasto total nacional del mercado para obtener porcentajes
        total_gasto_mercado = df['gasto_expandido'].sum()
        total_hogares_nacional = df[COL_FE].sum()

        # ======================================================================
        # BLOQUE 1: GENERACIÓN DE TABLA POR NIVEL SOCIOECONÓMICO (NSE)
        # ======================================================================
        # Agrupación por NSE para sumar el gasto expandido (Gasto Absoluto)
        gasto_absoluto_nse = df.groupby(COL_NSE)['gasto_expandido'].sum()
        
        # Cálculo de la participación porcentual de cada NSE sobre el total
        gasto_relativo_nse = (gasto_absoluto_nse / total_gasto_mercado) * 100
        
        # Suma de los factores de expansión para conocer el total de hogares por NSE
        total_hogares_nse = df.groupby(COL_NSE)[COL_FE].sum()

        # Unión de las tres métricas en una sola tabla cruzada por NSE
        tabla_nse = pd.concat([gasto_absoluto_nse, gasto_relativo_nse, total_hogares_nse], axis=1)
        tabla_nse.columns = ['Gasto Absoluto', 'Gasto Relativo (%)', 'Total Hogares']
        
        # Creación de la fila de totales generales para el cuadro de NSE
        fila_total_nse = pd.DataFrame([{
            'Gasto Absoluto': total_gasto_mercado,
            'Gasto Relativo (%)': 100.0,
            'Total Hogares': total_hogares_nacional
        }], index=['Total general'])
        
        # Concatenación de los datos por NSE con su fila de totales
        tabla_final_nse = pd.concat([tabla_nse, fila_total_nse])

        # ======================================================================
        # BLOQUE 2: GENERACIÓN DE TABLA POR ESTADO (ENTIDAD FEDERATIVA)
        # ======================================================================
        tabla_final_estado = None
        if col_estado:
            # Si se usa 'ubica_geo' (5 dígitos), extraemos los primeros 2 que corresponden al Estado
            if col_estado == 'ubica_geo':
                df['clave_estado'] = df['ubica_geo'].astype(str).str.zfill(5).str[:2]
                grupo_est = 'clave_estado'
            else:
                grupo_est = col_estado

            # Diccionario oficial de claves INEGI para mostrar el nombre del Estado
            catalogo_estados = {
                '01': 'Aguascalientes', '02': 'Baja California', '03': 'Baja California Sur',
                '04': 'Campeche', '05': 'Coahuila', '06': 'Colima', '07': 'Chiapas',
                '08': 'Chihuahua', '09': 'Ciudad de México', '10': 'Durango',
                '11': 'Guanajuato', '12': 'Guerrero', '13': 'Hidalgo', '14': 'Jalisco',
                '15': 'Estado de México', '16': 'Michoacán', '17': 'Morelos', '18': 'Nayarit',
                '19': 'Nuevo León', '20': 'Oaxaca', '21': 'Puebla', '22': 'Querétaro',
                '23': 'Quintana Roo', '24': 'San Luis Potosí', '25': 'Sinaloa', '26': 'Sonora',
                '27': 'Tabasco', '28': 'Tamaulipas', '29': 'Tlaxcala', '30': 'Veracruz',
                '31': 'Yucatán', '32': 'Zacatecas'
            }

            # Estandarizamos la clave a 2 dígitos y mapeamos el nombre del estado si es numérico
            df['Estado_Nombre'] = df[grupo_est].astype(str).str.zfill(2).map(catalogo_estados).fillna(df[grupo_est])

            # Cálculo de métricas agregadas por cada Estado
            gasto_abs_est = df.groupby('Estado_Nombre')['gasto_expandido'].sum()
            gasto_rel_est = (gasto_abs_est / total_gasto_mercado) * 100
            hogares_est = df.groupby('Estado_Nombre')[COL_FE].sum()

            # Construcción de la tabla cruzada por Estado ordenada de mayor a menor gasto
            tabla_estado = pd.concat([gasto_abs_est, gasto_rel_est, hogares_est], axis=1)
            tabla_estado.columns = ['Gasto Absoluto', 'Gasto Relativo (%)', 'Total Hogares']
            tabla_estado = tabla_estado.sort_values(by='Gasto Absoluto', ascending=False)

            # Incorporación de la fila de totales generales para la tabla de Estados
            tabla_final_estado = pd.concat([tabla_estado, fila_total_nse])

        # ======================================================================
        # BLOQUE 3: IMPRESIÓN EN CONSOLA Y EXPORTACIÓN A EXCEL
        # ======================================================================
        # Función auxiliar para dar formato visual legible (comas y porcentajes) en consola
        def formatear_consola(tabla):
            copia = tabla.copy()
            copia['Gasto Absoluto'] = copia['Gasto Absoluto'].map('{:,.2f}'.format)
            copia['Gasto Relativo (%)'] = copia['Gasto Relativo (%)'].map('{:.2f}%'.format)
            copia['Total Hogares'] = copia['Total Hogares'].map('{:,.0f}'.format)
            return copia

        # Impresión de resultados por NSE
        print("=" * 70)
        print(f"TABLA CRUZADA POR NSE: {producto_seleccionado.upper()}")
        print("=" * 70)
        print(formatear_consola(tabla_final_nse))
        print("=" * 70 + "\n")

        # Impresión de resultados por Estado (si la columna fue localizada)
        if tabla_final_estado is not None:
            print("=" * 70)
            print(f"TABLA CRUZADA POR ESTADO: {producto_seleccionado.upper()}")
            print("=" * 70)
            print(formatear_consola(tabla_final_estado))
            print("=" * 70 + "\n")
        else:
            print("Aviso: No se encontró una columna de entidad/estado para generar la segunda tabla.")

        # Exportación de ambas tablas a un mismo libro de Excel en pestañas separadas
        nombre_salida = f'resultado_geomarketing_{producto_seleccionado}.xlsx'
        with pd.ExcelWriter(nombre_salida) as writer:
            tabla_final_nse.to_excel(writer, sheet_name='Por_NSE')
            if tabla_final_estado is not None:
                tabla_final_estado.to_excel(writer, sheet_name='Por_Estado')
                
        print(f"¡Análisis completo! El documento se guardó en: '{nombre_salida}'")

    else:
        # Mensaje de error en caso de que falte alguna de las columnas principales
        print("Error: Revisa las columnas de tu archivo.")
        print("Columnas que lee Python actualmente:", list(df.columns))

# Captura de excepciones generales (por ejemplo, si el archivo no existe o está abierto)
except Exception as e:
    print(f"Ocurrió un error al procesar el archivo: {e}")
