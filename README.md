# F1 Historical Data Pipeline

Pipeline de datos ETL desarrollada en Python para la extraccion, transformacion y carga (ETL) de la informacion historica completa de la Formula 1. Los datos se extraen desde la API de Jolpica (Ergast API) y se almacenan en un almacén relacional estructurado en MySQL, disenado bajo estandares de integridad relacional y optimizado para su consumo en herramientas de Business Intelligence como Power BI.

---

## Arquitectura

```
f1-data-pipeline/
├── main.py                  # Punto de entrada CLI (argparse)
├── core/
│   └── database.py          # Conexion MySQL con logging
├── scripts/
│   └── ingesters.py         # 8 funciones de ingesta ETL
├── sql/
│   ├── create_schema.sql    # DDL del modelo relacional
│   └── queries.sql          # Vistas analiticas para Power BI
├── notebooks/
│   └── tests.ipynb          # Exploracion interactiva de la API
├── requirements.txt         # Dependencias con versiones fijadas
├── .env.example             # Plantilla de variables de entorno
└── .gitignore
```

## Entidades Ingeridas

| Entidad | Registros | Descripcion |
|---------|-----------|-------------|
| `drivers` | ~881 | Catalogo maestro de pilotos |
| `constructors` | ~214 | Historial de escuderias |
| `circuits` | ~78 | Circuitos y ubicaciones geograficas |
| `status_race` | ~136 | Estados de carrera (Finished, DNF, etc.) |
| `races` | ~1,171 | Calendarios temporada 1950 - presente |
| `results` | ~25,940 | Resultados detallados por carrera |
| `qualifying` | ~11,120 | Datos de clasificacion (era moderna) |
| `pit_stops` | ~12,502 | Paradas en boxes (2010+) |

## Desafios Tecnicos Resueltos

- **Integridad relacional estricta:** Uso de `ON DUPLICATE KEY UPDATE` en lugar de `INSERT IGNORE` para garantizar consistencia.
- **Rate limiting defensivo:** Mecanismos de reintento con backoff lineal y circuit breaker para codigos HTTP 429.
- **Manejo de datos incompletos:** Control de nulos para registros historicos sin telemetria moderna.
- **Desbordamiento numerico:** Filtros defensivos en Python para outliers en tiempos de pit stops.
- **Resumen de progreso:** Cada ingesta detecta registros existentes y retoma donde se quedo.

---

## Instalacion y Configuracion

### 1. Requisitos Previos

- Python 3.12 o superior
- Servidor MySQL activo

### 2. Clonar e Instalar Dependencias

```bash
git clone <url-del-repositorio>
cd f1-data-pipeline
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

Copia el archivo de ejemplo y completa tus credenciales:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus datos de conexion:

```
DB_HOST=127.0.0.1
DB_USER=root
DB_PASS=tu_password
DB_NAME=f1_data_engine
```

### 4. Crear el Schema en MySQL

```bash
mysql -u root -p < sql/create_schema.sql
```

---

## Uso

### Ejecutar toda la ingesta

```bash
python main.py --all
```

### Ejecutar una sola entidad

```bash
python main.py --entity drivers
python main.py --entity results
python main.py --entity pitstops
```

### Ver entidades disponibles

```bash
python main.py --list
```

**Orden de ejecucion recomendado** (para respetar las dependencias FK):

```
drivers -> constructors -> circuits -> statuses -> races -> results -> qualifying -> pitstops
```

---

## Modelo Relacional

```
circuits (PK: circuit_id)
    └── races (FK: circuit_id)
            ├── results (FK: race_id, driver_id, constructor_id, status_id)
            ├── qualifying (FK: race_id, driver_id, constructor_id)
            └── pit_stops (FK: race_id, driver_id)

drivers (PK: driver_id)
constructors (PK: constructor_id)
status_race (PK: status_id)
```

## Analitica (SQL)

El archivo `sql/queries.sql` contiene 7 vistas analiticas disenadas para Power BI:

1. **Top 10 pilotos con mas victorias historicas**
2. **Rendimiento por escuderia (podios y victorias)**
3. **Evolucion anual de carreras por circuito**
4. **Distribucion de tiempos de clasificacion por era**
5. **Circuitos con mayor tasa de abandono (DNFs)**
6. **Analisis de pit stops - duracion promedio por temporada**
7. **Grid vs Final Position - efectividad de pilotos**

## Tecnologias

- **Python 3.12** - Lenguaje principal
- **MySQL** - Base de datos relacional (3FN)
- **requests** - Consumo de API REST
- **mysql-connector-python** - Driver MySQL
- **python-dotenv** - Gestion de variables de entorno
