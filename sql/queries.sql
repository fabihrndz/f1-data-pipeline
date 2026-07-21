-- ============================================================================
-- F1 DATA ENGINE - VISTAS ANALITICAS
-- ============================================================================
-- Consultas diseñadas para consumo directo en Power BI y reportes.
-- ============================================================================


-- 1. TOP 10 PILOTOS CON MAS VICTORIAS HISTORICAS
-- ============================================================================
SELECT
    d.driver_id,
    CONCAT(d.first_name, ' ', d.last_name) AS driver_name,
    d.nationality,
    COUNT(*) AS total_wins,
    COUNT(DISTINCT r.year_race) AS seasons_with_wins
FROM results res
JOIN drivers d ON d.driver_id = res.driver_id
JOIN races r ON r.race_id = res.race_id
WHERE res.final_position = 1
GROUP BY d.driver_id, d.first_name, d.last_name, d.nationality
ORDER BY total_wins DESC
LIMIT 10;


-- 2. RENDIMIENTO POR ESCUDERIA (PODIOS Y VICTORIAS)
-- ============================================================================
SELECT
    c.constructor_id,
    c.name AS constructor_name,
    c.nationality,
    COUNT(*) AS total_races,
    SUM(CASE WHEN res.is_podium = TRUE THEN 1 ELSE 0 END) AS total_podiums,
    SUM(CASE WHEN res.final_position = 1 THEN 1 ELSE 0 END) AS total_wins,
    ROUND(SUM(CASE WHEN res.is_podium = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS podium_rate_pct,
    ROUND(SUM(CASE WHEN res.final_position = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate_pct
FROM results res
JOIN constructors c ON c.constructor_id = res.constructor_id
GROUP BY c.constructor_id, c.name, c.nationality
HAVING total_races >= 50
ORDER BY total_wins DESC;


-- 3. EVOLUCION ANUAL DE CARRERAS POR CIRCUITO
-- ============================================================================
SELECT
    cy.country,
    cy.name AS circuit_name,
    COUNT(r.race_id) AS total_events,
    MIN(r.year_race) AS first_year,
    MAX(r.year_race) AS last_year,
    COUNT(DISTINCT r.year_race) AS active_years
FROM races r
JOIN circuits cy ON cy.circuit_id = r.circuit_id
GROUP BY cy.country, cy.name
ORDER BY total_events DESC;


-- 4. DISTRIBUCION DE TIEMPOS DE CLASIFICACION POR ERA
-- ============================================================================
-- Comparacion de rendimiento en Q3 entre epocas de la F1
SELECT
    CASE
        WHEN r.year_race BETWEEN 1950 AND 1989 THEN '1950-1989 (Analogica)'
        WHEN r.year_race BETWEEN 1990 AND 2003 THEN '1990-2003 (Pre-V10)'
        WHEN r.year_race BETWEEN 2004 AND 2013 THEN '2004-2013 (V8)'
        WHEN r.year_race >= 2014 THEN '2014-Hoy (Hibridas)'
    END AS era,
    COUNT(*) AS total_qualifying_sessions,
    COUNT(q.q3) AS q3_sessions_with_data,
    ROUND(COUNT(q.q3) * 100.0 / COUNT(*), 2) AS q3_coverage_pct
FROM qualifying q
JOIN races r ON r.race_id = q.race_id
GROUP BY era
ORDER BY MIN(r.year_race);


-- 5. TOP CIRCUITOS CON MAS ABANDONOS (ESTADISTICAS DE STATUS)
-- ============================================================================
SELECT
    cy.name AS circuit_name,
    cy.country,
    COUNT(*) AS total_results,
    SUM(CASE WHEN sr.status_description != 'Finished' AND sr.status_description NOT LIKE 'Finished%' THEN 1 ELSE 0 END) AS total_dnfs,
    ROUND(
        SUM(CASE WHEN sr.status_description != 'Finished' AND sr.status_description NOT LIKE 'Finished%' THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 2
    ) AS dnf_rate_pct
FROM results res
JOIN races r ON r.race_id = res.race_id
JOIN circuits cy ON cy.circuit_id = r.circuit_id
JOIN status_race sr ON sr.status_id = res.status_id
GROUP BY cy.name, cy.country
HAVING total_results >= 100
ORDER BY dnf_rate_pct DESC
LIMIT 15;


-- 6. ANALISIS DE PIT STOPS - DURACION PROMEDIO POR TEMPORADA
-- ============================================================================
SELECT
    r.year_race,
    COUNT(DISTINCT r.race_id) AS races_in_season,
    COUNT(*) AS total_pit_stops,
    ROUND(AVG(ps.duration), 3) AS avg_pit_stop_duration,
    ROUND(MIN(ps.duration), 3) AS fastest_pit_stop,
    ROUND(MAX(ps.duration), 3) AS slowest_pit_stop
FROM pit_stops ps
JOIN races r ON r.race_id = ps.race_id
GROUP BY r.year_race
ORDER BY r.year_race;


-- 7. GRID vs FINAL POSITION - EFECTIVIDAD EN CARRERAS
-- ============================================================================
-- Que tan bien los pilotos mejoran su posicion desde la parrilla
SELECT
    d.driver_id,
    CONCAT(d.first_name, ' ', d.last_name) AS driver_name,
    COUNT(*) AS total_races,
    ROUND(AVG(res.grid_position - res.final_position), 2) AS avg_positions_gained,
    SUM(CASE WHEN res.grid_position > res.final_position THEN 1 ELSE 0 END) AS races_improved,
    SUM(CASE WHEN res.grid_position < res.final_position THEN 1 ELSE 0 END) AS races_lost_positions
FROM results res
JOIN drivers d ON d.driver_id = res.driver_id
WHERE res.grid_position > 0 AND res.final_position IS NOT NULL
GROUP BY d.driver_id, d.first_name, d.last_name
HAVING total_races >= 50
ORDER BY avg_positions_gained DESC
LIMIT 15;
