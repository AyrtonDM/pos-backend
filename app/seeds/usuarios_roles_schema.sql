CREATE TABLE IF NOT EXISTS persona (
    id_persona SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    genero VARCHAR(20) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    documento VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS rol (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario SERIAL PRIMARY KEY,
    id_persona INT NOT NULL UNIQUE,
    fecha_creacion DATE NOT NULL DEFAULT CURRENT_DATE,
    email VARCHAR(255) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_usuario_persona
        FOREIGN KEY (id_persona)
        REFERENCES persona(id_persona)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS usuario_rol (
    id_usuario_rol SERIAL PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_rol INT NOT NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_usuario_rol_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_usuario_rol_rol
        FOREIGN KEY (id_rol)
        REFERENCES rol(id_rol)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT uq_usuario_rol UNIQUE (id_usuario, id_rol)
);
