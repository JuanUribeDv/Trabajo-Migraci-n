"""
main.py — Orquestador del Framework de Calidad, Automatización y Migración
Biblioteca Universidad | Taller Calidad de Software
"""

import os
import json
import logging
import re
from datetime import datetime, date
from dotenv import load_dotenv

import psycopg2
import psycopg2.extras
from pymongo import MongoClient
from faker import Faker

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN INICIAL
# ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

LOG_PATH = os.path.join(BASE_DIR, "logs", "Reporte_calidad.log")
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

fake = Faker("es_CO")
fake.unique.clear()


def ruta(rel):
    """Ruta absoluta relativa al directorio del proyecto."""
    return os.path.join(BASE_DIR, rel)


# ─────────────────────────────────────────────────────────────
# CONEXIONES
# ─────────────────────────────────────────────────────────────
def get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5432)),
        dbname=os.getenv("PG_DATABASE", "biblioteca_db"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
    )


def get_mongo_client():
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


def ejecutar_sql_archivo(conn, archivo_rel):
    """Lee y ejecuta un archivo .sql completo."""
    ruta_abs = ruta(archivo_rel)
    if not os.path.exists(ruta_abs):
        log.error(f"  ✘ Archivo no encontrado: {ruta_abs}")
        return False
    cur = conn.cursor()
    try:
        with open(ruta_abs, encoding="utf-8") as f:
            sql = f.read()
        cur.execute(sql)
        conn.commit()
        log.info(f"  ✔ {archivo_rel} ejecutado OK")
        return True
    except Exception as e:
        conn.rollback()
        log.error(f"  ✘ Error en {archivo_rel}: {e}")
        return False
    finally:
        cur.close()


# ─────────────────────────────────────────────────────────────
# FASE 0 — CREAR TABLAS LEGACY
# ─────────────────────────────────────────────────────────────
def fase_0_crear_schema_legacy(conn):
    log.info("=" * 60)
    log.info("FASE 0 — Creando tablas legacy en PostgreSQL")
    log.info("=" * 60)
    ok = ejecutar_sql_archivo(conn, "sql/Schema_legacy.sql")
    if not ok:
        raise RuntimeError("No se pudo crear el schema legacy. Revisa sql/Schema_legacy.sql")
    log.info("Fase 0 completada.\n")


# ─────────────────────────────────────────────────────────────
# FASE A — POBLAMIENTO MASIVO (250 registros en tablas legacy)
# ─────────────────────────────────────────────────────────────
def fase_a_poblar_tablas_legacy(conn):
    log.info("=" * 60)
    log.info("FASE A — Poblamiento masivo de tablas legacy")
    log.info("=" * 60)

    cur = conn.cursor()
    categorias = ["Ciencias", "Historia", "Literatura", "Tecnologia", "Arte", "Filosofia"]
    estados    = ["activo", "devuelto", "vencido"]
    insertados = {"Biblioteca_Data": 0, "Prestamos_Crudos": 0,
                  "Inventario_Sedes": 0, "Resenias_Usuarios": 0}

    for i in range(250):
        try:
            categoria   = fake.random_element(categorias)
            descripcion = fake.sentence(nb_words=6)

            cur.execute(
                '''INSERT INTO "Biblioteca_Data"
                   (titulo_libro, autor_nombre, categoria_y_descripcion, editorial_info, fecha_publicacion)
                   VALUES (%s, %s, %s, %s, %s)''',
                (
                    fake.catch_phrase()[:254],
                    fake.name(),
                    f"{categoria}|{descripcion}",
                    fake.company()[:254],
                    str(fake.date_between(start_date="-50y", end_date="today")),
                ),
            )
            insertados["Biblioteca_Data"] += 1

            libros_txt = ", ".join([fake.catch_phrase() for _ in range(fake.random_int(1, 4))])
            cur.execute(
                '''INSERT INTO "Prestamos_Crudos"
                   (id_prestamo, nombre_usuario, correo_usuario, libros_prestados, fecha_salida, estado_prestamo)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (
                    i + 1,
                    fake.name(),
                    fake.email(),
                    libros_txt,
                    fake.date_between(start_date="-1y", end_date="today"),
                    fake.random_element(estados),
                ),
            )
            insertados["Prestamos_Crudos"] += 1

            cur.execute(
                '''INSERT INTO "Inventario_Sedes"
                   (sede_nombre, ubicacion_sede, libro_asociado, cantidad_total)
                   VALUES (%s, %s, %s, %s)''',
                (
                    fake.city()[:99],
                    fake.address()[:254],
                    fake.catch_phrase()[:254],
                    fake.random_int(0, 50),
                ),
            )
            insertados["Inventario_Sedes"] += 1

            cur.execute(
                '''INSERT INTO "Resenias_Usuarios"
                   (usuario_id, libro_titulo, comentario, calificacion)
                   VALUES (%s, %s, %s, %s)''',
                (
                    fake.random_int(1, 250),
                    fake.catch_phrase()[:254],
                    fake.paragraph(nb_sentences=2),
                    str(fake.random_int(1, 5)),
                ),
            )
            insertados["Resenias_Usuarios"] += 1

            if (i + 1) % 50 == 0:
                conn.commit()
                log.info(f"  ... {i+1}/250 registros procesados")

        except Exception as e:
            log.warning(f"  Registro {i+1} falló: {e}")
            conn.rollback()

    conn.commit()
    cur.close()

    for tabla, n in insertados.items():
        log.info(f"  ✔ {tabla}: {n} registros")
    log.info("Fase A completada.\n")
    return insertados


# ─────────────────────────────────────────────────────────────
# FASE B — VALIDACIÓN CON config_calidad.json
# ─────────────────────────────────────────────────────────────
def fase_b_validar_calidad(conn):
    log.info("=" * 60)
    log.info("FASE B — Validacion de calidad con JSON de reglas")
    log.info("=" * 60)

    with open(ruta("config/config_calidad.json"), encoding="utf-8") as f:
        config = json.load(f)

    reglas   = config["reglas"]
    umbrales = config["umbrales_calidad"]
    reporte  = {}

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mapa de nombre normalizado (por si la tabla tiene tilde)
    tabla_alias = {
        "Reseñas_Usuarios": "Resenias_Usuarios",
    }

    for tabla_cfg, campos in reglas.items():
        tabla = tabla_alias.get(tabla_cfg, tabla_cfg)
        errores = []
        try:
            cur.execute(f'SELECT * FROM "{tabla}"')
            filas = cur.fetchall()
        except Exception as e:
            log.error(f"  No se pudo consultar {tabla}: {e}")
            conn.rollback()
            continue

        total = len(filas)
        log.info(f"  Validando {tabla} ({total} registros)...")

        for fila in filas:
            fd = dict(fila)
            for campo, regla in campos.items():
                valor = fd.get(campo)

                if regla.get("violacion_1fn") and valor:
                    sep = regla.get("separador", "|")
                    if sep in str(valor):
                        errores.append({"tabla": tabla, "campo": campo,
                                        "tipo": "1FN", "valor": str(valor)[:60],
                                        "mensaje": regla.get("mensaje", "Viola 1FN")})

                if regla.get("requerido") and (valor is None or str(valor).strip() == ""):
                    errores.append({"tabla": tabla, "campo": campo,
                                    "tipo": "REQUERIDO", "valor": None,
                                    "mensaje": regla.get("mensaje", f"{campo} requerido")})

                if regla.get("patron") and valor:
                    if not re.match(regla["patron"], str(valor)):
                        errores.append({"tabla": tabla, "campo": campo,
                                        "tipo": "FORMATO", "valor": str(valor),
                                        "mensaje": regla.get("mensaje", "Formato invalido")})

                if regla.get("valores_permitidos") and valor:
                    if str(valor).lower() not in regla["valores_permitidos"]:
                        errores.append({"tabla": tabla, "campo": campo,
                                        "tipo": "DOMINIO", "valor": str(valor),
                                        "mensaje": regla.get("mensaje", "Valor fuera de dominio")})

                if regla.get("min") is not None and valor is not None:
                    try:
                        num = float(str(valor))
                        mx  = regla.get("max")
                        if num < regla["min"] or (mx is not None and num > mx):
                            errores.append({"tabla": tabla, "campo": campo,
                                            "tipo": "RANGO", "valor": str(valor),
                                            "mensaje": regla.get("mensaje", "Fuera de rango")})
                    except ValueError:
                        errores.append({"tabla": tabla, "campo": campo,
                                        "tipo": "TIPO_DATO", "valor": str(valor),
                                        "mensaje": f"{campo} deberia ser numerico"})

        validos = total - len(errores)
        pct     = (validos / total * 100) if total > 0 else 0
        nivel   = "OK" if pct >= umbrales["porcentaje_minimo_valido"] else "CRITICO"

        reporte[tabla] = {
            "total": total, "errores": len(errores),
            "validos": validos, "porcentaje_valido": round(pct, 2),
            "nivel": nivel, "detalle": errores[:20],
        }

        log.info(f"    {tabla}: {validos}/{total} validos ({pct:.1f}%) — {nivel}")
        for err in errores[:3]:
            log.warning(f"      [{err['tipo']}] {err['campo']}: {err['mensaje']}")

    cur.close()
    rep_path = ruta("logs/reporte_validacion.json")
    with open(rep_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2, default=str)
    log.info(f"  Reporte guardado en {rep_path}")
    log.info("Fase B completada.\n")
    return reporte


# ─────────────────────────────────────────────────────────────
# FASE C — SCHEMA NORMALIZADO + OBJETOS SQL + SEED LIMPIO
# ─────────────────────────────────────────────────────────────
def fase_c_ejecutar_objetos_sql(conn):
    log.info("=" * 60)
    log.info("FASE C — Schema normalizado, SPs, Vistas, Funciones, Cursores")
    log.info("=" * 60)

    # C.1  Schema normalizado — si falla, no tiene sentido continuar
    log.info("C.1 Aplicando schema normalizado...")
    ok = ejecutar_sql_archivo(conn, "sql/Schema_normalizado.sql")
    if not ok:
        raise RuntimeError("No se pudo crear el schema normalizado. Revisa sql/Schema_normalizado.sql")
    log.info("  ✔ Schema normalizado aplicado correctamente\n")

    # C.2  Stored procedures
    log.info("C.2 Creando stored procedures...")
    ejecutar_sql_archivo(conn, "sql/Stored_procedures.sql")

    # C.3  Vistas, funciones y cursores
    log.info("C.3 Creando vistas, funciones y cursores...")
    ejecutar_sql_archivo(conn, "sql/Vistas_funciones_cursores.sql")

    # C.4  Seed de tablas normalizadas con datos limpios
    log.info("C.4 Poblando tablas normalizadas con datos limpios...")
    cur = conn.cursor()
    try:
        autores_ids  = []
        libros_ids   = []
        usuarios_ids = []

        for _ in range(20):
            cur.execute(
                '''INSERT INTO "Autores" (nombre, nacionalidad, fecha_nacimiento)
                   VALUES (%s, %s, %s) RETURNING id_autor''',
                (fake.name(), fake.country()[:99],
                 fake.date_of_birth(minimum_age=25, maximum_age=80)),
            )
            autores_ids.append(cur.fetchone()[0])

        for _ in range(50):
            cur.execute(
                '''INSERT INTO "Libros"
                   (titulo, isbn, anio_publicacion, editorial, categoria, descripcion, id_autor)
                   VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_libro''',
                (
                    fake.catch_phrase()[:254],
                    fake.isbn13(),
                    fake.random_int(1970, 2024),
                    fake.company()[:254],
                    fake.random_element(["Ciencias", "Historia", "Literatura", "Arte", "Tecnologia"]),
                    fake.sentence(nb_words=10)[:499],
                    fake.random_element(autores_ids),
                ),
            )
            libros_ids.append(cur.fetchone()[0])

        correos_usados = set()
        for _ in range(40):
            correo = fake.unique.email()
            if correo in correos_usados:
                continue
            correos_usados.add(correo)
            cur.execute(
                '''INSERT INTO "Usuarios" (nombre, correo, telefono, fecha_registro)
                   VALUES (%s, %s, %s, %s) RETURNING id_usuario''',
                (fake.name(), correo, fake.phone_number()[:19],
                 fake.date_between(start_date="-2y", end_date="today")),
            )
            usuarios_ids.append(cur.fetchone()[0])

        for _ in range(100):
            fecha_salida   = fake.date_between(start_date="-6m", end_date="today")
            fecha_esperada = fake.date_between(start_date=fecha_salida, end_date="today")
            estado         = fake.random_element(["activo", "devuelto", "vencido"])
            fecha_real     = fecha_esperada if estado == "devuelto" else None
            cur.execute(
                '''INSERT INTO "Prestamos"
                   (id_usuario, id_libro, fecha_salida, fecha_devolucion_esperada,
                    fecha_devolucion_real, estado)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (
                    fake.random_element(usuarios_ids),
                    fake.random_element(libros_ids),
                    fecha_salida, fecha_esperada, fecha_real, estado,
                ),
            )

        conn.commit()
        log.info(f"  ✔ Autores: {len(autores_ids)} | Libros: {len(libros_ids)} "
                 f"| Usuarios: {len(usuarios_ids)} | Prestamos: 100")

    except Exception as e:
        conn.rollback()
        log.error(f"  ✘ Error en seed normalizado: {e}")
    finally:
        cur.close()

    # C.5  Consultar vista
    log.info("C.5 Consultando vista v_libros_mas_prestados...")
    cur2 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur2.execute("SELECT * FROM v_libros_mas_prestados LIMIT 5")
        filas = cur2.fetchall()
        log.info(f"  ✔ Vista retornó {len(filas)} registros")
        for fila in filas:
            log.info(f"    {dict(fila)}")
    except Exception as e:
        log.warning(f"  Vista v_libros_mas_prestados: {e}")
        conn.rollback()
    finally:
        cur2.close()

    # C.6  Función de multa
    log.info("C.6 Calculando multa para prestamo_id=1...")
    cur3 = conn.cursor()
    try:
        cur3.execute("SELECT fn_calcular_multa(1)")
        resultado = cur3.fetchone()
        log.info(f"  ✔ Multa calculada: ${resultado[0] if resultado else 0:.2f} COP")
    except Exception as e:
        log.warning(f"  fn_calcular_multa: {e}")
        conn.rollback()
    finally:
        cur3.close()

    # C.7  Cursor de auditoría
    log.info("C.7 Ejecutando cursor de auditoria...")
    cur4 = conn.cursor()
    try:
        cur4.execute("CALL sp_generar_log_auditoria()")
        conn.commit()
        log.info("  ✔ Log_Auditoria actualizado")
    except Exception as e:
        log.warning(f"  sp_generar_log_auditoria: {e}")
        conn.rollback()
    finally:
        cur4.close()

    log.info("Fase C completada.\n")

# ─────────────────────────────────────────────────────────────
# FASE D — MIGRACIÓN A MONGODB
# ─────────────────────────────────────────────────────────────
def _castear(valor, tipo):
    if valor is None:
        return None
    if tipo == "int":
        try: return int(valor)
        except: return None
    if tipo == "float":
        try: return float(valor)
        except: return None
    if tipo == "date":
        if isinstance(valor, (date, datetime)):
            return datetime(valor.year, valor.month, valor.day)
        return str(valor)
    return str(valor)


def _leer_tabla(cur, tabla):
    cur.execute(f'SELECT * FROM "{tabla}"')
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fase_d_migrar_a_mongodb(conn_pg, mongo_client):
    log.info("=" * 60)
    log.info("FASE D — Migracion automatica PostgreSQL → MongoDB")
    log.info("=" * 60)

    with open(ruta("config/mapping_mongo.json"), encoding="utf-8") as f:
        mapping = json.load(f)

    mongo_db      = mongo_client[mapping["base_datos_destino"]]
    transforms    = mapping.get("transformaciones_globales", {})
    meta_cfg      = transforms.get("agregar_metadata", {})
    metadata_base = {
        "migrated_at":     datetime.utcnow(),
        "source":          meta_cfg.get("source", "postgresql"),
        "schema_version":  meta_cfg.get("schema_version", "1.0"),
    }

    cur     = conn_pg.cursor()
    resumen = {}

    for col_name, col_cfg in mapping["colecciones"].items():
        tabla = col_cfg["tabla_origen"]
        log.info(f"  Migrando {tabla} → '{col_name}'...")

        try:
            filas = _leer_tabla(cur, tabla)
        except Exception as e:
            log.error(f"  ✘ No se pudo leer {tabla}: {e}")
            conn_pg.rollback()
            resumen[col_name] = {"error": str(e)}
            continue

        # Pre-cargar tablas de join para embeddings
        join_cache = {}
        emb_cfg = col_cfg.get("embedding")
        if emb_cfg:
            for _, emb in emb_cfg.items():
                if not isinstance(emb, dict) or "tabla_join" not in emb:
                    continue
                tj = emb["tabla_join"]
                if tj not in join_cache:
                    try:
                        rows_join = _leer_tabla(cur, tj)
                        pk = next((k for k in (rows_join[0] if rows_join else {}) if k.startswith("id_")), None)
                        join_cache[tj] = {str(r.get(pk, "")): r for r in rows_join}
                    except Exception as e:
                        log.warning(f"    No se pudo cargar join {tj}: {e}")
                        conn_pg.rollback()

        docs = []
        errores = 0
        for fila in filas:
            try:
                doc = {}
                for col_pg, cfg in col_cfg["campos"].items():
                    if not cfg.get("incluir", True):
                        continue
                    doc[cfg["destino"]] = _castear(fila.get(col_pg), cfg.get("tipo", "string"))

                doc["_metadata"] = dict(metadata_base)

                # Embeddings
                if emb_cfg:
                    for _, emb in emb_cfg.items():
                        if not isinstance(emb, dict) or "tabla_join" not in emb:
                            continue
                        tj      = emb["tabla_join"]
                        fk_val  = str(fila.get(emb["join_key"], ""))
                        row_j   = join_cache.get(tj, {}).get(fk_val)
                        if row_j:
                            doc[emb["campo_destino"]] = {
                                v: _castear(row_j.get(k), "string")
                                for k, v in emb["campos_embebidos"].items()
                            }

                # Limpiar nulos
                doc = {k: v for k, v in doc.items() if v is not None or k == "_metadata"}
                docs.append(doc)
            except Exception as e:
                errores += 1
                log.warning(f"    Doc error en {tabla}: {e}")

        insertados = 0
        if docs:
            try:
                col = mongo_db[col_name]
                col.drop()
                res = col.insert_many(docs, ordered=False)
                insertados = len(res.inserted_ids)
                for idx_campo in col_cfg.get("indices", []):
                    try: col.create_index(idx_campo)
                    except: pass
            except Exception as e:
                log.error(f"  ✘ MongoDB insert error: {e}")

        resumen[col_name] = {
            "tabla_origen": tabla,
            "total_pg": len(filas),
            "documentos_construidos": len(docs),
            "insertados_mongo": insertados,
            "errores": errores,
        }
        log.info(f"  ✔ '{col_name}': {insertados}/{len(filas)} documentos migrados")

    cur.close()
    res_path = ruta("logs/resumen_migracion.json")
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2, default=str)
    log.info(f"  Resumen guardado en {res_path}")
    log.info("Fase D completada.\n")
    return resumen


# ─────────────────────────────────────────────────────────────
# REPORTE FINAL
# ─────────────────────────────────────────────────────────────
def generar_reporte_final(migracion):
    log.info("=" * 60)
    log.info("REPORTE FINAL — Migración a MongoDB")
    log.info("=" * 60)
    total_mig  = sum(v.get("insertados_mongo", 0) for v in migracion.values())
    total_pg   = sum(v.get("total_pg", 0) for v in migracion.values())
    log.info(f"  Documentos migrados a MongoDB: {total_mig}/{total_pg}")
    for col, d in migracion.items():
        if "error" not in d:
            pct = (d["insertados_mongo"] / d["total_pg"] * 100) if d["total_pg"] > 0 else 0
            log.info(f"  MongoDB '{col}': {pct:.1f}% migrado")
    log.info(f"  Log completo: {LOG_PATH}")
    log.info("=" * 60)


# ─────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────
def main():
    log.info("Iniciando Framework de Migración — Biblioteca Universidad")
    log.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    conn_pg      = None
    mongo_client = None

    try:
        log.info("Conectando a PostgreSQL...")
        conn_pg = get_pg_conn()
        log.info("  ✔ PostgreSQL OK")

        log.info("Conectando a MongoDB...")
        mongo_client = get_mongo_client()
        mongo_client.admin.command("ping")
        log.info("  ✔ MongoDB OK\n")

        fase_c_ejecutar_objetos_sql(conn_pg)
        migracion = fase_d_migrar_a_mongodb(conn_pg, mongo_client)

        generar_reporte_final(migracion)

    except psycopg2.OperationalError as e:
        log.error(f"No se pudo conectar a PostgreSQL: {e}")
        log.error("Verifica las variables PG_* en tu archivo .env")
    except Exception as e:
        log.error(f"Error inesperado: {e}", exc_info=True)
    finally:
        if conn_pg:
            conn_pg.close()
        if mongo_client:
            mongo_client.close()
        log.info("Conexiones cerradas.")


if __name__ == "__main__":
    main()