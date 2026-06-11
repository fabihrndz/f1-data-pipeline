import requests                 #importacion para las APIs
import time
from datetime import datetime
from core.database import db_connection         #Mi Funcion para acceder a la conexion con SQL


# DRIVERS

def ingest_all_drivers():
    
    try:                                #Intenta conectar con SQL 
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    
    limit = 100  # 100 pilotos por cada llamada
    offset = 0   # desde el primero
    total_new = 0

    print("🚀 Iniciando descarga de la historia de la F1...")

    while True:                                  #Un bucle para que siga ejecutandose luego de los primeros 100 pilotos
        url = f"https://api.jolpi.ca/ergast/f1/drivers?limit={limit}&offset={offset}"
        response = requests.get(url)                      #Llamada a la API
        
        if response.status_code != 200:                  #Para el bucle si no se hace bien la llamada
            break
            
        data = response.json()
        drivers = data['MRData']['DriverTable']['Drivers']    #Ubicacion de los pilotos en el Json
        
        if not drivers: # Si ya no hay mas pilotos en la lista, salir del bucle
            break
                      
                  #Query de insercion en BBDD
        sql = """                                
            INSERT IGNORE INTO drivers 
            (driver_id, first_name, last_name, nationality, driver_number, birth_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        for d in drivers:         #Datos del Json que necesito
            #.get  devuelve None si el campo no existe
            valores = (
                d.get('driverId'), 
                d.get('givenName'),
                d.get('familyName'),
                d.get('nationality'), 
                d.get('permanentNumber'),
                d.get('dateOfBirth')
            )
            
            #Solo insertamos si al menos tenemos el ID del piloto
            if valores[0]:
                cursor.execute(sql, valores)
                total_new += cursor.rowcount

        conexion.commit()
        print(f"📥 Procesados {offset + len(drivers)} pilotos...")
        
        offset += limit
        time.sleep(0.5) #Pausa para no saturar la API

    print(f"🏁 ¡Hecho! Tienes {total_new} pilotos históricos en tu base de datos.")
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    ingest_all_drivers()



# CONSTRUCTORS

def ingest_all_constructors():

    try:                                #Intenta conectar con SQL 
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    
    limit = 100  # 100 constructores por cada llamada
    offset = 0   # desde el primero
    total_new = 0

    print("🚀 Iniciando descarga de la historia de la F1...")

    while True:                         #Un bucle para que siga ejecutandose luego de los primeros 100 constructores
        url = f"https://api.jolpi.ca/ergast/f1/constructors?limit={limit}&offset={offset}"
        response = requests.get(url)            #Llamada a la API
        
        if response.status_code != 200:
            break                                #Para el bucle si no se hace bien la llamada
            
        data = response.json()
        constructors = data['MRData']['ConstructorTable']['Constructors']      #Ubicacion de los constructores en el Json
        
        if not constructors: # Si ya no hay constructores en la lista, salimos del bucle
            break
                     
                     #Query de insercion
        sql = """
            INSERT IGNORE INTO constructors 
            (constructor_id, name, nationality)
            VALUES (%s, %s, %s)
        """
        
        for d in constructors:           #datos del Json que necesito
            #.get  devuelve None si el campo no existe, evitando el KeyError
            valores = (
                d.get('constructorId'), 
                d.get('name'),
                d.get('nationality'), 
            )
            
            # Solo inserta si al menos tenemos el ID del constructor
            if valores[0]:
                cursor.execute(sql, valores)
                total_new += cursor.rowcount

        conexion.commit()
        print(f"📥 Procesados {offset + len(constructors)} constructores...")
        
        offset += limit
        time.sleep(0.5) # Pausa para no saturar la API

    print(f"🏁 ¡Hecho! Tienes {total_new} constructores históricos en tu base de datos.")
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    ingest_all_constructors()


#CIRCUITS

def ingest_all_circuits():

    try:                                #Intenta conectar con SQL 
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    total_new = 0

    print("🚀 Iniciando descarga de la historia de la F1...")

    url = f"https://api.jolpi.ca/ergast/f1/circuits?limit=200"
    response = requests.get(url)            #Llamada a la API
        
    if response.status_code != 200:
        return                                #Para el bucle si no se hace bien la llamada
            
    data = response.json()
    circuits = data['MRData']['CircuitTable']['Circuits']     #Ubicacion de los circuitos en el Json
        
    if not circuits: # Si ya no hay circuitos en la lista, salimos del bucle
        return
                     
                     #Query de insercion
    sql = """
        INSERT IGNORE INTO circuits 
        (circuit_id, name, location, country, lat, lng, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
        
    for c in circuits:           #datos del Json que necesito
            #.get  devuelve None si el campo no existe, evitando el KeyError
        valores = (
            c.get('circuitId'),
            c.get('circuitName'),
            c.get('Location', {}).get('locality'),
            c.get('Location', {}).get('country'),
            c.get('Location', {}).get('lat'),
            c.get('Location', {}).get('long'),
            c.get('url')
        )
            
            # Solo inserta si al menos tenemos el ID del circuito
        if valores[0]:
            cursor.execute(sql, valores)
            total_new += cursor.rowcount

    conexion.commit()
    print(f"🏁 ¡Hecho! Tienes {total_new} circuitos históricos en tu base de datos.")
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    ingest_all_circuits()

# RACES

def ingest_all_races():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión en Carreras: {e}")
        return

    # Año actual para que el script no quede desactualizado
    año_actual = datetime.now().year
    total_new = 0

    print(f"🚀 Iniciando la descarga de todos los calendarios de F1 (1950 - {año_actual})...")

    # Recorre año por año desde 1950 hasta el año actual
    for year in range(1950, año_actual + 1):
        url = f"https://api.jolpi.ca/ergast/f1/{year}.json"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"⚠️ No se pudieron obtener datos del año {year}. Saltando...")
            continue
            
        data = response.json()
        races = data['MRData']['RaceTable']['Races']
        
        # Si por alguna razon ese año no tiene carreras registradas salta
        if not races:
            continue

        sql = """
            INSERT IGNORE INTO races 
            (race_id, name, year_race, round, race_date, circuit_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        for r in races:
            round_num = int(r.get('round', 0))
            
            # 🧠 ID = AÑO-RONDA con formato de dos digitos
            race_id = f"{year}-{round_num:02d}"
            
            valores = (
                race_id,
                r.get('raceName'),
                year, 
                round_num,
                r.get('date'),  
                r.get('Circuit', {}).get('circuitId')  
            )
            
            # Si el circuito existe continua
            if valores[5]:
                cursor.execute(sql, valores)
                total_new += cursor.rowcount
                
        conexion.commit()
        print(f"📥 Temporada {year} procesada con éxito.")
        
        time.sleep(0.3)

    print(f"🏁 ¡Historial completo! Se han añadido {total_new} nuevas carreras a la base de datos.")
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    ingest_all_races()