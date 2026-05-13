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

# ──────────────────────────────────────────────
# CONFIGURACIÓN INICIAL
# ──────────────────────────────────────────────
load_dotenv()

LOG_PATH = "logs/Reporte_calidad.log"
os.makedirs("logs", exist_ok=True)

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


# ──────────────────────────────────────────────
# CONEXIONES
# ──────────────────────────────────────────────
def get_pg_conn():
    """Retorna conexión a PostgreSQL usando variables de entorno."""
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", 5432),
        dbname=os.getenv("PG_DATABASE", "biblioteca_db"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "tu_contraseña"),
    )


def get_mongo_client():
    """Retorna cliente MongoDB."""
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return MongoClient(uri)


# ──────────────────────────────────────────────
# FASE A — POBLAMIENTO MASIVO (250 registros)
# ──────────────────────────────────────────────
def fase_a_poblar_tablas_legacy(conn):
    """
    Inserta 250 registros en las tablas legacy (sin normalizar)
    para demostrar ineficiencia con volumen alto.
    """
    log.info("=" * 60)
    log.info("FASE A — Poblamiento masivo de tablas legacy")
    log.info("=" * 60)

    cur = conn.cursor()
    categorias = ["Ciencias", "Historia", "Literatura", "Tecnología", "Arte", "Filosofía"]
    estados = ["activo", "devuelto", "vencido"]

    insertados = {"Biblioteca_Data": 0, "Prestamos_Crudos": 0,
                  "Inventario_Sedes": 0, "Reseñas_Usuarios": 0}

    for i in range(250):
        try:
            # Biblioteca_Data — campo combinado intencional (viola 1FN)
            categoria = fake.random_element(categorias)
            descripcion = fake.sentence(nb_words=6)
            cur.execute(
                """INSERT INTO "Biblioteca_Data"
                   (titulo_libro, autor_nombre, categoria_y_descripcion,
                    editorial_info, fecha_publicacion)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    fake.catch_phrase(),
                    fake.name(),
                    f"{categoria}|{descripcion}",          # viola 1FN a propósito
                    fake.company(),
                    str(fake.date_between(start_date="-50y", end_date="today")),  # VARCHAR, no DATE
                ),
            )
            insertados["Biblioteca_Data"] += 1

            # Prestamos_Crudos — lista separada por comas (viola 1FN)
            libros = ", ".join([fake.catch_phrase() for _ in range(fake.random_int(1, 4))])
            cur.execute(
                """INSERT INTO "Prestamos_Crudos"
                   (id_prestamo, nombre_usuario, correo_usuario,
                    libros_prestados, fecha_salida, estado_prestamo)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    i + 1,
                    fake.name(),
                    fake.email(),
                    libros,
                    fake.date_between(start_date="-1y", end_date="today"),
                    fake.random_element(estados),
                ),
            )
            insertados["Prestamos_Crudos"] += 1

            # Inventario_Sedes
            cur.execute(
                """INSERT INTO "Inventario_Sedes"
                   (sede_nombre, ubicacion_sede, libro_asociado, cantidad_total)
                   VALUES (%s, %s, %s, %s)""",
                (
                    fake.city(),
                    fake.address(),
                    fake.catch_phrase(),
                    fake.random_int(0, 50),
                ),
            )
            insertados["Inventario_Sedes"] += 1

            # Reseñas_Usuarios — calificacion como VARCHAR (viola tipo)
            cur.execute(
                """INSERT INTO "Reseñas_Usuarios"
                   (usuario_id, libro_titulo, comentario, calificacion)
                   VALUES (%s, %s, %s, %s)""",
                (
                    fake.random_int(1, 250),
                    fake.catch_phrase(),
                    fake.paragraph(nb_sentences=2),
                    str(fake.random_int(1, 5)),  # VARCHAR a propósito
                ),
            )
            insertados["Reseñas_Usuarios"] += 1

        except Exception as e:
            log.warning(f"Error en registro {i+1}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cur.close()

    for tabla, n in insertados.items():
        log.info(f"  ✔ {tabla}: {n} registros insertados")
    log.info("Fase A completada.\n")
    return insertados


# ──────────────────────────────────────────────
# FASE B — VALIDACIÓN CON config_calidad.json
# ──────────────────────────────────────────────
def fase_b_validar_calidad(conn):
    """
    Lee config_calidad.json y valida cada tabla.
    Genera entradas en el log con errores encontrados.
    """
    log.info("=" * 60)
    log.info("FASE B — Validación de calidad con JSON de reglas")
    log.info("=" * 60)

    with open("config/config_calidad.json", encoding="utf-8") as f:
        config = json.load(f)

    reglas = config["reglas"]
    umbrales = config["umbrales_calidad"]
    reporte = {}

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    for tabla, campos in reglas.items():
        errores = []
        try:
            cur.execute(f'SELECT * FROM "{tabla}"')
            filas = cur.fetchall()
        except Exception as e:
            log.error(f"No se pudo consultar {tabla}: {e}")
            continue

        total = len(filas)
        log.info(f"Validando {tabla} ({total} registros)...")

        for fila in filas:
            fila_dict = dict(fila)
            for campo, regla in campos.items():
                valor = fila_dict.get(campo)

                # Violación 1FN — campo combinado con separador
                if regla.get("violacion_1fn") and valor:
                    sep = regla.get("separador", "|")
                    if sep in str(valor):
                        errores.append({
                            "tabla": tabla, "campo": campo,
                            "valor": str(valor)[:60],
                            "tipo": "1FN",
                            "mensaje": regla.get("mensaje", "Violación 1FN")
                        })

                # Campo requerido vacío
                if regla.get("requerido") and (valor is None or str(valor).strip() == ""):
                    errores.append({
                        "tabla": tabla, "campo": campo, "valor": None,
                        "tipo": "REQUERIDO",
                        "mensaje": regla.get("mensaje", f"{campo} es requerido")
                    })

                # Validación de correo
                if regla.get("patron") and valor:
                    if not re.match(regla["patron"], str(valor)):
                        errores.append({
                            "tabla": tabla, "campo": campo, "valor": str(valor),
                            "tipo": "FORMATO",
                            "mensaje": regla.get("mensaje", "Formato inválido")
                        })

                # Valores permitidos
                if regla.get("valores_permitidos") and valor:
                    if str(valor).lower() not in regla["valores_permitidos"]:
                        errores.append({
                            "tabla": tabla, "campo": campo, "valor": str(valor),
                            "tipo": "DOMINIO",
                            "mensaje": regla.get("mensaje", "Valor fuera del dominio")
                        })

                # Rango numérico
                if regla.get("min") is not None and valor is not None:
                    try:
                        num = float(str(valor))
                        if num < regla["min"] or (regla.get("max") and num > regla["max"]):
                            errores.append({
                                "tabla": tabla, "campo": campo, "valor": str(valor),
                                "tipo": "RANGO",
                                "mensaje": regla.get("mensaje", f"Valor fuera de rango [{regla['min']}-{regla.get('max')}]")
                            })
                    except ValueError:
                        errores.append({
                            "tabla": tabla, "campo": campo, "valor": str(valor),
                            "tipo": "TIPO_DATO",
                            "mensaje": f"{campo} debería ser numérico"
                        })

        validos = total - len(errores)
        pct = (validos / total * 100) if total > 0 else 0
        nivel = "OK" if pct >= umbrales["porcentaje_minimo_valido"] else "CRITICO"

        reporte[tabla] = {
            "total": total,
            "errores": len(errores),
            "validos": validos,
            "porcentaje_valido": round(pct, 2),
            "nivel": nivel,
            "detalle": errores[:20],  # primeros 20 errores en log
        }

        log.info(f"  {tabla}: {validos}/{total} válidos ({pct:.1f}%) — {nivel}")
        for err in errores[:5]:
            log.warning(f"    [{err['tipo']}] {err['campo']}: {err['mensaje']} | valor={err['valor']}")

    cur.close()

    # Guardar reporte JSON en logs
    reporte_path = "logs/reporte_validacion.json"
    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2, default=str)

    log.info(f"Reporte de validación guardado en {reporte_path}")
    log.info("Fase B completada.\n")
    return reporte


# ──────────────────────────────────────────────
# FASE C — STORED PROCEDURES, VISTAS, FUNCIONES
# ──────────────────────────────────────────────
def fase_c_ejecutar_objetos_sql(conn):
    """
    Ejecuta los scripts SQL normalizados y llama a objetos de BD
    (stored procedures, vistas, cursores, funciones) desde Python.
    """
    log.info("=" * 60)
    log.info("FASE C — Ejecución de objetos SQL desde Python")
    log.info("=" * 60)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # ── C.1 Ejecutar Schema normalizado ──────────────────────────
    log.info("C.1 Aplicando schema normalizado...")
    try:
        with open("sql/Schema_normalizado.sql", encoding="utf-8") as f:
            sql_normalizado = f.read()
        cur.execute(sql_normalizado)
        conn.commit()
        log.info("  ✔ Schema normalizado aplicado")
    except Exception as e:
        log.error(f"  ✘ Error aplicando schema: {e}")
        conn.rollback()

    # ── C.2 Ejecutar Stored Procedures ───────────────────────────
    log.info("C.2 Creando stored procedures...")
    try:
        with open("sql/Stored_procedures.sql", encoding="utf-8") as f:
            sql_sp = f.read()
        cur.execute(sql_sp)
        conn.commit()
        log.info("  ✔ Stored procedures creados")
    except Exception as e:
        log.error(f"  ✘ Error creando SPs: {e}")
        conn.rollback()

    # ── C.3 Ejecutar Vistas, Funciones y Cursores ─────────────────
    log.info("C.3 Creando vistas, funciones y cursores...")
    try:
        with open("sql/Vistas_funciones_cursores.sql", encoding="utf-8") as f:
            sql_vfc = f.read()
        cur.execute(sql_vfc)
        conn.commit()
        log.info("  ✔ Vistas, funciones y cursores creados")
    except Exception as e:
        log.error(f"  ✘ Error: {e}")
        conn.rollback()

    # ── C.4 Llamar SP insertar_libro desde Python ─────────────────
    log.info("C.4 Insertando datos limpios via Stored Procedures...")
    libros_insertados = 0
    for _ in range(10):
        try:
            cur.execute(
                "CALL insertar_libro(%s, %s, %s, %s, %s, %s)",
                (
                    fake.catch_phrase(),
                    fake.isbn13(),
                    fake.random_int(1950, 2024),
                    fake.company(),
                    fake.random_element(["Ciencias", "Literatura", "Historia", "Arte"]),
                    fake.sentence(nb_words=8),
                ),
            )
            libros_insertados += 1
        except Exception as e:
            log.warning(f"  SP insertar_libro: {e}")
            conn.rollback()

    conn.commit()
    log.info(f"  ✔ {libros_insertados} libros insertados via SP")

    # ── C.5 Consultar vista libros_mas_prestados ──────────────────
    log.info("C.5 Consultando vista libros_mas_prestados...")
    try:
        cur.execute("SELECT * FROM libros_mas_prestados LIMIT 10")
        filas = cur.fetchall()
        log.info(f"  ✔ Vista retornó {len(filas)} registros")
        for fila in filas:
            log.info(f"    {dict(fila)}")
    except Exception as e:
        log.warning(f"  Vista libros_mas_prestados: {e}")

    # ── C.6 Ejecutar función de multa para usuario 1 ──────────────
    log.info("C.6 Calculando multa para usuario_id=1...")
    try:
        cur.execute("SELECT calcular_multa(1)")
        resultado = cur.fetchone()
        multa = resultado[0] if resultado else 0
        log.info(f"  ✔ Multa calculada: ${multa:.2f} COP")
    except Exception as e:
        log.warning(f"  Función calcular_multa: {e}")

    # ── C.7 Ejecutar cursor de auditoría ─────────────────────────
    log.info("C.7 Ejecutando cursor de auditoría de préstamos activos...")
    try:
        cur.execute("CALL ejecutar_auditoria_prestamos()")
        conn.commit()
        log.info("  ✔ Cursor de auditoría ejecutado")
    except Exception as e:
        log.warning(f"  Cursor auditoría: {e}")

    cur.close()
    log.info("Fase C completada.\n")


# ──────────────────────────────────────────────
# FASE D — MIGRACIÓN A MONGODB
# ──────────────────────────────────────────────
def _castear_valor(valor, tipo_destino):
    """Convierte un valor Python al tipo indicado en el mapping."""
    if valor is None:
        return None
    if tipo_destino == "int":
        try:
            return int(valor)
        except (ValueError, TypeError):
            return None
    if tipo_destino == "float":
        try:
            return float(valor)
        except (ValueError, TypeError):
            return None
    if tipo_destino == "date":
        if isinstance(valor, (date, datetime)):
            return datetime(valor.year, valor.month, valor.day) if isinstance(valor, date) else valor
        return str(valor)
    return str(valor)


def _extraer_tabla(cur, tabla):
    """Retorna todas las filas de una tabla como lista de dicts."""
    cur.execute(f'SELECT * FROM "{tabla}"')
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, fila)) for fila in cur.fetchall()]


def _construir_documento(fila, campos_mapping, metadata):
    """Construye un documento MongoDB a partir de una fila y el mapping."""
    doc = {}
    for col_pg, regla in campos_mapping.items():
        if not regla.get("incluir", True):
            continue
        valor = fila.get(col_pg)
        doc[regla["destino"]] = _castear_valor(valor, regla.get("tipo", "string"))

    doc["_metadata"] = metadata
    return doc


def fase_d_migrar_a_mongodb(conn_pg, mongo_client):
    """
    Lee mapping_mongo.json y migra las 4 tablas normalizadas
    de PostgreSQL a colecciones MongoDB con embeddings.
    """
    log.info("=" * 60)
    log.info("FASE D — Migración automática PostgreSQL → MongoDB")
    log.info("=" * 60)

    with open("config/mapping_mongo.json", encoding="utf-8") as f:
        mapping = json.load(f)

    db_destino = mapping["base_datos_destino"]
    mongo_db = mongo_client[db_destino]
    transformaciones = mapping.get("transformaciones_globales", {})

    metadata_base = {}
    if transformaciones.get("agregar_metadata"):
        meta_cfg = transformaciones["agregar_metadata"]
        metadata_base = {
            "migrated_at": datetime.utcnow(),
            "source": meta_cfg.get("source", "postgresql"),
            "schema_version": meta_cfg.get("schema_version", "1.0"),
        }

    cur = conn_pg.cursor()
    resumen_migracion = {}

    for nombre_coleccion, config_col in mapping["colecciones"].items():
        tabla = config_col["tabla_origen"]
        log.info(f"Migrando {tabla} → colección '{nombre_coleccion}'...")

        try:
            filas = _extraer_tabla(cur, tabla)
        except Exception as e:
            log.error(f"  ✘ No se pudo leer {tabla}: {e}")
            resumen_migracion[nombre_coleccion] = {"error": str(e)}
            continue

        # Precargar tablas de embedding si es necesario
        embedding_cfg = config_col.get("embedding")
        tabla_join_cache = {}
        if embedding_cfg:
            for emb_key, emb_conf in embedding_cfg.items():
                if isinstance(emb_conf, dict) and "tabla_join" in emb_conf:
                    tj = emb_conf["tabla_join"]
                    if tj not in tabla_join_cache:
                        try:
                            filas_join = _extraer_tabla(cur, tj)
                            pk = emb_conf["join_key"].replace("id_", "id_")
                            # Intentar detectar PK de la tabla join
                            pk_col = next(
                                (k for k in (filas_join[0].keys() if filas_join else [])
                                 if k.startswith("id_")), None
                            )
                            tabla_join_cache[tj] = {
                                str(row.get(pk_col, row.get(emb_conf["join_key"], ""))): row
                                for row in filas_join
                            }
                        except Exception as e:
                            log.warning(f"  No se pudo cargar tabla join {tj}: {e}")

        documentos = []
        errores_doc = 0

        for fila in filas:
            try:
                doc = _construir_documento(
                    fila, config_col["campos"], dict(metadata_base)
                )

                # Aplicar embeddings
                if embedding_cfg:
                    for emb_key, emb_conf in embedding_cfg.items():
                        if not isinstance(emb_conf, dict) or "tabla_join" not in emb_conf:
                            continue
                        tj = emb_conf["tabla_join"]
                        fk_val = str(fila.get(emb_conf["join_key"], ""))
                        fila_join = tabla_join_cache.get(tj, {}).get(fk_val)
                        if fila_join:
                            subdoc = {
                                v: _castear_valor(fila_join.get(k), "string")
                                for k, v in emb_conf["campos_embebidos"].items()
                            }
                            doc[emb_conf["campo_destino"]] = subdoc

                # Limpiar nulos si el mapping lo indica
                if transformaciones.get("nulos_como") is None:
                    doc = {k: v for k, v in doc.items() if v is not None or k == "_metadata"}

                documentos.append(doc)

            except Exception as e:
                errores_doc += 1
                log.warning(f"  Error construyendo doc de {tabla}: {e}")

        # Insertar en MongoDB
        insertados_mongo = 0
        if documentos:
            try:
                coleccion = mongo_db[nombre_coleccion]
                coleccion.drop()  # limpiar antes de migrar
                resultado = coleccion.insert_many(documentos, ordered=False)
                insertados_mongo = len(resultado.inserted_ids)

                # Crear índices
                for campo_idx in config_col.get("indices", []):
                    try:
                        coleccion.create_index(campo_idx)
                    except Exception:
                        pass

            except Exception as e:
                log.error(f"  ✘ Error insertando en MongoDB: {e}")

        resumen_migracion[nombre_coleccion] = {
            "tabla_origen": tabla,
            "total_pg": len(filas),
            "documentos_construidos": len(documentos),
            "insertados_mongo": insertados_mongo,
            "errores": errores_doc,
        }
        log.info(
            f"  ✔ {insertados_mongo}/{len(filas)} documentos migrados"
            f" (errores: {errores_doc})"
        )

    cur.close()

    # Guardar resumen de migración
    resumen_path = "logs/resumen_migracion.json"
    with open(resumen_path, "w", encoding="utf-8") as f:
        json.dump(resumen_migracion, f, ensure_ascii=False, indent=2, default=str)

    log.info(f"Resumen de migración guardado en {resumen_path}")
    log.info("Fase D completada.\n")
    return resumen_migracion


# ──────────────────────────────────────────────
# REPORTE FINAL
# ──────────────────────────────────────────────
def generar_reporte_final(poblamiento, validacion, migracion):
    """Imprime y guarda el resumen ejecutivo del framework."""
    log.info("=" * 60)
    log.info("REPORTE FINAL — Framework de Calidad")
    log.info("=" * 60)

    total_insertados = sum(poblamiento.values())
    total_errores_val = sum(v.get("errores", 0) for v in validacion.values())
    total_migrados = sum(v.get("insertados_mongo", 0) for v in migracion.values())
    total_pg = sum(v.get("total_pg", 0) for v in migracion.values())

    log.info(f"  Registros poblados (legacy):    {total_insertados}")
    log.info(f"  Errores de calidad detectados:  {total_errores_val}")
    log.info(f"  Documentos migrados a MongoDB:  {total_migrados}/{total_pg}")

    for tabla, datos in validacion.items():
        log.info(
            f"  {tabla}: {datos.get('porcentaje_valido', 0):.1f}% válido — {datos.get('nivel', 'N/A')}"
        )

    for col, datos in migracion.items():
        if "error" not in datos:
            pct = (datos["insertados_mongo"] / datos["total_pg"] * 100) if datos["total_pg"] > 0 else 0
            log.info(f"  MongoDB '{col}': {pct:.1f}% migrado")

    log.info("=" * 60)
    log.info(f"Log completo: {LOG_PATH}")
    log.info("=" * 60)


# ──────────────────────────────────────────────
# PUNTO DE ENTRADA
# ──────────────────────────────────────────────
def main():
    log.info("Iniciando Framework de Calidad — Biblioteca Universidad")
    log.info(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    conn_pg = None
    mongo_client = None

    try:
        log.info("Conectando a PostgreSQL...")
        conn_pg = get_pg_conn()
        log.info("  ✔ Conexión PostgreSQL OK")

        log.info("Conectando a MongoDB...")
        mongo_client = get_mongo_client()
        mongo_client.admin.command("ping")
        log.info("  ✔ Conexión MongoDB OK\n")

        # Ejecutar fases en orden
        poblamiento = fase_a_poblar_tablas_legacy(conn_pg)
        validacion  = fase_b_validar_calidad(conn_pg)
        fase_c_ejecutar_objetos_sql(conn_pg)
        migracion   = fase_d_migrar_a_mongodb(conn_pg, mongo_client)

        generar_reporte_final(poblamiento, validacion, migracion)

    except psycopg2.OperationalError as e:
        log.error(f"No se pudo conectar a PostgreSQL: {e}")
        log.error("Verifica las variables PG_* en tu archivo .env")
    except Exception as e:
        log.error(f"Error inesperado en el framework: {e}", exc_info=True)
    finally:
        if conn_pg:
            conn_pg.close()
            log.info("Conexión PostgreSQL cerrada.")
        if mongo_client:
            mongo_client.close()
            log.info("Conexión MongoDB cerrada.")


if __name__ == "__main__":
    main()