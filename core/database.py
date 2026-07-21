import logging
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
        )
        logger.debug("Conexion a MySQL establecida correctamente")
        return conn
    except mysql.connector.Error as e:
        logger.error("Error al conectar con MySQL: %s", e)
        raise
