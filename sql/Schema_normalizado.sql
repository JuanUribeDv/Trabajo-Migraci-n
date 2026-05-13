-- Querys normalizadas


CREATE TABLE Autores (
    id_autor    SERIAL PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL,
    nacionalidad VARCHAR(100)
);
 
CREATE TABLE Libros (
    id_libro        SERIAL PRIMARY KEY,
    titulo          VARCHAR(255) NOT NULL,
    id_autor        INT NOT NULL REFERENCES Autores(id_autor),
    categoria       VARCHAR(100),         -- antes era "categoria_y_descripcion" combinado
    descripcion     TEXT,
    editorial       VARCHAR(255),
    fecha_publicacion DATE,               -- antes era VARCHAR(50), tipo correcto ahora
    isbn            VARCHAR(20) UNIQUE
);
 
CREATE TABLE Sedes (
    id_sede     SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    ubicacion   VARCHAR(255)
);
 
CREATE TABLE Inventario (
    id_inventario   SERIAL PRIMARY KEY,
    id_libro        INT NOT NULL REFERENCES Libros(id_libro),
    id_sede         INT NOT NULL REFERENCES Sedes(id_sede),
    cantidad_total  INT DEFAULT 0 CHECK (cantidad_total >= 0)
);

CREATE TABLE Usuarios (
    id_usuario  SERIAL PRIMARY KEY,
    nombre      VARCHAR(255) NOT NULL,
    correo      VARCHAR(255) UNIQUE NOT NULL CHECK (correo LIKE '%@%'),
    telefono    VARCHAR(20)
);

CREATE TABLE Prestamos (
    id_prestamo     SERIAL PRIMARY KEY,
    id_usuario      INT NOT NULL REFERENCES Usuarios(id_usuario),
    id_libro        INT NOT NULL REFERENCES Libros(id_libro),
    fecha_salida    DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_devolucion DATE,
    estado          VARCHAR(20) DEFAULT 'activo' CHECK (estado IN ('activo','devuelto','vencido'))
);
CREATE TABLE Reseñas (
    id_reseña      SERIAL PRIMARY KEY,
    id_usuario      INT NOT NULL REFERENCES Usuarios(id_usuario),
    id_libro        INT NOT NULL REFERENCES Libros(id_libro),
    comentario      TEXT,
    calificacion    NUMERIC(2,1) CHECK (calificacion BETWEEN 1 AND 5)
);
CREATE TABLE Log_Auditoria (
    id_log          SERIAL PRIMARY KEY,
    id_prestamo     INT REFERENCES Prestamos(id_prestamo),
    fecha_registro  TIMESTAMP DEFAULT NOW(),
    mensaje         TEXT
);