# Paquete de configuración del proyecto SGIL.
#
# Django busca el driver "MySQLdb" (mysqlclient) para conectarse a MySQL, pero
# ese driver hay que compilarlo y suele fallar en Windows. PyMySQL está escrito
# solo en Python: con install_as_MySQLdb() se "hace pasar" por MySQLdb y Django
# lo usa sin darse cuenta.
import pymysql

pymysql.install_as_MySQLdb()
