# F1 Historical Data Pipeline

Este proyecto consiste en una pipeline de datos profesional desarrollada en Python para la extracción, transformación y carga (ETL) de la información histórica completa de la Fórmula 1. Los datos se extraen desde la API de Jolpica (Ergast API) y se almacenan en un almacén relacional estructurado en MySQL, diseñado bajo estándares estrictos de integridad relacional y optimizado para su posterior consumo en herramientas de Business Intelligence como Tableau o Power BI.

## 📋 Descripción y Estado del Pipeline

La pipeline automatiza de forma robusta la recolección, paginación e inserción estricta de las siguientes entidades (1950 - Presente):

* **`drivers` (Catálogo maestro):** Sincronización completa con control de paginación dinámica y manejo de IDs compuestos largos. **(881 pilotos)**.
* **`constructors` (Catálogo maestro):** Historial completo de escuderías normalizado a formato JSON. **(214 escuderías)**.
* **`circuits` (Catálogo maestro):** Ubicaciones geográficas y metadatos técnicos de las pistas, estructurado de forma escalable. **(78 circuitos)**.
* **`status_race` (Catálogo maestro):** Tipado estricto a entero de todos los tipos de abandono y estados de carrera. **(136 estados)**.
* **`races` (Tabla de hechos intermedia):** Mapeo cronológico estructurado temporada por temporada de los calendarios oficiales. **(1,171 carreras)**.
* **`results` (Tabla de hechos principal):** Ingesta masiva y detallada del rendimiento en pista (posiciones, puntos, vueltas rápidas). **(~26,000+ registros)**.
* *`qualifying`, `pit_stops`, `lap_times`: (Estructura SQL preparada, próximas fases de desarrollo).*

## 🧠 Desafíos Técnicos Resueltos

* **Integridad Relacional Estricta:** Se eliminó el uso de inserciones permisivas (`INSERT IGNORE`) en favor de una estrategia estricta basada en `ON DUPLICATE KEY UPDATE`. Esto garantiza la consistencia de los datos históricos y fuerza la detección de anomalías en el log de ejecución.
* **Arquitectura de Datos Escalable:** Rediseño dinámico de las longitudes de las Claves Foráneas (FK) y llaves primarias en cascada a `VARCHAR(50)` para absorber desbordamientos de IDs compuestos generados por la API y evitar el truncado latente de datos.
* **Manejo Defensivo de Datos Incompletos:** Control estricto de nulos mediante excepciones para procesar correctamente la ausencia de registros de telemetría moderna (como el objeto `FastestLap`) en carreras históricas de las décadas de 1950 a 1970.
* **Optimización del Consumo de API:** Implementación de paginación mediante saltos de `offset` controlados y ventanas de tiempo (*rate limiting*) para respetar las políticas del servidor de la API sin degradar el rendimiento de la conexión.

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.12
* **Base de Datos:** MySQL (Diseño relacional en Tercera Forma Normal - 3FN)
* **Librerías:** `requests`, `mysql-connector-python`, `python-dotenv`

## 🚀 Instalación y Configuración

### 1. Requisitos Previos
* Python 3.12 o superior.
* Servidor activo de MySQL.

### 2. Clonar e Instalar Dependencias
```bash
git clone <url-del-repositorio>
cd f1-data-pipeline
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt