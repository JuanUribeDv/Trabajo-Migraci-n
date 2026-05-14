


DROP TABLE IF EXISTS "Reseñas_Usuarios"   CASCADE;
DROP TABLE IF EXISTS "Inventario_Sedes"   CASCADE;
DROP TABLE IF EXISTS "Prestamos_Crudos"   CASCADE;
DROP TABLE IF EXISTS "Biblioteca_Data"    CASCADE;


CREATE TABLE "Biblioteca_Data" (
    id_registro             SERIAL PRIMARY KEY,
    titulo_libro            VARCHAR(255),
    autor_nombre            VARCHAR(255),
    categoria_y_descripcion TEXT,           -- Campo combinado: viola 1FN
    editorial_info          VARCHAR(255),
    fecha_publicacion       VARCHAR(50)     -- Tipo incorrecto: debería ser DATE
);


CREATE TABLE "Prestamos_Crudos" (
    id_prestamo      INT,                   -- Sin PRIMARY KEY explícita
    nombre_usuario   VARCHAR(255),
    correo_usuario   VARCHAR(255),
    libros_prestados TEXT,                  -- Lista separada por comas: viola 1FN
    fecha_salida     DATE,
    estado_prestamo  VARCHAR(20)
);


CREATE TABLE "Inventario_Sedes" (
    sede_nombre     VARCHAR(100),
    ubicacion_sede  VARCHAR(255),
    libro_asociado  VARCHAR(255),           -- Redundante: debería ser FK a Libros
    cantidad_total  INT
);


CREATE TABLE "Reseñas_Usuarios" (
    usuario_id    INT,
    libro_titulo  VARCHAR(255),
    comentario    TEXT,
    calificacion  VARCHAR(10)              -- Debería ser INT o NUMERIC
);