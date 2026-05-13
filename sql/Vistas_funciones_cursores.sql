CREATE OR REPLACE FUNCTION calcular_multa(p_prestamo_id INT)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
    dias_retraso INT;
    multa NUMERIC;
BEGIN
    SELECT GREATEST((CURRENT_DATE - fecha_devolucion),0)
    INTO dias_retraso
    FROM Prestamos
    WHERE prestamo_id = p_prestamo_id;

    multa := dias_retraso * 1000; -- $1000 por día de retraso
    RETURN multa;
END;
$$;


CREATE OR REPLACE FUNCTION auditar_prestamos_activos()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    cur CURSOR FOR
        SELECT prestamo_id, usuario_id, libro_id
        FROM Prestamos
        WHERE estado = 'Activo';
    fila RECORD;
BEGIN
    OPEN cur;
    LOOP
        FETCH cur INTO fila;
        EXIT WHEN NOT FOUND;
        INSERT INTO Auditoria(prestamo_id, mensaje)
        VALUES (fila.prestamo_id, 'Préstamo activo auditado');
    END LOOP;
    CLOSE cur;
END;
$$;