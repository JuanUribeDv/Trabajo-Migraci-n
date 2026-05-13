# Framework de Calidad — Biblioteca Universidad

## Estructura del proyecto

```
Trabajo-Migracion/
├── main.py                          # Orquestador principal
├── requirements.txt
├── .env                             # Variables de entorno (NO subir a Git)
├── .gitignore
├── config/
│   ├── config_calidad.json          # Reglas de validación QA
│   └── mapping_mongo.json           # Mapeo PostgreSQL → MongoDB
├── sql/
│   ├── Schema_legacy.sql            # Tablas sin normalizar (punto de partida)
│   ├── Schema_normalizado.sql       # 4 tablas en 3FN con FK
│   ├── Stored_procedures.sql        # CRUD: insertar_libro, actualizar_libro, eliminar_libro
│   └── Vistas_funciones_cursores.sql
└── logs/
    ├── Reporte_calidad.log          # Log generado en tiempo de ejecución
    ├── reporte_validacion.json      # Detalle de errores por tabla
    └── resumen_migracion.json       # Resultado de la migración a MongoDB
```

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Edita `.env` con tus credenciales reales de PostgreSQL y MongoDB.

## Ejecución

```bash
python main.py
```

El orquestador ejecuta las 4 fases en orden:
- **Fase A**: Pobla las tablas legacy con 250 registros usando Faker
- **Fase B**: Valida calidad contra `config_calidad.json` y genera logs de error
- **Fase C**: Aplica schema normalizado y ejecuta objetos SQL (SPs, vistas, funciones, cursores)
- **Fase D**: Migra datos de PostgreSQL a MongoDB usando `mapping_mongo.json`

## Fases del taller

| Fase | Descripción | Archivo principal |
|------|-------------|-------------------|
| A — QA | Normalización 1FN/2FN/3FN | `sql/Schema_normalizado.sql` |
| B — SQL | Stored Procedures, Vistas, Funciones, Cursores | `sql/Stored_procedures.sql`, `sql/Vistas_funciones_cursores.sql` |
| C — Python | Automatización y validación | `main.py` (fases A, B, C) |
| D — MongoDB | Migración NoSQL | `main.py` (fase D) + `config/mapping_mongo.json` |