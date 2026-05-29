# Motor de base de datos usando arbol b+ #
## 1. Integrantes ##
Jefferson David Rico Ruiz 20242020108
Kevin Sebastian Correo Buritica 20241020075
Kevin Felipe Vargas Farfan 20242020259

## 2. Descripcion del proyecto ##
Este proyecto es motor de base de datos utilizando un arbol b+ para el proceso de insercion, consulta, eliminacion y actualizacion de registros garantizando una complejidad en las operaciones de O(log(n)). Las operaciones que soporta la base de datos son:
## 3. Operacion soportadas ##
1. Creacion de tablas con nombre, los nombres de las columnas y el tipo de dato que van albergar
2. Insercion de registros indicando a la tabla donde se quiere ingresar, el Id o la clave que se le va asignar y los valores asociados a cada tabla
3. Actualizacion de cualquiera de los campos de un registro, ingresando la tabla, el campo que se quiere actualizar y el id asociado al registro
4. Consultas a registros por el id donde se indica la tabla a buscar y el id del registro para ver sus datos
5. Consulta total a los registros encontrados en una tabla, indicando el nombre de la tabla
6. Eliminacion de registro indicando la tabla donde se quiere eliminar, ingresando el id asociado al registro
7. Eliminacion de tablas indicando el nombre de la tabla que se requiere eliminar

## 4. Instrucciones de ejecuccion ## 
Ejecutar los siguientes comandos en la terminal 
1. Clonar repositorio: ``git clone https://github.com/Jefferson3108/Motor_Base_De_Datos_Relacional``
2. Crear entorno: ``python -m venv .venv`` en windows, En macOS/Linux ``python3 -m ven .venv``
3. Activacion: ``.ven\Scripts\Activate`` en windows, En macOS/Linux ``source venv/bin/Activate`` 
4. Instalar dependencias: ``pip install -r requirements.txt``
5. Ejecuccion: en la terminal escribir ``python -m parsing.repl``
6. Ejecuccion pruebas unitarias ``pytest -v``

## 5. Ejemplos de comandos ##
1. Para crear una tabla

- ``CREATE TABLE estudiantes(Id int, nombre str, edad int)``

- ``CREATE TABLE materias(Id int, nombre str, creditos int, profesor str, activa bool)``  

2. Para insertar un registro 

- ``INSERT INTO estudiantes VALUES(1,Jaime,23)``

- ``INSERT INTO materias VALUES(1,matematicas,3,Walter,true)``

3. Para consultar una tabla entera

- ``SELECT * FROM estudiantes``

- ``SELECT * FROM materias``

4. Para consultar un registro por id 

- ``SELECT * FROM estudiantes WHERE id=1``

- ``SELECT * FROM materias WHERE id=1``

5. Para actualizar un registro por id

- ``UPDATE estudiantes set nombre= David WHERE id=1``

- ``UPDATE materias set creditos= 2 WHERE id=1``

6. Para eliminar un registro por id

- ``DELETE FROM estudiantes WHERE id=1``

- ``DELETE FROM materias WHERE id=1``

7. Para eliminar un tabla

- ``DROP TABLE estudiantes``

- ``DROP TABLE materias``

8. Comando para salir

- ``exit``




