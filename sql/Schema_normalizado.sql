

-- Limpiar versiones con y sin comillas (cubre corridas anteriores)
DROP TABLE IF EXISTS "Prestamos"    CASCADE;
DROP TABLE IF EXISTS "Libros"       CASCADE;
DROP TABLE IF EXISTS "Autores"      CASCADE;
DROP TABLE IF EXISTS "Usuarios"     CASCADE;
DROP TABLE IF EXISTS "AuditoriaLog" CASCADE;
DROP TABLE IF EXISTS prestamos      CASCADE;
DROP TABLE IF EXISTS libros         CASCADE;
DROP TABLE IF EXISTS autores        CASCADE;
DROP TABLE IF EXISTS usuarios       CASCADE;
DROP TABLE IF EXISTS auditorialog   CASCADE;
DROP TABLE IF EXISTS "Log_Auditoria" CASCADE;
DROP TABLE IF EXISTS log_auditoria  CASCADE;


CREATE TABLE "Autores" (
    id_autor         SERIAL PRIMARY KEY,
    nombre           VARCHAR(255) NOT NULL,
    nacionalidad     VARCHAR(100),
    fecha_nacimiento DATE
);


CREATE TABLE "Libros" (
    id_libro         SERIAL PRIMARY KEY,
    titulo           VARCHAR(255) NOT NULL,
    isbn             VARCHAR(20)  UNIQUE,
    anio_publicacion INT,
    editorial        VARCHAR(255),
    categoria        VARCHAR(100),
    descripcion      VARCHAR(500),
    id_autor         INT REFERENCES "Autores"(id_autor) ON DELETE SET NULL
);


CREATE TABLE "Usuarios" (
    id_usuario     SERIAL PRIMARY KEY,
    nombre         VARCHAR(255) NOT NULL,
    correo         VARCHAR(255) NOT NULL UNIQUE,
    telefono       VARCHAR(20),
    fecha_registro DATE DEFAULT CURRENT_DATE
);


CREATE TABLE "Prestamos" (
    id_prestamo               SERIAL PRIMARY KEY,
    id_usuario                INT NOT NULL REFERENCES "Usuarios"(id_usuario) ON DELETE CASCADE,
    id_libro                  INT NOT NULL REFERENCES "Libros"(id_libro)     ON DELETE CASCADE,
    fecha_salida              DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_devolucion_esperada DATE NOT NULL,
    fecha_devolucion_real     DATE,
    estado                    VARCHAR(20) NOT NULL DEFAULT 'activo'
                                  CHECK (estado IN ('activo','devuelto','vencido','renovado')),
    multa                     NUMERIC(10,2) DEFAULT 0
);


CREATE TABLE "Log_Auditoria" (
    id_auditoria SERIAL PRIMARY KEY,
    id_prestamo  INT,
    id_usuario   INT,
    titulo_libro VARCHAR(255),
    estado       VARCHAR(20),
    dias_retraso INT,
    fecha_log    TIMESTAMP DEFAULT NOW()
);