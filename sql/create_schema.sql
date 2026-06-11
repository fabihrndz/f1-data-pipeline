CREATE SCHEMA f1_data_engine;             -- Creacion y nombre de la base de datos

USE f1_data_engine;

CREATE TABLE circuits (                   -- Creacion de la tabla para registar los circuitos, un id como clave primaria y datos de los circuitos
    circuit_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    country VARCHAR(50),
    lat DECIMAL(9,6),
    lng DECIMAL(9,6),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE drivers (                         -- Creacion de la tabla para registar a los pilotos, un id como clave primaria y datos de los pilotos
    driver_id VARCHAR(10) PRIMARY KEY,
    first_name VARCHAR(25),
    last_name VARCHAR(25) NOT NULL,
    nationality VARCHAR(25),
    driver_number SMALLINT,
    birth_date DATE,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE constructors (                       -- Creacion de la tabla para registar a los constructores, un id como clave primaria y datos de los constructores
    constructor_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    nationality VARCHAR(25),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE status_race (                                 -- Aqui se registra cualquiler incidente en la carrera
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    status_description VARCHAR(250),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE races (                                -- Datos de las pistas por fecha y condiciones 
    race_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    year_race YEAR,
    round INT,
    race_date DATE,
    weather_condition VARCHAR(100),
    circuit_id VARCHAR(10),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_races_circuits 
        FOREIGN KEY (circuit_id)
        REFERENCES circuits(circuit_id)
    ON DELETE RESTRICT
);

CREATE TABLE results (                                      -- Tabla para almacenar los resultados detallados, con foreign keys para conectar con el resto de tablas
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    race_id VARCHAR(10),
    driver_id VARCHAR(10),
    constructor_id VARCHAR(10),
    status_id INT,
    grip_position SMALLINT,
    final_position SMALLINT,
    points DECIMAL(5,2) DEFAULT 0.0,
    fastest_lap_time TIME,
    is_podium BOOLEAN DEFAULT FALSE,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_races_results
        FOREIGN KEY (race_id)
        REFERENCES races(race_id),
    CONSTRAINT fk_drivers_results
        FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id),
    CONSTRAINT fk_constructors_results
        FOREIGN KEY (constructor_id)
        REFERENCES constructors(constructor_id),
    CONSTRAINT fk_status_results
        FOREIGN KEY (status_id)
        REFERENCES status_race(status_id)
    ON DELETE RESTRICT 
);

CREATE TABLE pit_stops (
    pit_id INT AUTO_INCREMENT PRIMARY KEY
    race_id VARCHAR(10),
    driver_id VARCHAR(10),
    stop_number INT,
    lap INT,
    duration DECIMAL(6,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pitstops_races 
        FOREIGN KEY (race_id) 
        REFERENCES races(race_id),
    CONSTRAINT fk_pitstops_drivers
        FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id)
);

ALTER TABLE circuits 
ADD COLUMN url VARCHAR(255) AFTER lng;