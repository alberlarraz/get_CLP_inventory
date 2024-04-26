import urllib.request
from pprint import pprint
from html_table_parser import HTMLTableParser 
import pandas as pd
from tqdm import tqdm

def url_get_contents(url):
    req = urllib.request.Request(url = url)
    f = urllib.request.urlopen(req)
    return f.read()

# Inicializar dataframe global donde se almacenaran las tablas de las diferentes paginas
bbdd = pd.DataFrame()

# Configurar pandas para mostrar todas las filas y columnas
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

lista_dataframes = []

# repeticion por cada una de las paginas
for i in tqdm(range(355000, 359000)):
    url = 'https://echa.europa.eu/es/information-on-chemicals/cl-inventory-database/-/discli/details/' + str(i)
    # Imprimir la el número de la página como control
    #print("Compuesto: ", i)
    # Codigo para acceder la tabla y su contenido
    xhtml = url_get_contents(url).decode('utf-8')
    p = HTMLTableParser()
    p.feed(xhtml)

    head0 = ['EC / List no.', 'Name', 'CAS Number']
    head1 = ['Notified classification and labelling        General Information       EC / List no.', 'Name', 'CAS Number']
    head2 = ['Classification', 'Labelling', 'Specific Concentration limits, M-Factors', 'Notes', 'Classification affected by Impurities / Additives', 'Additional Notified Information', 'Number of Notifiers', 'Joint Entries', '']

    try:
        for j in range(len(p.tables)):
            if len(p.tables[j]) > 1:
                if p.tables[j][0] == head0 or p.tables[j][0] == head1:
                    df0 = pd.DataFrame([p.tables[j][1]], columns=p.tables[j][0])
                    #print("General Information:\n", df0)
                if p.tables[j][0] == head2:
                    data = p.tables[j][2:]

                    # Encuentra la longitud máxima de las filas
                    longitud_maxima = max(len(fila) for fila in data)
                    
                    # Completa cada fila con '' hasta que tenga la longitud máxima
                    tabla_completa_2 = [fila + [''] * (longitud_maxima - len(fila)) for fila in data]
                    
                    # Crear un DataFrame con un MultiIndex de dos niveles
                    columns2 = [
                        'Hazard_Class_and_Category_Code', 'Hazard_Statement_Code', 
                        'Labelling', 'Supplementary_Hazard_Statement_Code','Pictograms,_Signal_Word_Code',
                        'Specific_Concentration_limits,_M-Factors',
                        'Notes',
                        'Classification_affected_by Impurities_/_Additives',
                        'Additional_Notified_Information',
                        'Number_of_Notifiers',
                        'Joint_Entries',
                        'Details'
                    ]
                    
                    # Crea un DataFrame a partir de la tabla completa
                    df2 = pd.DataFrame(tabla_completa_2, columns=columns2)
                    # Imprime el DataFrame resultante
                    #print("Notified classification:\n", df2.iloc[:,[0,9]])

                    # Lista de nombres de columnas que deseas mantener
                    columnas_a_mantener = ['Hazard_Class_and_Category_Code','Hazard_Statement_Code', 'Number_of_Notifiers',]
                    # Seleccionar solo las columnas que deseas mantener
                    df2 = df2[columnas_a_mantener]

                    #Eliminamos la información extra de las frases H
                    for index, celda in enumerate(df2.Hazard_Statement_Code):
                        if celda !="":
                            df2.iloc[index, 1] = celda[:4]
                    #Completamos datos de notificadores en la tabla
                    for index, celda in enumerate(df2.Number_of_Notifiers):
                        if celda.isnumeric():
                            notifiers = celda
                        else:
                            df2.iloc[index, 2] = notifiers
                    
                    #Transformamos la columna de Number_of_Notifiers en números para poder sumarla al agrupar
                    df2['Number_of_Notifiers'] = pd.to_numeric(df2['Number_of_Notifiers'], errors='coerce')
                    #Agrupamos las frases H (Hazard_Statement_Code'), sumando la frecuencia ('Number_of_Notifiers') con la que aparecen y asignándole la categoría ('Hazard_Class_and_Category_Code') a cada una
                    df_agrupado = df2.groupby('Hazard_Statement_Code').agg({'Number_of_Notifiers':'sum', 'Hazard_Class_and_Category_Code': 'first'}).reset_index()
                    #Cambiamos los huecos por NA para eliminar la fila vacía de frases H
                    df_agrupado.replace('',pd.NA, inplace=True)
                    df_final = df_agrupado.dropna(subset=['Hazard_Class_and_Category_Code'])
                    #Añadimos en las tres primera columnas los datos de cada molécula
                    df_final.insert(0, 'EC_num', df0.iloc[:,0][0])
                    df_final.insert(1, 'CAS_num', df0.iloc[:,2][0])
                    df_final.insert(2, 'Name', df0.iloc[:,1][0])
                    #print(df_final)
                    
                    #Agrupamos el dataframe con todos los anteriores
                    lista_dataframes.append(df_final)

    except:
        pass

# Combina los dataframes en uno solo, uno debajo del otro           
resultado = pd.concat(lista_dataframes, ignore_index=True)

# Guarda el dataframe combinado en un archivo Excel
resultado.to_excel('notified_clp_355000_359000.xlsx', index=False, header=True)