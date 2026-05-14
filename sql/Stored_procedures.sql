
CREATE OR REPLACE PROCEDURE sp_insertar_libro(
    p_titulo        VARCHAR,
    p_id_autor      INT,
    p_categoria     VARCHAR,
    p_descripcion   TEXT,
    p_editorial     VARCHAR,
    p_fecha         DATE
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO Libros (titulo, id_autor, categoria, descripcion, editorial, fecha_publicacion)
    VALUES (p_titulo, p_id_autor, p_categoria, p_descripcion, p_editorial, p_fecha);
END;
$$;


CREATE OR REPLACE PROCEDURE sp_actualizar_libro(
    p_id_libro  INT,
    p_titulo    VARCHAR,
    p_editorial VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Libros
    SET titulo = p_titulo, editorial = p_editorial
    WHERE id_libro = p_id_libro;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Libro con id % no encontrado', p_id_libro;
    END IF;
END;
$$;


CREATE OR REPLACE PROCEDURE sp_eliminar_libro(p_id_libro INT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM Libros WHERE id_libro = p_id_libro;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Libro con id % no encontrado', p_id_libro;
    END IF;
END;
$$;
