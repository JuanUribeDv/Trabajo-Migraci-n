"""
diagnostico.py — Verifica que todo esté listo antes de correr main.py
Ejecutar: python diagnostico.py
"""

import os
import sys
import json
import importlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OK  = "\033[92m  ✔\033[0m"
ERR = "\033[91m  ✘\033[0m"
WRN = "\033[93m  !\033[0m"

errores_criticos = 0

def ok(msg):   print(f"{OK}  {msg}")
def err(msg):  print(f"{ERR} {msg}"); global errores_criticos; errores_criticos += 1
def warn(msg): print(f"{WRN}  {msg}")


print("\n[1] Dependencias Python")
for lib in ["psycopg2", "pymongo", "faker", "dotenv"]:
    try:
        importlib.import_module(lib)
        ok(lib)
    except ImportError:
        err(f"{lib} NO instalado → pip install {lib.replace('dotenv','python-dotenv')}")


print("\n[2] Archivo .env")
env_path = os.path.join(BASE_DIR, ".env")
if not os.path.exists(env_path):
    err(".env no encontrado")
else:
    ok(".env existe")
    from dotenv import load_dotenv
    load_dotenv(env_path)
    for var in ["PG_HOST", "PG_PORT", "PG_DATABASE", "PG_USER", "PG_PASSWORD",
                "MONGO_URI", "MONGO_DATABASE"]:
        val = os.getenv(var)
        if val:
            display = val if var not in ("PG_PASSWORD",) else "***"
            ok(f"{var} = {display}")
        else:
            err(f"{var} no definida en .env")



print("\n[3] Archivos del proyecto")
archivos_requeridos = [
    "config/config_calidad.json",
    "config/mapping_mongo.json",
    "sql/Schema_legacy.sql",
    "sql/Schema_normalizado.sql",
    "sql/Stored_procedures.sql",
    "sql/Vistas_funciones_cursores.sql",
]
for rel in archivos_requeridos:
    full = os.path.join(BASE_DIR, rel)
    if os.path.exists(full):
        ok(rel)
    else:
        err(f"{rel} NO EXISTE")


print("\n[4] Validez de archivos JSON")
for rel in ["config/config_calidad.json", "config/mapping_mongo.json"]:
    full = os.path.join(BASE_DIR, rel)
    if os.path.exists(full):
        try:
            json.load(open(full, encoding="utf-8"))
            ok(f"{rel} es JSON válido")
        except json.JSONDecodeError as e:
            err(f"{rel} tiene error JSON: {e}")



print("\n[5] Conexión a PostgreSQL")
try:
    import psycopg2
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5432)),
        dbname=os.getenv("PG_DATABASE", "biblioteca_db"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
    )
    ok(f"Conectado a PostgreSQL — BD: {os.getenv('PG_DATABASE')}")

    cur = conn.cursor()

   
    cur.execute("SELECT current_database(), version()")
    db, ver = cur.fetchone()
    ok(f"Base de datos: {db}")
    ok(f"Versión: {ver[:50]}")

    
    print("\n  Tablas legacy:")
    for tabla in ["Biblioteca_Data", "Prestamos_Crudos", "Inventario_Sedes", "Resenias_Usuarios"]:
        cur.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = '{tabla}'
            )""")
        existe = cur.fetchone()[0]
        if existe:
            cur.execute(f'SELECT COUNT(*) FROM "{tabla}"')
            n = cur.fetchone()[0]
            ok(f"{tabla}: {n} registros")
        else:
            warn(f"{tabla}: no existe aún (se creará al correr main.py)")

   
    print("\n  Tablas normalizadas:")
    for tabla in ["Autores", "Libros", "Usuarios", "Prestamos", "AuditoriaLog"]:
        cur.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = '{tabla}'
            )""")
        existe = cur.fetchone()[0]
        if existe:
            cur.execute(f'SELECT COUNT(*) FROM "{tabla}"')
            n = cur.fetchone()[0]
            ok(f"{tabla}: {n} registros")
        else:
            warn(f"{tabla}: no existe aún (se creará en Fase C)")

    cur.close()
    conn.close()

except Exception as e:
    err(f"PostgreSQL falló: {e}")
    warn("Verifica: 1) PostgreSQL está corriendo  2) La BD existe  3) Credenciales en .env")
    warn(f"Para crear la BD: psql -U postgres -c \"CREATE DATABASE {os.getenv('PG_DATABASE','biblioteca_db')};\"")



print("\n[6] Conexión a MongoDB")
try:
    from pymongo import MongoClient
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"),
                         serverSelectionTimeoutMS=3000)
    client.admin.command("ping")
    ok("Conectado a MongoDB")

    db_name = os.getenv("MONGO_DATABASE", "biblioteca_mongo")
    db = client[db_name]
    colecciones = db.list_collection_names()
    if colecciones:
        print(f"\n  Colecciones en '{db_name}':")
        for col in colecciones:
            n = db[col].count_documents({})
            ok(f"  {col}: {n} documentos")
    else:
        warn(f"La BD '{db_name}' existe pero no tiene colecciones aún (se llenarán en Fase D)")

    client.close()
except Exception as e:
    err(f"MongoDB falló: {e}")
    warn("Verifica que MongoDB esté corriendo: mongod --dbpath /data/db")



print("\n" + "=" * 50)
if errores_criticos == 0:
    print("\033[92m✔ Todo OK — puedes correr: python main.py\033[0m")
else:
    print(f"\033[91m✘ {errores_criticos} errores críticos encontrados — corrígelos antes de correr main.py\033[0m")
print("=" * 50 + "\n")