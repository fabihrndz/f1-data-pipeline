import os
import requests
import mysql.connector
from dotenv import load_dotenv
import time

load_dotenv()

# DRIVERS

def ingest_all_drivers():
    try:
        conexion = mysql.connector.connect(
            host= ("localhost"),
            user= ("root"),
            password=os.getenv("SQL"),
            database= ("f1_data_engine")
        )
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    
    limit = 100  # 100 pilotos por cada llamada
    offset = 0   # desde el primero
    total_new = 0

    print("🚀 Iniciando descarga de la historia de la F1...")

    while True:
        url = f"https://api.jolpi.ca/ergast/f1/drivers.json?limit={limit}&offset={offset}"
        response = requests.get(url)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        drivers = data['MRData']['DriverTable']['Drivers']
        
        if not drivers: # Si ya no hay más pilotos en la lista, salir del bucle
            break

        sql = """
            INSERT IGNORE INTO drivers 
            (driver_id, first_name, last_name, nationality, driver_number, birth_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        for d in drivers:
            # .get  devuelve None si el campo no existe
            valores = (
                d.get('driverId'), 
                d.get('givenName'),
                d.get('familyName'),
                d.get('nationality'), 
                d.get('permanentNumber'),
                d.get('dateOfBirth')
            )
            
            # Solo insertamos si al menos tenemos el ID del piloto
            if valores[0]:
                cursor.execute(sql, valores)
                total_new += cursor.rowcount

        conexion.commit()
        print(f"📥 Procesados {offset + len(drivers)} constructores...")
        
        offset += limit
        time.sleep(0.5) # Pausa para no saturar la API

    print(f"🏁 ¡Hecho! Tienes {total_new} constructores históricos en tu base de datos.")
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    ingest_all_drivers()



# CONSTRUCTORS

def ingest_all_constructors():
    try:
        conexion = mysql.connector.connect(
            host= ("localhost"),
            user= ("root"),
            password=os.getenv("SQL"),
            database= ("f1_data_engine")
        )
        cursor = conexion.cursor()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    
    limit = 100  # 100 pilotos por cada llamada
    offset = 0   # desde el primero
    total_new = 0

    print("🚀 Iniciando descarga de la historia de la F1...")

    while True:
        url = f"https://api.jolpi.ca/ergast/f1/constructors.json?limit={limit}&offset={offset}"
        response = requests.get(url)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        constructors = data['MRData']['ConstructorTable']['Constructors']
        
        if not constructors: # Si ya no hay constructores en la lista, salimos del bucle
            break

        sql = """
            INSERT IGNORE INTO constructors 
            (constructor_id, name, nationality)
            VALUES (%s, %s, %s)
        """
        
        for d in constructors:
            # .get  devuelve None si el campo no existe, evitando el KeyError
            valores = (
                d.get('constructorId'), 
                d.get('name'),
                d.get('nationality'), 
            )
            
            # Solo inserta si al menos tenemos el ID del constructor
            if valores[0]:
                cursor.execute(sql, valores)
                total_new += cursor.rowcount

        conexion.commit()
        print(f"📥 Procesados {offset + len(constructors)} pilotos...")
        
        offset += limit
        time.sleep(0.5) # Pausa para no saturar la API

    print(f"🏁 ¡Hecho! Tienes {total_new} pilotos históricos en tu base de datos.")
    cursor.close()
    conexion.close()

if __name__ == "__main__":
    ingest_all_constructors()