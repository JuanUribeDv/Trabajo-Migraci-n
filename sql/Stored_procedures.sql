

-- ── AUTORES ──────────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE sp_insertar_autor(
    p_nombre           VARCHAR,
    p_nacionalidad     VARCHAR DEFAULT NULL,
    p_fecha_nacimiento DATE    DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "Autores" (nombre, nacionalidad, fecha_nacimiento)
    VALUES (p_nombre, p_nacionalidad, p_fecha_nacimiento);
END;
$$;

CREATE OR REPLACE PROCEDURE sp_actualizar_autor(
    p_id   INT,
    p_nombre       VARCHAR,
    p_nacionalidad VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE "Autores" SET nombre = p_nombre, nacionalidad = p_nacionalidad
    WHERE id_autor = p_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_eliminar_autor(p_id INT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM "Autores" WHERE id_autor = p_id;
END;
$$;

-- ── LIBROS ───────────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE sp_insertar_libro(
    p_titulo            VARCHAR,
    p_isbn              VARCHAR DEFAULT NULL,
    p_anio_publicacion  INT     DEFAULT NULL,
    p_editorial         VARCHAR DEFAULT NULL,
    p_categoria         VARCHAR DEFAULT NULL,
    p_descripcion       VARCHAR DEFAULT NULL,
    p_id_autor          INT     DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "Libros" (titulo, isbn, anio_publicacion, editorial, categoria, descripcion, id_autor)
    VALUES (p_titulo, p_isbn, p_anio_publicacion, p_editorial, p_categoria, p_descripcion, p_id_autor);
END;
$$;

CREATE OR REPLACE PROCEDURE sp_actualizar_libro(
    p_id        INT,
    p_titulo    VARCHAR,
    p_editorial VARCHAR DEFAULT NULL,
    p_categoria VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE "Libros"
    SET titulo = p_titulo, editorial = p_editorial, categoria = p_categoria
    WHERE id_libro = p_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_eliminar_libro(p_id INT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM "Libros" WHERE id_libro = p_id;
END;
$$;

-- ── USUARIOS ─────────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE sp_insertar_usuario(
    p_nombre   VARCHAR,
    p_correo   VARCHAR,
    p_telefono VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "Usuarios" (nombre, correo, telefono)
    VALUES (p_nombre, p_correo, p_telefono)
    ON CONFLICT (correo) DO NOTHING;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_actualizar_usuario(
    p_id       INT,
    p_nombre   VARCHAR,
    p_telefono VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE "Usuarios" SET nombre = p_nombre, telefono = p_telefono
    WHERE id_usuario = p_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_eliminar_usuario(p_id INT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM "Usuarios" WHERE id_usuario = p_id;
END;
$$;

-- ── PRESTAMOS ────────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE sp_insertar_prestamo(
    p_id_usuario INT,
    p_id_libro   INT,
    p_dias_prestamo INT DEFAULT 15
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "Prestamos" (id_usuario, id_libro, fecha_salida, fecha_devolucion_esperada, estado)
    VALUES (p_id_usuario, p_id_libro, CURRENT_DATE, CURRENT_DATE + p_dias_prestamo, 'activo');
END;
$$;

CREATE OR REPLACE PROCEDURE sp_devolver_prestamo(p_id_prestamo INT)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE "Prestamos"
    SET estado = 'devuelto', fecha_devolucion_real = CURRENT_DATE
    WHERE id_prestamo = p_id_prestamo;
END;
$$;