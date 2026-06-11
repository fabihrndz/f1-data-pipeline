# F1 Data Pipeline 🏎️💨

Este proyecto es una pipeline de datos desarrollada en Python para extraer información histórica de la Fórmula 1 desde la API de Ergast (versión de jolpi.ca) y almacenarla de forma estructurada en una base de datos MySQL.

## 📋 Descripción

La pipeline permite automatizar la recolección de datos sobre:
- **Pilotos:** Información histórica detallada.
- **Constructores:** Equipos que han participado en la F1.
- **Circuitos:** Ubicaciones y detalles técnicos de las pistas.
- **Resultados y Carreras:** (En desarrollo/Estructura preparada en SQL).

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.12
- **Base de Datos:** MySQL
- **Librerías Principales:**
  - `requests`: Para el consumo de la API REST.
  - `mysql-connector-python`: Para la interacción con la base de datos.
  - `python-dotenv`: Para la gestión de variables de entorno seguras.

## 🚀 Instalación y Configuración

### 1. Requisitos Previos

- Tener instalado **Python 3**.
- Tener un servidor **MySQL** activo.

### 2. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd f1-data-pipeline
```

### 3. Instalar Dependencias

Es recomendable usar un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configuración de la Base de Datos

Ejecuta el script SQL ubicado en `sql/create_schema.sql` en tu gestor de base de datos (MySQL Workbench, DBeaver, etc.) para crear las tablas necesarias.

### 5. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con tus credenciales de MySQL:

```env
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASS=tu_contraseña
DB_NAME=f1_data_engine
```

## 💻 Uso

Para iniciar el proceso de ingesta de datos, simplemente ejecuta el archivo principal:

```bash
python main.py
```

Esto ejecutará los procesos de ingesta de pilotos y constructores definidos en `scripts/ingesters.py`.

## 📂 Estructura del Proyecto

- `main.py`: Punto de entrada de la aplicación.
- `core/`: Contiene la lógica de conexión a la base de datos.
- `scripts/`: Contiene los scripts de ingesta (`ingesters.py`) para las diferentes entidades.
- `sql/`: Scripts para la creación y mantenimiento del esquema de la base de datos.
- `notebooks/`: Espacio para pruebas y análisis exploratorio (Jupyter Notebooks).
- `requirements.txt`: Lista de dependencias del proyecto.

---
Desarrollado para el análisis y procesamiento de datos de Formula 1.
