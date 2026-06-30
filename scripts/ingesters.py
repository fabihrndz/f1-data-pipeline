import requests                 #importacion para las APIs
import time
from datetime import datetime
from core.database import db_connection         #Mi Funcion para acceder a la conexion con SQL


# DRIVERS

def ingest_all_drivers():
    conexion = db_connection()
    cursor = conexion.cursor()
    
    offset = 0
    limit = 100
    total_guardados = 0
    
    print("🏎️ Sincronizando catálogo completo de pilotos de forma estricta...")
    
    while True:
        url = f"https://api.jolpi.ca/ergast/f1/drivers.json?limit={limit}&offset={offset}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"❌ Error en la API. Código de estado: {response.status_code}")
            break
            
        data = response.json()
        drivers_list = data['MRData']['DriverTable']['Drivers']
        
        # Si ya no vienen mas pilotos en la pagina, el catalogo ha terminado
        if not drivers_list:
            break
            
        sql = """
            INSERT INTO drivers (driver_id, first_name, last_name, nationality, birth_date)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                nationality = VALUES(nationality),
                birth_date = VALUES(birth_date);
        """
        
        for d in drivers_list:
            valores = (
                d.get('driverId'),
                d.get('givenName'),
                d.get('familyName'),
                d.get('nationality'),
                d.get('dateOfBirth')
            )
            cursor.execute(sql, valores)
            total_guardados += 1
            
        conexion.commit()
        print(f"📥 Pasada completada: Procesados pilotos desde el offset {offset} al {offset + len(drivers_list)}")
        
        # Avanza a la siguiente página de 100
        offset += limit
        time.sleep(1.5) # Tiempo de espera para respetar la API
        
    cursor.close()
    conexion.close()
    print(f"🏁 ¡Sincronización de pilotos terminada con éxito! Total procesados: {total_guardados}")



# CONSTRUCTORS

def ingest_all_constructors():
    try: 
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    limit = 100  
    offset = 0   
    total_new = 0

    print("🚀 Sincronizando catálogo completo de escuderías...")

    while True: 
        url = f"https://api.jolpi.ca/ergast/f1/constructors.json?limit={limit}&offset={offset}"
        response = requests.get(url) 
        
        if response.status_code != 200:
            print(f"❌ Error en la API. Código: {response.status_code}")
            break 
            
        data = response.json()
        constructors = data['MRData']['ConstructorTable']['Constructors'] 
        
        if not constructors: 
            break
                     
        # Eliminamos el IGNORE. Usamos ON DUPLICATE KEY para actualizar si el ID ya existe
        sql = """
            INSERT INTO constructors (constructor_id, name, nationality)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name),
                nationality = VALUES(nationality);
        """
        
        for d in constructors: 
            valores = (
                d.get('constructorId'), 
                d.get('name'),
                d.get('nationality')
            )
            
            cursor.execute(sql, valores)
            total_new += 1

        conexion.commit()
        print(f"📥 Pasada completada: Procesados constructores desde el offset {offset} al {offset + len(constructors)}")
        
        offset += limit
        time.sleep(1.5) # Respiro de seguridad para evitar bloqueos de la API

    cursor.close()
    conexion.close()
    print(f"🏁 ¡Hecho! Sincronización terminada con éxito.")


#CIRCUITS

def ingest_all_circuits():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    limit = 100
    offset = 0
    total_procesados = 0

    print("🚀 Sincronizando catálogo completo de circuitos de forma paginada...")

    while True:
        url = f"https://api.jolpi.ca/ergast/f1/circuits.json?limit={limit}&offset={offset}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"❌ Error en la API. Código de estado: {response.status_code}")
            break
            
        data = response.json()
        circuits = data['MRData']['CircuitTable']['Circuits']
        
        # Si la página actual viene vacía, significa que ya procesamos todos los circuitos
        if not circuits:
            break

        # Query estricta con ON DUPLICATE KEY UPDATE
        sql = """
            INSERT INTO circuits (circuit_id, name, location, country, lat, lng, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name),
                location = VALUES(location),
                country = VALUES(country),
                lat = VALUES(lat),
                lng = VALUES(lng),
                url = VALUES(url);
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
            cursor.execute(sql, valores)
            total_procesados += 1

        conexion.commit()
        print(f"📥 Pasada completada: Procesados circuitos desde el offset {offset} al {offset + len(circuits)}")
        
        # Avanzamos al siguiente bloque de 100
        offset += limit
        time.sleep(1.5) # Respiro para cumplir las políticas de la API

    cursor.close()
    conexion.close()
    print(f"🏁 ¡Hecho! Catálogo cerrado. Total circuitos procesados: {total_procesados}")


# RACES

def ingest_all_races():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión en Carreras: {e}")
        return

    año_actual = datetime.now().year
    total_new = 0

    print(f"🚀 Sincronizando calendarios históricos año por año (1950 - {año_actual})...")

    for year in range(1950, año_actual + 1):
        url = f"https://api.jolpi.ca/ergast/f1/{year}.json"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"⚠️ Error al obtener el año {year}. Código: {response.status_code}")
            time.sleep(2.0)
            continue
            
        data = response.json()
        races = data['MRData']['RaceTable']['Races']
        
        if not races:
            continue

        # Eliminamos el IGNORE. Usamos ON DUPLICATE KEY UPDATE para ser estrictos
        sql = """
            INSERT INTO races (race_id, name, year_race, round, race_date, circuit_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                name = VALUES(name),
                race_date = VALUES(race_date),
                circuit_id = VALUES(circuit_id);
        """
        
        for r in races:
            round_num = int(r.get('round', 0))
            race_id = f"{year}-{round_num:02d}"
            
            valores = (
                race_id,
                r.get('raceName'),
                year, 
                round_num,
                r.get('date'),  
                r.get('Circuit', {}).get('circuitId')  
            )
            
            # Forzamos la inserción estricta si viene el ID del circuito
            if valores[5]:
                cursor.execute(sql, valores)
                total_new += 1
                
        conexion.commit()
        print(f"📥 Temporada {year} sincronizada con éxito.")
        time.sleep(1.0)

    cursor.close()
    conexion.close()
    print(f"🏁 ¡Historial completo! Total de carreras procesadas en el pipeline: {total_new}")


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
    total_procesados = 0

    print("🚀 Sincronizando catálogo completo de estados de carrera...")

    while True:
        url = f"https://api.jolpi.ca/ergast/f1/status.json?limit={limit}&offset={offset}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"❌ Error en la API. Código de estado: {response.status_code}")
            break
            
        data = response.json()
        status_list = data['MRData']['StatusTable']['Status']
        
        if not status_list:
            break

        # Eliminamos el IGNORE. Usamos ON DUPLICATE KEY UPDATE para ser estrictos
        sql = """
            INSERT INTO status_race (status_id, status_description)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE 
                status_description = VALUES(status_description);
        """
        
        for s in status_list:
            try:
                # Nos aseguramos de pasar el ID como un entero limpio para MySQL
                status_id = int(s.get('statusId'))
                status_desc = s.get('status')
                
                valores = (status_id, status_desc)
                
                cursor.execute(sql, valores)
                total_procesados += 1
            except (ValueError, TypeError) as parse_err:
                print(f"⚠️ Ocurrió un problema con el formato de un estado: {parse_err}")
                continue

        conexion.commit()
        print(f"📥 Pasada completada: Procesados estados desde el offset {offset} al {offset + len(status_list)}")
        
        offset += limit
        time.sleep(1.0) # Respiro de seguridad para la API

    cursor.close()
    conexion.close()
    print(f"🏁 ¡Hecho! Catálogo cerrado. Total de estados procesados: {total_procesados}")


    # RESULTS

def ingest_all_results():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    # 1️⃣ DETECTAR PROGRESO: Averiguar qué carreras ya procesamos antes del bloqueo
    print("🔍 Comprobando progreso previo en la base de datos...")
    cursor.execute("SELECT DISTINCT race_id FROM results")
    carreras_procesadas = {row[0] for row in cursor.fetchall()} # Guardamos en un set para búsqueda rápida
    
    # 2️⃣ TRAER TODAS LAS CARRERAS PLANIFICADAS
    cursor.execute("SELECT year_race, round, race_id FROM races ORDER BY year_race ASC, round ASC")
    todas_las_carreras = cursor.fetchall()
    
    # 3️⃣ FILTRAR: Dejar solo las carreras que faltan por descargar
    carreras_pendientes = [c for c in todas_las_carreras if c[2] not in carreras_procesadas]
    
    print(f"📊 Estado actual del pipeline:")
    print(f"   - Carreras ya guardadas con éxito: {len(carreras_procesadas)}")
    print(f"   - Carreras pendientes por descargar: {len(carreras_pendientes)}")
    
    if not carreras_pendientes:
        print("🏁 ¡Felicidades! Todas las carreras ya están completamente sincronizadas.")
        cursor.close()
        conexion.close()
        return

    total_procesados = 0
    sql = """
        INSERT INTO results 
        (race_id, driver_id, constructor_id, status_id, grip_position, final_position, points, laps, fastest_lap_rank, fastest_lap_time, is_podium)
        VALUES (
            %s, %s, %s, 
            (SELECT status_id FROM status_race WHERE status_description = %s LIMIT 1), 
            %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE 
            status_id = VALUES(status_id),
            grip_position = VALUES(grip_position),
            final_position = VALUES(final_position),
            points = VALUES(points),
            laps = VALUES(laps),
            fastest_lap_rank = VALUES(fastest_lap_rank),
            fastest_lap_time = VALUES(fastest_lap_time),
            is_podium = VALUES(is_podium);
    """

    for year, round_num, race_id in carreras_pendientes:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/results.json"
        
        reintentos_429 = 0
        while True:
            response = requests.get(url)
            
            if response.status_code == 429:
                reintentos_429 += 1
                # Si se queda atascado muchas veces, aumentamos drásticamente el tiempo de espera
                tiempo_espera = 30.0 if reintentos_429 < 3 else 60.0
                print(f"🛑 Bloqueo 429 en {race_id} (Intento {reintentos_429}). Enfriando por {tiempo_espera}s...")
                time.sleep(tiempo_espera)
                continue 
                
            if response.status_code != 200:
                print(f"⚠️ Error en {race_id}. Código: {response.status_code}. Pasando a la siguiente...")
                break 
                
            data = response.json()
            races_list = data['MRData']['RaceTable']['Races']
            if not races_list:
                break
                
            results = races_list[0]['Results']
            
            for r in results:
                try:
                    final_pos = int(r.get('position', 0))
                except (ValueError, TypeError):
                    final_pos = None

                fastest_lap_obj = r.get('FastestLap', {})
                try:
                    fl_rank = int(fastest_lap_obj.get('rank', 0)) if fastest_lap_obj else None
                except (ValueError, TypeError):
                    fl_rank = None

                fl_time = fastest_lap_obj.get('Time', {}).get('time') if fastest_lap_obj else None

                valores = (
                    race_id,
                    r.get('Driver', {}).get('driverId'),
                    r.get('Constructor', {}).get('constructorId'),
                    r.get('status'), 
                    int(r.get('grid', 0)),
                    final_pos,
                    float(r.get('points', 0)),
                    int(r.get('laps', 0)),
                    fl_rank,
                    fl_time,
                    True if final_pos in [1, 2, 3] else False
                )
                
                cursor.execute(sql, valores)
                total_procesados += 1
                    
            conexion.commit() 
            print(f"📥 Resultados reanudados y guardados: {race_id}")
            break 

        # 3 segundos de pausa obligatoria entre llamadas exitosas para no estresar la API
        time.sleep(3.0)

    cursor.close()
    conexion.close()
    print(f"🏁 Sesión de sincronización terminada. Nuevos registros añadidos: {total_procesados}")


# QUALIFYING

def ingest_qualifying():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión en qualifying: {e}")
        return

    # 1️⃣ DETECTAR PROGRESO: Evitar duplicar llamadas si el script se frena
    print("🔍 Comprobando progreso previo en la tabla qualifying...")
    cursor.execute("SELECT DISTINCT race_id FROM qualifying")
    carreras_procesadas = {row[0] for row in cursor.fetchall()}
    
    # 2️⃣ TRAER TODAS LAS CARRERAS PLANIFICADAS
    cursor.execute("SELECT year_race, round, race_id FROM races ORDER BY year_race ASC, round ASC")
    todas_las_carreras = cursor.fetchall()
    
    # 3️⃣ FILTRAR: Quedarnos solo con las carreras que faltan por descargar
    carreras_pendientes = [c for c in todas_las_carreras if c[2] not in carreras_procesadas]
    
    print(f"📊 Estado del pipeline de Clasificación:")
    print(f"   - Carreras ya guardadas en qualifying: {len(carreras_procesadas)}")
    print(f"   - Carreras pendientes por descargar: {len(carreras_pendientes)}")
    
    if not carreras_pendientes:
        print("🏁 ¡Todo listo! La tabla qualifying ya está completamente sincronizada.")
        cursor.close()
        conexion.close()
        return

    total_procesados = 0
    
    sql = """
        INSERT INTO qualifying 
        (race_id, driver_id, constructor_id, position, q1, q2, q3)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            constructor_id = VALUES(constructor_id),
            position = VALUES(position),
            q1 = VALUES(q1),
            q2 = VALUES(q2),
            q3 = VALUES(q3);
    """

    # Cabecera para simular un navegador web real y evitar bloqueos extras
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for year, round_num, race_id in carreras_pendientes:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/qualifying.json"
        
        reintentos_429 = 0
        abortar_por_bloqueo = False
        
        while True:
            response = requests.get(url, headers=headers)
            
            # Control inteligente del Error 429
            if response.status_code == 429:
                reintentos_429 += 1
                if reintentos_429 > 3:
                    print(f"\n🚨 La API ha bloqueado nuestra IP de forma prolongada en {race_id}.")
                    print("🛑 Deteniendo el script de forma segura para proteger el pipeline. ¡Tu progreso está a salvo!")
                    abortar_por_bloqueo = True
                    break 
                
                tiempo_espera = 30.0 if reintentos_429 < 2 else 60.0
                print(f"🛑 Bloqueo 429 en {race_id} (Intento {reintentos_429}/3). Enfriando por {tiempo_espera}s...")
                time.sleep(tiempo_espera)
                continue 
                
            # Control de otros errores (404, 500, etc.)
            if response.status_code != 200:
                print(f"⚠️ Error en clasificación {race_id}. Código: {response.status_code}. Pasando...")
                break 
                
            # Si el código es 200, procesamos el JSON
            data = response.json()
            try:
                races_list = data['MRData']['RaceTable']['Races']
                if not races_list:
                    print(f"ℹ️ Sin datos de clasificación registrados para: {race_id}")
                    break
                qualifying_results = races_list[0].get('QualifyingResults', [])
            except (KeyError, IndexError):
                print(f"⚠️ Estructura inesperada en: {race_id}")
                break

            for q in qualifying_results:
                try:
                    posicion_final = int(q.get('position', 0))
                except (ValueError, TypeError):
                    posicion_final = None

                valores = (
                    race_id,
                    q.get('Driver', {}).get('driverId'),
                    q.get('Constructor', {}).get('constructorId'),
                    posicion_final,
                    q.get('Q1'), 
                    q.get('Q2'), 
                    q.get('Q3')
                )
                cursor.execute(sql, valores)
                total_procesados += 1
                    
            conexion.commit() 
            print(f"📥 Clasificación guardada: {race_id}")
            break 

        # Si se activó la parada de emergencia por bloqueo IP, rompemos el bucle principal
        if abortar_por_bloqueo:
            break

        # Pausa estructural prudente entre llamadas exitosas para no estresar la API
        time.sleep(3.5)

    cursor.close()
    conexion.close()
    print(f"\n🏁 Sesión de clasificación terminada. Registros añadidos en esta tanda: {total_procesados}")

