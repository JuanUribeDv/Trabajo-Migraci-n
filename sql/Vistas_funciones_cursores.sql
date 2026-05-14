-- ============================================================
-- VISTAS, FUNCIONES Y CURSORES
-- ============================================================

-- ── VISTA: libros más prestados con nombre de usuario ────────
CREATE OR REPLACE VIEW libros_mas_prestados AS
SELECT
    l.titulo                        AS titulo_libro,
    a.nombre                        AS autor,
    COUNT(p.id_prestamo)            AS total_prestamos,
    STRING_AGG(u.nombre, ', ')      AS usuarios
FROM "Prestamos"  p
JOIN "Libros"     l ON l.id_libro   = p.id_libro
JOIN "Usuarios"   u ON u.id_usuario = p.id_usuario
LEFT JOIN "Autores" a ON a.id_autor = l.id_autor
GROUP BY l.titulo, a.nombre
ORDER BY total_prestamos DESC;

-- ── FUNCIÓN: calcular multa por retraso ──────────────────────
-- Cobra $500 COP por día de retraso sobre préstamos activos vencidos
CREATE OR REPLACE FUNCTION calcular_multa(p_id_usuario INT)
RETURNS NUMERIC
LANGUAGE plpgsql AS $$
DECLARE
    v_multa      NUMERIC := 0;
    v_dias       INT;
    rec          RECORD;
    tarifa_dia   CONSTANT NUMERIC := 500;   -- $500 COP por día
BEGIN
    FOR rec IN
        SELECT id_prestamo, fecha_devolucion_esperada
        FROM "Prestamos"
        WHERE id_usuario = p_id_usuario
          AND estado     = 'activo'
          AND fecha_devolucion_esperada < CURRENT_DATE
    LOOP
        v_dias  := CURRENT_DATE - rec.fecha_devolucion_esperada;
        v_multa := v_multa + (v_dias * tarifa_dia);

        -- Actualizar multa en la tabla
        UPDATE "Prestamos"
        SET multa = (v_dias * tarifa_dia)
        WHERE id_prestamo = rec.id_prestamo;
    END LOOP;

    RETURN v_multa;
END;
$$;

-- ── PROCEDIMIENTO CON CURSOR: auditoría de préstamos activos ─
CREATE OR REPLACE PROCEDURE ejecutar_auditoria_prestamos()
LANGUAGE plpgsql AS $$
DECLARE
    cur_prestamos CURSOR FOR
        SELECT
            p.id_prestamo,
            p.id_usuario,
            l.titulo,
            p.estado,
            CURRENT_DATE - p.fecha_devolucion_esperada AS dias_retraso
        FROM "Prestamos" p
        JOIN "Libros"    l ON l.id_libro = p.id_libro
        WHERE p.estado = 'activo';

    rec RECORD;
BEGIN
    OPEN cur_prestamos;
    LOOP
        FETCH cur_prestamos INTO rec;
        EXIT WHEN NOT FOUND;

        -- Solo registrar si tiene retraso o está activo
        INSERT INTO "AuditoriaLog" (id_prestamo, id_usuario, titulo_libro, estado, dias_retraso)
        VALUES (
            rec.id_prestamo,
            rec.id_usuario,
            rec.titulo,
            rec.estado,
            GREATEST(rec.dias_retraso, 0)
        );
    END LOOP;
    CLOSE cur_prestamos;

    RAISE NOTICE 'Auditoría completada. Registros insertados en AuditoriaLog.';
END;
$$;