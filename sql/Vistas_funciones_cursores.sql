


CREATE OR REPLACE VIEW v_libros_mas_prestados AS
SELECT
    l.titulo                   AS titulo_libro,
    a.nombre                   AS autor,
    COUNT(p.id_prestamo)       AS total_prestamos,
    STRING_AGG(u.nombre, ', ') AS usuarios
FROM "Prestamos"  p
JOIN "Libros"     l ON l.id_libro   = p.id_libro
JOIN "Usuarios"   u ON u.id_usuario = p.id_usuario
LEFT JOIN "Autores" a ON a.id_autor = l.id_autor
GROUP BY l.titulo, a.nombre
ORDER BY total_prestamos DESC;


-- Recibe id_prestamo, retorna monto de multa en COP
CREATE OR REPLACE FUNCTION fn_calcular_multa(p_id_prestamo INT)
RETURNS NUMERIC
LANGUAGE plpgsql AS $$
DECLARE
    v_dias   INT     := 0;
    v_multa  NUMERIC := 0;
    tarifa   CONSTANT NUMERIC := 500;  
    rec      RECORD;
BEGIN
    SELECT fecha_devolucion_esperada, estado
    INTO rec
    FROM "Prestamos"
    WHERE id_prestamo = p_id_prestamo;

    IF NOT FOUND THEN
        RETURN 0;
    END IF;

    IF rec.estado = 'activo' AND rec.fecha_devolucion_esperada < CURRENT_DATE THEN
        v_dias  := CURRENT_DATE - rec.fecha_devolucion_esperada;
        v_multa := v_dias * tarifa;

        UPDATE "Prestamos"
        SET multa = v_multa
        WHERE id_prestamo = p_id_prestamo;
    END IF;

    RETURN v_multa;
END;
$$;


CREATE OR REPLACE PROCEDURE sp_generar_log_auditoria()
LANGUAGE plpgsql AS $$
DECLARE
    cur_p CURSOR FOR
        SELECT
            p.id_prestamo,
            p.id_usuario,
            l.titulo,
            p.estado,
            GREATEST(CURRENT_DATE - p.fecha_devolucion_esperada, 0) AS dias_retraso
        FROM "Prestamos" p
        JOIN "Libros"    l ON l.id_libro = p.id_libro
        WHERE p.estado IN ('activo', 'vencido');
    rec RECORD;
BEGIN
    OPEN cur_p;
    LOOP
        FETCH cur_p INTO rec;
        EXIT WHEN NOT FOUND;

        INSERT INTO "Log_Auditoria"
            (id_prestamo, id_usuario, titulo_libro, estado, dias_retraso)
        VALUES
            (rec.id_prestamo, rec.id_usuario, rec.titulo, rec.estado, rec.dias_retraso);
    END LOOP;
    CLOSE cur_p;
    RAISE NOTICE 'Auditoria completada.';
END;
$$;