-- =====================================================================
-- crear_bd.sql — Crea la base de datos y el usuario de MySQL del SGIL.
--
-- Cómo usarlo: abrir MySQL Workbench, conectarse como root, abrir este
-- archivo y ejecutarlo con el rayo (⚡). Sirve también para dejar la base
-- limpia antes de la demo (borra todo y la crea de nuevo).
-- Después de ejecutarlo: python manage.py migrate
-- =====================================================================

-- Borra la base si existía, para partir siempre desde cero.
DROP DATABASE IF EXISTS sgil_db;

-- utf8mb4 permite guardar tildes, ñ y cualquier carácter sin problemas.
CREATE DATABASE sgil_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usuario que usa Django (ver DATABASES en sgil/settings.py).
-- La contraseña es simple porque es solo la base local de cada integrante.
CREATE USER IF NOT EXISTS 'sgil'@'localhost' IDENTIFIED BY 'sgil123';
GRANT ALL PRIVILEGES ON sgil_db.* TO 'sgil'@'localhost';

-- Django crea la base test_sgil_db cuando se ejecutan los tests.
GRANT ALL PRIVILEGES ON test_sgil_db.* TO 'sgil'@'localhost';

FLUSH PRIVILEGES;
