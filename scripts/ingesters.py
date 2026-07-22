import logging
import time
from datetime import datetime

from core.database import db_connection
from scripts.cache import (
    TTL_CATALOG,
    TTL_RACE,
    TTL_YEAR,
    fetch_or_cache,
)

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.jolpi.ca/ergast/f1"
SLEEP_CATALOG = 2.0
SLEEP_RACE = 4.0
SLEEP_YEAR = 5.0
QUALIFYING_MIN_YEAR = 1994
RESULTS_MIN_YEAR = 1950
PITSTOPS_MIN_YEAR = 2010


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
            cache_key = f"drivers_{offset}"
            url = f"{API_BASE_URL}/drivers.json?limit={limit}&offset={offset}"
            data = fetch_or_cache(url, "catalog", cache_key, TTL_CATALOG)

            if data is None:
                logger.error("No se pudo obtener pagina de pilotos offset %d", offset)
                break

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
                try:
                    cursor.execute(sql, valores)
                    total_guardados += 1
                except Exception as e:
                    logger.error("Error al insertar piloto %s: %s", d.get('driverId'), e)
                    continue

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
            cache_key = f"constructors_{offset}"
            url = f"{API_BASE_URL}/constructors.json?limit={limit}&offset={offset}"
            data = fetch_or_cache(url, "catalog", cache_key, TTL_CATALOG)

            if data is None:
                logger.error("No se pudo obtener pagina de constructores offset %d", offset)
                break

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
                try:
                    cursor.execute(sql, valores)
                    total_new += 1
                except Exception as e:
                    logger.error("Error al insertar escuderia %s: %s", d.get('constructorId'), e)
                    continue

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
            cache_key = f"circuits_{offset}"
            url = f"{API_BASE_URL}/circuits.json?limit={limit}&offset={offset}"
            data = fetch_or_cache(url, "catalog", cache_key, TTL_CATALOG)

            if data is None:
                logger.error("No se pudo obtener pagina de circuitos offset %d", offset)
                break

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
                try:
                    cursor.execute(sql, valores)
                    total_procesados += 1
                except Exception as e:
                    logger.error("Error al insertar circuito %s: %s", c.get('circuitId'), e)
                    continue

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

    logger.info("Comprobando progreso previo en races...")
    cursor.execute("SELECT year_race, COUNT(*) FROM races GROUP BY year_race")
    counts_por_anio = {row[0]: row[1] for row in cursor.fetchall()}

    logger.info("Sincronizando calendarios historicos (1950 - %d)...", anio_actual)

    try:
        for year in range(1950, anio_actual + 1):
            ttl = TTL_YEAR if year == anio_actual else None
            url = f"{API_BASE_URL}/{year}.json"
            data = fetch_or_cache(url, "races", str(year), ttl)

            if data is None:
                logger.warning("No se pudo obtener ano %d. Saltando.", year)
                continue

            races = data['MRData']['RaceTable']['Races']

            if not races:
                continue

            api_total = len(races)
            db_count = counts_por_anio.get(year, 0)

            if db_count >= api_total:
                logger.info("Ano %d ya completo en DB (%d/%d). Saltando insercion.", year, db_count, api_total)
                time.sleep(SLEEP_CATALOG)
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
                    try:
                        cursor.execute(sql, valores)
                        total_new += 1
                    except Exception as e:
                        logger.error("Error al insertar carrera %s: %s", race_id, e)
                        continue

            conexion.commit()
            logger.info("Temporada %d sincronizada (%d carreras).", year, api_total)
            time.sleep(SLEEP_CATALOG)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de carreras finalizada. Registros insertados: %d", total_new)


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
            cache_key = f"status_{offset}"
            url = f"{API_BASE_URL}/status.json?limit={limit}&offset={offset}"
            data = fetch_or_cache(url, "catalog", cache_key, TTL_CATALOG)

            if data is None:
                logger.error("No se pudo obtener pagina de estados offset %d", offset)
                break

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
                except Exception as e:
                    logger.error("Error al insertar estado %s: %s", s.get('statusId'), e)
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
    cursor.execute("SELECT race_id, COUNT(*) FROM results GROUP BY race_id")
    counts_existentes = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute(
        "SELECT race_id, year_race, round FROM races WHERE year_race >= %s ORDER BY year_race, round",
        (RESULTS_MIN_YEAR,),
    )
    todas_carreras = cursor.fetchall()

    total_carreras = len(todas_carreras)
    con_datos = sum(1 for rid, _, _ in todas_carreras if counts_existentes.get(rid, 0) > 0)

    logger.info("Results: %d carreras totales, %d ya con datos en DB", total_carreras, con_datos)

    if not todas_carreras:
        logger.info("No hay carreras en la tabla races.")
        cursor.close()
        conexion.close()
        return

    total_procesados = 0
    total_actualizados = 0
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

    anio_actual = datetime.now().year
    current_year = None
    try:
        for idx, (race_id, year, round_num) in enumerate(todas_carreras, 1):
            if year != current_year:
                if current_year is not None:
                    time.sleep(SLEEP_YEAR)
                current_year = year

            ttl = TTL_RACE if year == anio_actual else None
            url = f"{API_BASE_URL}/{year}/{round_num}/results.json"
            data = fetch_or_cache(url, "results", race_id, ttl)

            if data is None:
                logger.warning("[%d/%d] No se pudieron obtener resultados de %s. Saltando.", idx, total_carreras, race_id)
                time.sleep(SLEEP_RACE)
                continue

            try:
                races_list = data['MRData']['RaceTable']['Races']
                if not races_list:
                    time.sleep(SLEEP_RACE)
                    continue
                results = races_list[0].get('Results', [])
            except (KeyError, IndexError):
                time.sleep(SLEEP_RACE)
                continue

            api_count = len(results)
            db_count = counts_existentes.get(race_id, 0)

            if api_count == db_count and api_count > 0:
                if idx % 100 == 0:
                    logger.info("[%d/%d] Results: verificado %s (%d registros OK)", idx, total_carreras, race_id, api_count)
                time.sleep(SLEEP_RACE)
                continue

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

                try:
                    cursor.execute(sql, valores)
                    total_procesados += 1
                except Exception as e:
                    logger.error("Error al insertar resultado en %s: %s", race_id, e)
                    continue

            conexion.commit()
            counts_existentes[race_id] = api_count
            total_actualizados += 1
            logger.info("[%d/%d] Results guardados: %s (API: %d, DB previo: %d)", idx, total_carreras, race_id, api_count, db_count)
            time.sleep(SLEEP_RACE)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de results finalizada. Carreras actualizadas: %d, Registros insertados: %d", total_actualizados, total_procesados)


def ingest_qualifying():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en qualifying: %s", e)
        return

    logger.info("Comprobando progreso previo en qualifying...")
    cursor.execute("SELECT race_id, COUNT(*) FROM qualifying GROUP BY race_id")
    counts_existentes = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute(
        "SELECT race_id, year_race, round FROM races WHERE year_race >= %s ORDER BY year_race, round",
        (QUALIFYING_MIN_YEAR,),
    )
    todas_carreras = cursor.fetchall()

    total_carreras = len(todas_carreras)
    con_datos = sum(1 for rid, _, _ in todas_carreras if counts_existentes.get(rid, 0) > 0)

    logger.info("Qualifying: %d carreras totales, %d ya con datos en DB", total_carreras, con_datos)

    if not todas_carreras:
        logger.info("No hay carreras desde %d en la tabla races.", QUALIFYING_MIN_YEAR)
        cursor.close()
        conexion.close()
        return

    total_procesados = 0
    total_actualizados = 0

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

    anio_actual = datetime.now().year
    current_year = None
    try:
        for idx, (race_id, year, round_num) in enumerate(todas_carreras, 1):
            if year != current_year:
                if current_year is not None:
                    time.sleep(SLEEP_YEAR)
                current_year = year

            ttl = TTL_RACE if year == anio_actual else None
            url = f"{API_BASE_URL}/{year}/{round_num}/qualifying.json"
            data = fetch_or_cache(url, "qualifying", race_id, ttl)

            if data is None:
                logger.warning("[%d/%d] No se pudo obtener clasificacion de %s. Saltando.", idx, total_carreras, race_id)
                time.sleep(SLEEP_RACE)
                continue

            try:
                races_list = data['MRData']['RaceTable']['Races']
                if not races_list:
                    time.sleep(SLEEP_RACE)
                    continue
                qualifying_results = races_list[0].get('QualifyingResults', [])
            except (KeyError, IndexError):
                time.sleep(SLEEP_RACE)
                continue

            api_count = len(qualifying_results)
            db_count = counts_existentes.get(race_id, 0)

            if api_count == db_count and api_count > 0:
                if idx % 100 == 0:
                    logger.info("[%d/%d] Qualifying: verificado %s (%d registros OK)", idx, total_carreras, race_id, api_count)
                time.sleep(SLEEP_RACE)
                continue

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
                try:
                    cursor.execute(sql, valores)
                    total_procesados += 1
                except Exception as e:
                    logger.error("Error al insertar clasificacion en %s: %s", race_id, e)
                    continue

            conexion.commit()
            counts_existentes[race_id] = api_count
            total_actualizados += 1
            logger.info("[%d/%d] Qualifying guardados: %s (API: %d, DB previo: %d)", idx, total_carreras, race_id, api_count, db_count)
            time.sleep(SLEEP_RACE)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de qualifying finalizada. Carreras actualizadas: %d, Registros insertados: %d", total_actualizados, total_procesados)


def ingest_pit_stops():
    try:
        conexion = db_connection()
        cursor = conexion.cursor()
    except Exception as e:
        logger.error("Error de conexion en pit_stops: %s", e)
        return

    logger.info("Comprobando progreso previo en pit_stops...")
    cursor.execute("SELECT DISTINCT race_id FROM pit_stops")
    existentes = {row[0] for row in cursor.fetchall()}

    cursor.execute("SELECT MIN(year_race) FROM races WHERE year_race >= %s", (PITSTOPS_MIN_YEAR,))
    min_year_row = cursor.fetchone()
    if not min_year_row or min_year_row[0] is None:
        logger.info("No hay carreras desde %d en la tabla races.", PITSTOPS_MIN_YEAR)
        cursor.close()
        conexion.close()
        return

    anio_actual = datetime.now().year
    carreras_pendientes = []

    for year in range(PITSTOPS_MIN_YEAR, anio_actual + 1):
        cursor.execute("SELECT race_id FROM races WHERE year_race = %s ORDER BY round ASC", (year,))
        race_ids_anio = [row[0] for row in cursor.fetchall()]
        if not race_ids_anio:
            continue
        pendientes_anio = [rid for rid in race_ids_anio if rid not in existentes]
        carreras_pendientes.extend([(year, rid) for rid in pendientes_anio])

    logger.info("Pit Stops: %d en DB, %d pendientes (%d-%d)", len(existentes), len(carreras_pendientes), PITSTOPS_MIN_YEAR, anio_actual)

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

    try:
        current_year = None
        for year, race_id in carreras_pendientes:
            if year != current_year:
                if current_year is not None:
                    time.sleep(SLEEP_YEAR)
                current_year = year

            ttl = TTL_RACE if year == anio_actual else None
            round_num = int(race_id.split('-')[1])
            url = f"{API_BASE_URL}/{year}/{round_num}/pitstops.json?limit=100"

            data = fetch_or_cache(url, "pitstops", race_id, ttl)

            if data is None:
                logger.warning("No se pudieron obtener paradas de %s. Saltando.", race_id)
                time.sleep(SLEEP_RACE)
                continue

            try:
                races_list = data['MRData']['RaceTable']['Races']
                if not races_list:
                    time.sleep(SLEEP_RACE)
                    continue
                pit_stops_list = races_list[0].get('PitStops', [])
            except (KeyError, IndexError):
                time.sleep(SLEEP_RACE)
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

            time.sleep(SLEEP_RACE)
    finally:
        cursor.close()
        conexion.close()

    logger.info("Sincronizacion de pit_stops finalizada.")
