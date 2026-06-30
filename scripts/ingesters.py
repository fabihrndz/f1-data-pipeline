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
        
        # Si la pagina actual viene vacia, significa que ya proceso todos los circuitos
        if not circuits:
            break

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
        
        # Avanza al siguiente bloque de 100
        offset += limit
        time.sleep(1.5) # Respiro para cumplir las politicas de la API

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
            
            # Inserción si viene el ID del circuito
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

        sql = """
            INSERT INTO status_race (status_id, status_description)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE 
                status_description = VALUES(status_description);
        """
        
        for s in status_list:
            try:
                # ID como un entero limpio para MySQL
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

    # Averigua que carreras ya proceso
    print("🔍 Comprobando progreso previo en la base de datos...")
    cursor.execute("SELECT DISTINCT race_id FROM results")
    carreras_procesadas = {row[0] for row in cursor.fetchall()} # Guarda en un set para busqueda rapida
    
    # Trae las carreras
    cursor.execute("SELECT year_race, round, race_id FROM races ORDER BY year_race ASC, round ASC")
    todas_las_carreras = cursor.fetchall()
    
    # Deja solo las carreras que faltan por descargar
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
                # Si se queda atascado muchas veces, aumentamos el tiempo de espera
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

    # Evitar duplicar llamadas si el script se frena
    print("🔍 Comprobando progreso previo en la tabla qualifying...")
    cursor.execute("SELECT DISTINCT race_id FROM qualifying")
    carreras_procesadas = {row[0] for row in cursor.fetchall()}
    
    # # Traer las carreras
    cursor.execute("SELECT year_race, round, race_id FROM races ORDER BY year_race ASC, round ASC")
    todas_las_carreras = cursor.fetchall()
    
    # Solo con las carreras que faltan por descargar
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
            
            # Control del Error 429
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
                
            # Control de otros errores
            if response.status_code != 200:
                print(f"⚠️ Error en clasificación {race_id}. Código: {response.status_code}. Pasando...")
                break 
                
            # Si el codigo es 200, procesamos el JSON
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

        # Si se activa la parada de emergencia por bloqueo IP, rompemos el bucle principal
        if abortar_por_bloqueo:
            break

        # Pausa estructural prudente entre llamadas exitosas para no estresar la API
        time.sleep(3.5)

    cursor.close()
    conexion.close()
    print(f"\n🏁 Sesión de clasificación terminada. Registros añadidos en esta tanda: {total_procesados}")


# PIT STOPS

def ingest_pit_stops():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión en pit_stops: {e}")
        return

    # 1️⃣ DETECTAR PROGRESO
    cursor.execute("SELECT DISTINCT race_id FROM pit_stops")
    carreras_procesadas = {row[0] for row in cursor.fetchall()}
    
    # 2️⃣ TRAER CARRERAS FILTRADAS (Solo desde 2010 por diseño eficiente)
    cursor.execute("""
        SELECT year_race, round, race_id 
        FROM races 
        WHERE year_race >= 2010 
        ORDER BY year_race ASC, round ASC
    """)
    todas_las_carreras = cursor.fetchall()
    
    # 3️⃣ FILTRAR PENDIENTES
    carreras_pendientes = [c for c in todas_las_carreras if c[2] not in carreras_procesadas]
    
    print(f"📊 Pipeline Pit Stops Optimizado (Filtro >= 2010):")
    print(f"   - Carreras pendientes: {len(carreras_pendientes)}")
    
    if not carreras_pendientes:
        print("🏁 ¡Tabla pit_stops sincronizada!")
        cursor.close()
        conexion.close()
        return

    sql = """
        INSERT INTO pit_stops (race_id, driver_id, stop_number, lap, duration)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE lap = VALUES(lap), duration = VALUES(duration);
    """

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for year, round_num, race_id in carreras_pendientes:
        url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_num}/pitstops.json?limit=100"
        
        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            print(f"⚠️ Error de red en {race_id}: {e}")
            continue
        
        if response.status_code == 429:
            print(f"🚨 Bloqueo 429 en {race_id}. Deteniendo para proteger IP.")
            break
            
        if response.status_code != 200:
            continue
            
        data = response.json()
        try:
            races_list = data['MRData']['RaceTable']['Races']
            if not races_list:
                continue
            pit_stops_list = races_list[0].get('PitStops', [])
        except (KeyError, IndexError):
            continue

        for p in pit_stops_list:
            try:
                duracion_str = p.get('duration', '').replace(':', '')
                duracion = float(duracion_str) if duracion_str else None
                
                # Validación defensiva avanzada para evitar desbordamientos en la BD
                if duracion and duracion > 99999.999:
                    duracion = None
            except (ValueError, TypeError):
                duracion = None

            try:
                cursor.execute(sql, (race_id, p.get('driverId'), int(p.get('stop', 0)), int(p.get('lap', 0)), duracion))
            except Exception as e:
                print(f"❌ Error al insertar parada en {race_id}: {e}")
                continue
                
        conexion.commit()
        if pit_stops_list:
            print(f"📥 Guardados Pit Stops: {race_id} ({len(pit_stops_list)} paradas)")
        
        time.sleep(3.5)

    cursor.close()
    conexion.close()