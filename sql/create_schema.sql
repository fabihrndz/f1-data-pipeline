CREATE SCHEMA f1_data_engine;

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  DRIVERS
CREATE TABLE drivers (
    driver_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(25),
    last_name VARCHAR(25) NOT NULL,
    nationality VARCHAR(25),
    birth_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  CONSTRUCTORS
CREATE TABLE constructors (
    constructor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    nationality VARCHAR(25),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  STATUS_RACE
CREATE TABLE status_race (
    status_id INT PRIMARY KEY,
    status_description VARCHAR(250),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  RACES
CREATE TABLE races (
    race_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    year_race YEAR,
    round INT,
    race_date DATE,
    circuit_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_races_circuits FOREIGN KEY (circuit_id) REFERENCES circuits(circuit_id) ON DELETE RESTRICT
);

--  RESULTS
CREATE TABLE results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    race_id VARCHAR(50),
    driver_id VARCHAR(50),
    constructor_id VARCHAR(50),
    status_id INT,
    grid_position SMALLINT,
    final_position SMALLINT,
    points DECIMAL(5,2) DEFAULT 0.0,
    laps INT,
    fastest_lap_rank SMALLINT,
    fastest_lap_time VARCHAR(10),
    is_podium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_results_race_driver UNIQUE (race_id, driver_id),
    CONSTRAINT fk_races_results FOREIGN KEY (race_id) REFERENCES races(race_id) ON DELETE RESTRICT,
    CONSTRAINT fk_drivers_results FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE RESTRICT,
    CONSTRAINT fk_constructors_results FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id) ON DELETE RESTRICT,
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
    CONSTRAINT uq_pitstops_race_driver_stop UNIQUE (race_id, driver_id, stop_number),
    CONSTRAINT fk_pitstops_races FOREIGN KEY (race_id) REFERENCES races(race_id) ON DELETE RESTRICT,
    CONSTRAINT fk_pitstops_drivers FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE RESTRICT
);

--  QUALIFYING
CREATE TABLE qualifying (
    qualifying_id INT AUTO_INCREMENT PRIMARY KEY,
    race_id VARCHAR(50),
    driver_id VARCHAR(50),
    constructor_id VARCHAR(50),
    position SMALLINT,
    q1 VARCHAR(10),
    q2 VARCHAR(10),
    q3 VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_qualifying_race_driver UNIQUE (race_id, driver_id),
    CONSTRAINT fk_qualifying_races FOREIGN KEY (race_id) REFERENCES races(race_id) ON DELETE RESTRICT,
    CONSTRAINT fk_qualifying_drivers FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE RESTRICT,
    CONSTRAINT fk_qualifying_constructors FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id) ON DELETE RESTRICT
);
