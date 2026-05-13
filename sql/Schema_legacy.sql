-- Querys sin normalizar 

CREATE TABLE Biblioteca_Data ( 
    id_registro SERIAL PRIMARY KEY, 
    titulo_libro VARCHAR(255), 
    autor_nombre VARCHAR(255), 
    categoria_y_descripcion TEXT, -- Campo combinado (Viola 1FN) 
    editorial_info VARCHAR(255), 
    fecha_publicacion VARCHAR(50) -- Tipo de dato incorrecto 
); 
 
CREATE TABLE Prestamos_Crudos ( 
    id_prestamo INT, 
    nombre_usuario VARCHAR(255), 
    correo_usuario VARCHAR(255), 
    libros_prestados TEXT, -- Lista separada por comas (Viola 1FN) 
    fecha_salida DATE, 
    estado_prestamo VARCHAR(20) 
); 
 
CREATE TABLE Inventario_Sedes ( 
    sede_nombre VARCHAR(100), 
    ubicacion_sede VARCHAR(255), 
    libro_asociado VARCHAR(255), 
    cantidad_total INT 
); 
 
CREATE TABLE Reseñas_Usuarios ( 
    usuario_id INT, 
    libro_titulo VARCHAR(255), 
    comentario TEXT, 
    calificacion VARCHAR(10) -- Debería ser numérico 
);