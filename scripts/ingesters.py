import logging
import time
from datetime import datetime

import requests

from core.database import db_connection

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.jolpi.ca/ergast/f1"
SLEEP_CATALOG = 1.5
SLEEP_RACE = 3.0
SLEEP_QUALIFYING = 3.5
MAX_RETRIES_429 = 3


def ingest_all_drivers():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en drivers: %s", e)
        return

    offset = 0
    limit = 100
    total_guardados = 0

    logger.info("Sincronizando catalogo completo de pilotos...")

    try:
        while True:
            url = f"{API_BASE_URL}/drivers.json?limit={limit}&offset={offset}"
            response = requests.get(url)

            if response.status_code != 200:
                logger.error("Error en la API. Codigo de estado: %d", response.status_code)
                break

            data = response.json()
            drivers_list = data['MRData']['DriverTable']['Drivers']

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
            logger.info("Pasada completada: pilotos offset %d - %d", offset, offset + len(drivers_list))

            offset += limit
            time.sleep(SLEEP_CATALOG)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de pilotos finalizada. Total: %d", total_guardados)


def ingest_all_constructors():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en constructors: %s", e)
        return

    limit = 100
    offset = 0
    total_new = 0

    logger.info("Sincronizando catalogo completo de escuderias...")

    try:
        while True:
            url = f"{API_BASE_URL}/constructors.json?limit={limit}&offset={offset}"
            response = requests.get(url)

            if response.status_code != 200:
                logger.error("Error en la API. Codigo: %d", response.status_code)
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
            logger.info("Pasada completada: constructores offset %d - %d", offset, offset + len(constructors))

            offset += limit
            time.sleep(SLEEP_CATALOG)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de escuderias finalizada. Total: %d", total_new)


def ingest_all_circuits():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en circuits: %s", e)
        return

    limit = 100
    offset = 0
    total_procesados = 0

    logger.info("Sincronizando catalogo completo de circuitos...")

    try:
        while True:
            url = f"{API_BASE_URL}/circuits.json?limit={limit}&offset={offset}"
            response = requests.get(url)

            if response.status_code != 200:
                logger.error("Error en la API. Codigo de estado: %d", response.status_code)
                break

            data = response.json()
            circuits = data['MRData']['CircuitTable']['Circuits']

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
            logger.info("Pasada completada: circuitos offset %d - %d", offset, offset + len(circuits))

            offset += limit
            time.sleep(SLEEP_CATALOG)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de circuitos finalizada. Total: %d", total_procesados)


def ingest_all_races():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en races: %s", e)
        return

    anio_actual = datetime.now().year
    total_new = 0

    logger.info("Sincronizando calendarios historicos (1950 - %d)...", anio_actual)

    try:
        for year in range(1950, anio_actual + 1):
            url = f"{API_BASE_URL}/{year}.json"
            response = requests.get(url)

            if response.status_code != 200:
                logger.warning("Error al obtener el ano %d. Codigo: %d", year, response.status_code)
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

                if valores[5]:
                    cursor.execute(sql, valores)
                    total_new += 1

            conexion.commit()
            logger.info("Temporada %d sincronizada.", year)
            time.sleep(SLEEP_CATALOG)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de carreras finalizada. Total: %d", total_new)


def ingest_all_statuses():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en statuses: %s", e)
        return

    limit = 100
    offset = 0
    total_procesados = 0

    logger.info("Sincronizando catalogo de estados de carrera...")

    try:
        while True:
            url = f"{API_BASE_URL}/status.json?limit={limit}&offset={offset}"
            response = requests.get(url)

            if response.status_code != 200:
                logger.error("Error en la API. Codigo de estado: %d", response.status_code)
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
                    status_id = int(s.get('statusId'))
                    status_desc = s.get('status')
                    valores = (status_id, status_desc)
                    cursor.execute(sql, valores)
                    total_procesados += 1
                except (ValueError, TypeError) as parse_err:
                    logger.warning("Problema con formato de estado: %s", parse_err)
                    continue

            conexion.commit()
            logger.info("Pasada completada: estados offset %d - %d", offset, offset + len(status_list))

            offset += limit
            time.sleep(SLEEP_CATALOG)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de estados finalizada. Total: %d", total_procesados)


def ingest_all_results():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en results: %s", e)
        return

    logger.info("Comprobando progreso previo en results...")
    cursor.execute("SELECT DISTINCT race_id FROM results")
    carreras_procesadas = {row[0] for row in cursor.fetchall()}

    cursor.execute("SELECT year_race, round, race_id FROM races ORDER BY year_race ASC, round ASC")
    todas_las_carreras = cursor.fetchall()

    carreras_pendientes = [c for c in todas_las_carreras if c[2] not in carreras_procesadas]

    logger.info("Results: %d guardadas, %d pendientes", len(carreras_procesadas), len(carreras_pendientes))

    if not carreras_pendientes:
        logger.info("Todas las carreras estan sincronizadas en results.")
        cursor.close()
        conexion.close()
        return

    total_procesados = 0
    sql = """
        INSERT INTO results
        (race_id, driver_id, constructor_id, status_id, grid_position, final_position, points, laps, fastest_lap_rank, fastest_lap_time, is_podium)
        VALUES (
            %s, %s, %s,
            (SELECT status_id FROM status_race WHERE status_description = %s LIMIT 1),
            %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            status_id = VALUES(status_id),
            grid_position = VALUES(grid_position),
            final_position = VALUES(final_position),
            points = VALUES(points),
            laps = VALUES(laps),
            fastest_lap_rank = VALUES(fastest_lap_rank),
            fastest_lap_time = VALUES(fastest_lap_time),
            is_podium = VALUES(is_podium);
    """

    try:
        for year, round_num, race_id in carreras_pendientes:
            url = f"{API_BASE_URL}/{year}/{round_num}/results.json"

            reintentos_429 = 0
            while True:
                response = requests.get(url)

                if response.status_code == 429:
                    reintentos_429 += 1
                    tiempo_espera = 30.0 if reintentos_429 < 3 else 60.0
                    logger.warning("Bloqueo 429 en %s (intento %d). Esperando %.0fs...", race_id, reintentos_429, tiempo_espera)
                    time.sleep(tiempo_espera)
                    continue

                if response.status_code != 200:
                    logger.warning("Error en %s. Codigo: %d", race_id, response.status_code)
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
                logger.info("Resultados guardados: %s", race_id)
                break

            time.sleep(SLEEP_RACE)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de results finalizada. Registros anadidos: %d", total_procesados)


def ingest_qualifying():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en qualifying: %s", e)
        return

    logger.info("Comprobando progreso previo en qualifying...")
    cursor.execute("SELECT DISTINCT race_id FROM qualifying")
    carreras_procesadas = {row[0] for row in cursor.fetchall()}

    cursor.execute("SELECT year_race, round, race_id FROM races ORDER BY year_race ASC, round ASC")
    todas_las_carreras = cursor.fetchall()

    carreras_pendientes = [c for c in todas_las_carreras if c[2] not in carreras_procesadas]

    logger.info("Qualifying: %d guardadas, %d pendientes", len(carreras_procesadas), len(carreras_pendientes))

    if not carreras_pendientes:
        logger.info("Tabla qualifying sincronizada.")
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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        for year, round_num, race_id in carreras_pendientes:
            url = f"{API_BASE_URL}/{year}/{round_num}/qualifying.json"

            reintentos_429 = 0
            abortar_por_bloqueo = False

            while True:
                response = requests.get(url, headers=headers)

                if response.status_code == 429:
                    reintentos_429 += 1
                    if reintentos_429 > MAX_RETRIES_429:
                        logger.error("API bloqueada prolongadamente en %s. Deteniendo.", race_id)
                        abortar_por_bloqueo = True
                        break

                    tiempo_espera = 30.0 if reintentos_429 < 2 else 60.0
                    logger.warning("Bloqueo 429 en %s (intento %d/%d). Esperando %.0fs...", race_id, reintentos_429, MAX_RETRIES_429, tiempo_espera)
                    time.sleep(tiempo_espera)
                    continue

                if response.status_code != 200:
                    logger.warning("Error en clasificacion %s. Codigo: %d", race_id, response.status_code)
                    break

                data = response.json()
                try:
                    races_list = data['MRData']['RaceTable']['Races']
                    if not races_list:
                        logger.info("Sin datos de clasificacion para: %s", race_id)
                        break
                    qualifying_results = races_list[0].get('QualifyingResults', [])
                except (KeyError, IndexError):
                    logger.warning("Estructura inesperada en: %s", race_id)
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
                logger.info("Clasificacion guardada: %s", race_id)
                break

            if abortar_por_bloqueo:
                break

            time.sleep(SLEEP_QUALIFYING)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de qualifying finalizada. Registros anadidos: %d", total_procesados)


def ingest_pit_stops():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en pit_stops: %s", e)
        return

    cursor.execute("SELECT DISTINCT race_id FROM pit_stops")
    carreras_procesadas = {row[0] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT year_race, round, race_id
        FROM races
        WHERE year_race >= 2010
        ORDER BY year_race ASC, round ASC
    """)
    todas_las_carreras = cursor.fetchall()

    carreras_pendientes = [c for c in todas_las_carreras if c[2] not in carreras_procesadas]

    logger.info("Pit Stops: %d pendientes", len(carreras_pendientes))

    if not carreras_pendientes:
        logger.info("Tabla pit_stops sincronizada.")
        cursor.close()
        conexion.close()
        return

    sql = """
        INSERT INTO pit_stops (race_id, driver_id, stop_number, lap, duration)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE lap = VALUES(lap), duration = VALUES(duration);
    """

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        for year, round_num, race_id in carreras_pendientes:
            url = f"{API_BASE_URL}/{year}/{round_num}/pitstops.json?limit=100"

            try:
                response = requests.get(url, headers=headers)
            except Exception as e:
                logger.warning("Error de red en %s: %s", race_id, e)
                continue

            if response.status_code == 429:
                logger.error("Bloqueo 429 en %s. Deteniendo.", race_id)
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
                    if duracion and duracion > 99999.999:
                        duracion = None
                except (ValueError, TypeError):
                    duracion = None

                try:
                    cursor.execute(sql, (race_id, p.get('driverId'), int(p.get('stop', 0)), int(p.get('lap', 0)), duracion))
                except Exception as e:
                    logger.error("Error al insertar parada en %s: %s", race_id, e)
                    continue

            conexion.commit()
            if pit_stops_list:
                logger.info("Pit Stops guardados: %s (%d paradas)", race_id, len(pit_stops_list))

            time.sleep(SLEEP_QUALIFYING)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de pit_stops finalizada.")
