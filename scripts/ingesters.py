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
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    año_actual = datetime.now().year
    total_new = 0
    print(f"🚀 Descargando circuitos históricos año por año (1950 - {año_actual})...")

    # Recorre año por año para capturar los circuitos exactos de cada época
    for year in range(1950, año_actual + 1):
        url = f"https://api.jolpi.ca/ergast/f1/{year}/circuits.json?limit=100"
        response = requests.get(url)
        
        if response.status_code != 200:
            continue
            
        data = response.json()
        circuits = data['MRData']['CircuitTable']['Circuits']
        
        if not circuits:
            continue

        sql = """
            INSERT IGNORE INTO circuits 
            (circuit_id, name, location, country, lat, lng, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        for c in circuits:
            valores = (
                c.get('circuitId'),
                c.get('circuitName'),
                c.get('Location', {}).get('locality'),
                c.get('Location', {}).get('country'),
                c.get('Location', {}).get('lat'),
                c.get('Location', {}).get('long'),
                c.get('url')
            )
            
            if valores[0]:
                cursor.execute(sql, valores)
                total_new += cursor.rowcount

        conexion.commit()
        # Imprime solo cada 10 años para no llenar la pantalla de texto
        if year % 10 == 0 or year == año_actual:
            print(f"📥 Estado: Procesados circuitos hasta el año {year}...")
        
        time.sleep(0.5) # Pausa para no saturar la API

    print(f"🏁 ¡Hecho! Se han añadido {total_new} circuitos históricos.")
    cursor.close()
    conexion.close()


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
            print(f"⚠️ API respondió con código {response.status_code}. No se pudo cargar este bloque.")
            time.sleep(3.0)
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
        
        time.sleep(1.5)

    print(f"🏁 ¡Historial completo! Se han añadido {total_new} nuevas carreras a la base de datos.")
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    ingest_all_races()


    # STATUS

def ingest_all_statuses():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    limit = 100
    offset = 0
    total_new = 0

    print("🚀 Descargando todos los estados de carreras.")

    while True:
        url = f"https://api.jolpi.ca/ergast/f1/status.json?limit={limit}&offset={offset}"
        response = requests.get(url)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        status_list = data['MRData']['StatusTable']['Status']
        
        # Si ya no hay mas estados en esa pagina, rompe el bucle
        if not status_list:
            break

        sql = """
            INSERT IGNORE INTO status_race (status_id, status_description)
            VALUES (%s, %s)
        """
        
        for s in status_list:
            valores = (
                s.get('statusId'),
                s.get('status')
            )
            if valores[0]:
                cursor.execute(sql, valores)
                total_new += cursor.rowcount

        conexion.commit()
        print(f"📥 Procesados {offset + len(status_list)} estados...")
        
        # Avanzamos los siguientes 100
        offset += limit
        time.sleep(0.3)

    print(f"🏁 ¡Hecho! Tienes {total_new} estados guardados en tu base de datos.")
    cursor.close()
    conexion.close()

    # RESULTS

def ingest_all_results():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    print("🔍 Consultando las carreras almacenadas en la base de datos...")
    cursor.execute("SELECT year_race, round, race_id FROM races ORDER BY year_race ASC, round ASC")
    carreras_en_db = cursor.fetchall()

    if not carreras_en_db:
        print("⚠️ No hay carreras en la tabla 'races'.")
        cursor.close()
        conexion.close()
        return

    total_new = 0
    print(f"🚀 Descargando resultados para {len(carreras_en_db)} carreras...")

    for year, round_num, race_id in carreras_en_db:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/results.json"
        response = requests.get(url)
        
        if response.status_code != 200:
            continue
            
        data = response.json()
        races_list = data['MRData']['RaceTable']['Races']
        if not races_list:
            continue
            
        results = races_list[0]['Results']
        
        sql = """
            INSERT IGNORE INTO results 
            (race_id, driver_id, constructor_id, status_id, grip_position, final_position, points, laps, fastest_lap_rank, fastest_lap_time, is_podium)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for r in results:
            driver_id = r.get('Driver', {}).get('driverId')
            constructor_id = r.get('Constructor', {}).get('constructorId')
            status_id = int(r.get('statusId', 0))
            grip_position = int(r.get('grid', 0))
            
            try:
                final_position = int(r.get('position', 0))
            except (ValueError, TypeError):
                final_position = None
                
            points = float(r.get('points', 0))
            laps = int(r.get('laps', 0))
            
            fastest_lap_info = r.get('FastestLap', {})
            try:
                fastest_lap_rank = int(fastest_lap_info.get('rank', 0))
            except (ValueError, TypeError):
                fastest_lap_rank = None
                
            fastest_lap_time = fastest_lap_info.get('Time', {}).get('time') 
            is_podium = True if final_position in [1, 2, 3] else False

            valores = (
                race_id, driver_id, constructor_id, status_id,
                grip_position, final_position, points, laps,
                fastest_lap_rank, fastest_lap_time, is_podium
            )
            
            if valores[0] and valores[1] and valores[2]:
                cursor.execute(sql, valores)
                total_new += cursor.rowcount
                
        conexion.commit()
        print(f"📥 Resultados guardados: {race_id}")
        time.sleep(1.0)

    print(f"🏁 ¡Hecho! Se han añadido {total_new} filas a 'results'.")
    cursor.close()
    conexion.close()