CREATE SCHEMA f1_data_engine;             -- Creacion y nombre de la base de datos

USE f1_data_engine;

--  CIRCUITS
CREATE TABLE circuits (
    circuit_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    country VARCHAR(50),
    lat DECIMAL(9,6),
    lng DECIMAL(9,6),
    url VARCHAR(255),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  DRIVERS
CREATE TABLE drivers (
    driver_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(25),
    last_name VARCHAR(25) NOT NULL,
    nationality VARCHAR(25),
    driver_number SMALLINT,
    birth_date DATE,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  CONSTRUCTORS
CREATE TABLE constructors (
    constructor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    nationality VARCHAR(25),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  STATUS_RACE
CREATE TABLE status_race (
    status_id INT PRIMARY KEY, 
    status_description VARCHAR(250),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  RACES
CREATE TABLE races (
    race_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    year_race YEAR,
    round INT,
    race_date DATE,
    circuit_id VARCHAR(50),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_races_circuits FOREIGN KEY (circuit_id) REFERENCES circuits(circuit_id) ON DELETE RESTRICT
);

--  RESULTS 
CREATE TABLE results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    race_id VARCHAR(50),
    driver_id VARCHAR(50),
    constructor_id VARCHAR(50),
    status_id INT,
    grid_position SMALLINT,       -- Posición en parrilla (grid)
    final_position SMALLINT,      -- Posición final
    points DECIMAL(5,2) DEFAULT 0.0,
    laps INT,                     -- Vueltas completadas
    fastest_lap_rank SMALLINT,    -- Posición de su vuelta rápida en la carrera
    fastest_lap_time VARCHAR(10), 
    is_podium BOOLEAN DEFAULT FALSE,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_races_results FOREIGN KEY (race_id) REFERENCES races(race_id),
    CONSTRAINT fk_drivers_results FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    CONSTRAINT fk_constructors_results FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id),
    CONSTRAINT fk_status_results FOREIGN KEY (status_id) REFERENCES status_race(status_id) ON DELETE RESTRICT
);

--  PIT_STOPS 
CREATE TABLE pit_stops (
    pit_id INT AUTO_INCREMENT PRIMARY KEY,
    race_id VARCHAR(50),
    driver_id VARCHAR(50),
    stop_number INT,
    lap INT,
    duration DECIMAL(8,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pitstops_races FOREIGN KEY (race_id) REFERENCES races(race_id),
    CONSTRAINT fk_pitstops_drivers FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
);

--  QUALIFYING
CREATE TABLE qualifying (
    qualifying_id INT AUTO_INCREMENT PRIMARY KEY,
    race_id VARCHAR(50),
    driver_id VARCHAR(50),
    constructor_id VARCHAR(50),
    position SMALLINT,            -- Posición final en clasificación
    q1 VARCHAR(10),               -- Tiempo en Q1 
    q2 VARCHAR(10),               -- Tiempo en Q2
    q3 VARCHAR(10),               -- Tiempo en Q3
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_qualifying_races FOREIGN KEY (race_id) REFERENCES races(race_id),
    CONSTRAINT fk_qualifying_drivers FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    CONSTRAINT fk_qualifying_constructors FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id)
);