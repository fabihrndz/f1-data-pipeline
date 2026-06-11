import mysql.connector                   #Importaciones necesarias para conectar a la base de datos de SQL y mis credenciales en el .env
import os
from dotenv import load_dotenv

load_dotenv()

def db_connection():                      #Codigo para conectar con SQL
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )