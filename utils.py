# utils.py (VERSIÓN FINAL Y COMPLETA)

import sqlite3
from tkinter import messagebox 
import os
# Importar 'appdirs' para obtener la ruta de datos de la aplicación de forma multiplataforma
try:
    from appdirs import user_local_dir
except ImportError:
    print("Advertencia: No se encontró la librería 'appdirs'. Usando una ruta de respaldo simple.")
    def user_local_dir(name, author):
        if os.name == 'nt': 
            return os.path.join(os.environ.get('LOCALAPPDATA', ''), name)
        return os.path.join(os.path.expanduser('~'), f".{name}") 
    
import json
import hashlib
import datetime

# --- CONFIGURACIÓN DE CONSTANTES ---
DB_NAME = "darklord.db"
ADMIN_PASSWORD_RAW = "mb25adminx#" 

LICENSE_KEY_HASH_VALUE = "6a83746d4dc14abea820aa1130fe9dd3296408e411ab784b1aa122364b8674b2"
LICENSE_FILE = "license.key"

def check_license_key(input_key_raw: str) -> bool:
    """Verifica si el hash de la clave de licencia cruda ingresada (tras limpieza) coincide con el hash maestro."""
    
    # 1. Aplicar .strip() para eliminar CUALQUIER espacio/salto de línea sobrante
    cleaned_key = input_key_raw.strip()
    
    # 2. Generar el hash a partir de la clave limpia
    generated_hash = hashlib.sha256(cleaned_key.encode('utf-8')).hexdigest()

    # ⭐ DEBUG FINAL
    print(f"DEBUG: Clave de entrada limpia (Longitud {len(cleaned_key)}): '{cleaned_key}'")
    print(f"DEBUG: Hash esperado: {LICENSE_KEY_HASH_VALUE}")
    print(f"DEBUG: Hash generado: {generated_hash}")
    
    # 3. Comparar
    return generated_hash == LICENSE_KEY_HASH_VALUE


def check_license_file() -> bool:
    """Verifica si el archivo de licencia de activación existe y si su contenido es válido."""
    try:
        mdb_dir = get_db_folder_path() 
        if mdb_dir is None: return False
        license_path = os.path.join(mdb_dir, LICENSE_FILE)
        
        if not os.path.exists(license_path): return False
            
        with open(license_path, 'r') as f:
            stored_hash = f.read().strip()
            
        return stored_hash == LICENSE_KEY_HASH_VALUE
        
    except Exception as e:
        print(f"Error al verificar el archivo de licencia: {e}")
        return False

def create_license_file():
    """Crea el archivo de licencia después de la verificación exitosa."""
    try:
        mdb_dir = get_db_folder_path()
        if mdb_dir is None: return False
        
        license_path = os.path.join(mdb_dir, LICENSE_FILE)
        # Escribimos el hash del valor limpio
        with open(license_path, 'w') as f:
            f.write(LICENSE_KEY_HASH_VALUE)
        return True
    except Exception as e:
        print(f"Error al crear el archivo de licencia: {e}")
        return False
        
# --- CONSTANTES ESPECÍFICAS DE LA RUTA DE LA DB ---
APP_NAME = "BUSSINES" 
APP_AUTHOR = "SIJJ2003" 
DB_FOLDER = "MDB" 


# ===================================================================
# --- LÓGICA DE RUTA DE BASE DE DATOS FIJA ---
# ===================================================================

def get_db_folder_path():
    """Calcula la ruta absoluta de la carpeta MDB."""
    try:
        base_dir = user_local_dir(APP_NAME, APP_AUTHOR)
        mdb_dir = os.path.join(base_dir, DB_FOLDER)
        os.makedirs(mdb_dir, exist_ok=True)
        return mdb_dir
    except Exception as e:
        messagebox.showerror(
            "Error de Ruta Fija", 
            f"No se pudo determinar ni crear la ruta de la base de datos.\nError: {e}"
        )
        return None

def get_db_path_for_connection():
    """Calcula la ruta absoluta de la base de datos."""
    mdb_dir = get_db_folder_path()
    if mdb_dir is None:
        return None
        
    final_db_path = os.path.join(mdb_dir, DB_NAME)
    return final_db_path


def verify_password(input_password: str) -> bool:
    return input_password == ADMIN_PASSWORD_RAW


def setup_db() -> sqlite3.Connection:
    """Inicializa y conecta a la base de datos en la ruta fija determinada."""
    final_db_path = get_db_path_for_connection()
    
    if final_db_path is None:
        return None 

    try:
        conn = sqlite3.connect(final_db_path) 
        cursor = conn.cursor()
        
        # 1. Crear la tabla Productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio_compra REAL NOT NULL,      
                precio_venta REAL NOT NULL,      
                stock INTEGER NOT NULL,          
                proveedor TEXT,
                fecha_registro TEXT,
                stock_bultos REAL,              
                unidades_por_bulto REAL NOT NULL,
                precio_bulto REAL NOT NULL,     
                porcentaje_ganancia REAL NOT NULL 
            )
        """)


        # 2. Crear la tabla Ventas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                total_venta REAL NOT NULL,
                detalle TEXT,                      
                metodo_pago TEXT,                  
                estado TEXT NOT NULL,
                monto_total_bs REAL,
                tasa_bcv REAL
            )
        """)

        # 3. Crear la tabla AvancesEfectivo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AvancesEfectivo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                monto_entregado REAL NOT NULL,
                comision REAL NOT NULL,
                monto_total REAL NOT NULL,
                metodo_pago TEXT NOT NULL,
                fecha_hora TEXT NOT NULL,
                estado TEXT NOT NULL
            )
        """)

        # 4. Crear la tabla TasasBCV
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TasasBCV (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tasa REAL NOT NULL,
                fecha_registro TEXT NOT NULL
            )
        """)
        
        # 5. Crear la tabla RecargasTelefonicas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS RecargasTelefonicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            monto_base REAL NOT NULL,
            comision REAL NOT NULL,
            monto_total REAL NOT NULL,
            fecha_hora TEXT NOT NULL,
            estado TEXT NOT NULL
        )
       """)
        
        conn.commit()
        return conn
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        return None