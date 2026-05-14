# Framework de Calidad, Automatización y Migración de Datos — Biblioteca Universidad

Este proyecto implementa un framework completo para la migración de datos desde un esquema de base de datos legacy (sin normalizar) hacia un esquema normalizado en PostgreSQL y posteriormente a MongoDB. Incluye validación de calidad de datos, automatización de procesos y objetos SQL avanzados.

## Estructura del Proyecto

```
Trabajo Migración/
├── main.py                          # Orquestador principal que ejecuta las 4 fases del proceso
├── diagnostico.py                   # Script de verificación previa para asegurar que todo esté configurado correctamente
├── requirements.txt                 # Dependencias Python necesarias
├── README.md                        # Este archivo de documentación
├── .env                             # Variables de entorno (NO subir a Git - contiene credenciales)
├── .gitignore                       # Archivos ignorados por Git
├── config/
│   ├── Config_calidad.json          # Reglas de validación de calidad de datos para tablas legacy
│   └── Mapping_mongo.json           # Configuración de mapeo PostgreSQL → MongoDB con embeddings
├── sql/
│   ├── Schema_legacy.sql            # Creación de tablas sin normalizar (violaciones 1FN/2FN/3FN)
│   ├── Schema_normalizado.sql       # Esquema normalizado en 3FN con claves foráneas
│   ├── Stored_procedures.sql        # Procedimientos almacenados CRUD para todas las entidades
│   └── Vistas_funciones_cursores.sql # Vista, función de multa y procedimiento con cursor para auditoría
└── logs/
    ├── Reporte_calidad.log          # Log detallado generado durante la ejecución
    ├── reporte_validacion.json      # Reporte JSON con errores de validación por tabla
    └── resumen_migracion.json       # Resumen de la migración a MongoDB
```

## Descripción de Carpetas y Archivos

### Raíz del Proyecto
- **`main.py`**: Script principal que orquesta todo el proceso de migración en 4 fases secuenciales.
- **`diagnostico.py`**: Utilidad para verificar dependencias, conexiones y archivos antes de ejecutar `main.py`.
- **`requirements.txt`**: Lista de paquetes Python requeridos (psycopg2-binary, pymongo, faker, python-dotenv).
- **`.env`**: Archivo de configuración con variables de entorno para conexiones a PostgreSQL y MongoDB.

### Carpeta `config/`
Contiene archivos de configuración JSON que definen reglas de negocio y mapeos:
- **`Config_calidad.json`**: Define reglas de validación para detectar violaciones de normalización, tipos de datos incorrectos, campos requeridos, etc. en las tablas legacy.
- **`Mapping_mongo.json`**: Especifica cómo mapear las tablas PostgreSQL normalizadas a colecciones MongoDB, incluyendo embeddings de datos relacionados y índices.

### Carpeta `sql/`
Scripts SQL que implementan los esquemas de base de datos y objetos avanzados:
- **`Schema_legacy.sql`**: Crea tablas sin normalizar con violaciones intencionales de 1FN (campos combinados), tipos de datos incorrectos y falta de claves primarias/foráneas.
- **`Schema_normalizado.sql`**: Implementa el esquema en 3FN con 4 tablas principales (Autores, Libros, Usuarios, Prestamos) y una tabla de auditoría, todas con restricciones apropiadas.
- **`Stored_procedures.sql`**: Define procedimientos almacenados para operaciones CRUD en todas las entidades normalizadas.
- **`Vistas_funciones_cursores.sql`**: Contiene una vista para libros más prestados, una función para calcular multas por retraso, y un procedimiento que usa cursores para generar logs de auditoría.

### Carpeta `logs/`
Archivos generados durante la ejecución (se crean automáticamente):
- **`Reporte_calidad.log`**: Log completo con timestamps de todas las operaciones.
- **`reporte_validacion.json`**: Detalle de errores de calidad encontrados en las tablas legacy.
- **`resumen_migracion.json`**: Estadísticas de la migración a MongoDB por colección.

## Flujo Específico del Programa

El programa ejecuta 4 fases secuenciales automatizadas:

### Fase 0: Preparación de Schema Legacy
- Elimina y recrea las tablas legacy con diseño intencionalmente deficiente.
- Prepara el punto de partida con violaciones de normalización.

### Fase A: Poblado Masivo de Datos Legacy
- Inserta 250 registros sintéticos en las 4 tablas legacy usando la biblioteca Faker.
- Genera datos "sucios" que violan las reglas de calidad definidas.

### Fase B: Validación de Calidad de Datos
- Aplica las reglas de `Config_calidad.json` a cada registro de las tablas legacy.
- Detecta violaciones de 1FN, tipos de datos incorrectos, campos requeridos faltantes, etc.
- Genera reporte detallado en `reporte_validacion.json` con porcentajes de calidad.

### Fase C: Normalización y Objetos SQL
- Crea el esquema normalizado en 3FN con claves foráneas.
- Implementa stored procedures para CRUD completo.
- Crea vista para análisis de libros más prestados.
- Implementa función para cálculo automático de multas por retraso.
- Crea procedimiento con cursor para auditoría de préstamos vencidos.
- Puebla las tablas normalizadas con 100 registros limpios (20 autores, 50 libros, 40 usuarios, 100 préstamos).

### Fase D: Migración a MongoDB
- Lee las tablas PostgreSQL normalizadas.
- Aplica el mapeo definido en `Mapping_mongo.json`.
- Realiza embeddings de datos relacionados (autor en libro, snapshots en préstamos).
- Migra a 4 colecciones MongoDB: books, users, loans, authors.
- Crea índices apropiados en MongoDB.
- Genera resumen de migración.

## Stored Procedures Explicados

Los procedimientos almacenados implementan operaciones CRUD para cada entidad del esquema normalizado:

### Autores
- **`sp_insertar_autor`**: Inserta un nuevo autor con nombre, nacionalidad y fecha de nacimiento.
- **`sp_actualizar_autor`**: Actualiza nombre y nacionalidad de un autor existente.
- **`sp_eliminar_autor`**: Elimina un autor por ID.

### Libros
- **`sp_insertar_libro`**: Inserta un libro con todos sus campos, incluyendo referencia al autor.
- **`sp_actualizar_libro`**: Actualiza título, editorial y categoría de un libro.
- **`sp_eliminar_libro`**: Elimina un libro por ID.

### Usuarios
- **`sp_insertar_usuario`**: Inserta usuario con nombre, correo y teléfono (evita duplicados por correo).
- **`sp_actualizar_usuario`**: Actualiza nombre y teléfono.
- **`sp_eliminar_usuario`**: Elimina usuario por ID.

### Préstamos
- **`sp_insertar_prestamo`**: Crea un préstamo activo con fechas calculadas automáticamente.
- **`sp_devolver_prestamo`**: Marca un préstamo como devuelto con fecha actual.

## Instalación y Configuración

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**:
   Crear archivo `.env` con:
   ```
   PG_HOST=localhost
   PG_PORT=5432
   PG_DATABASE=biblioteca_db
   PG_USER=postgres
   PG_PASSWORD=tu_password

   MONGO_URI=mongodb://localhost:27017
   MONGO_DATABASE=biblioteca_mongo
   ```

3. **Verificar configuración**:
   ```bash
   python diagnostico.py
   ```

## Ejecución

Ejecutar el proceso completo:
```bash
python main.py
```

El programa generará logs en tiempo real y archivos de reporte en la carpeta `logs/`.

## Tecnologías Utilizadas

- **Python**: Lenguaje principal para automatización
- **PostgreSQL**: Base de datos relacional para esquemas legacy y normalizado
- **MongoDB**: Base de datos NoSQL para migración final
- **psycopg2**: Conector PostgreSQL
- **pymongo**: Driver MongoDB
- **Faker**: Generación de datos sintéticos
- **PL/pgSQL**: Lenguaje para procedimientos, funciones y cursores en PostgreSQL

## Propósito Educativo

Este proyecto está diseñado como taller práctico para demostrar:
- Problemas de calidad en datos no normalizados
- Técnicas de normalización de bases de datos
- Implementación de objetos SQL avanzados
- Migración relacional → NoSQL con embeddings
- Automatización de procesos ETL con Python