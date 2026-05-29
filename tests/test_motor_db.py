# tests/test_motor_db.py
import os
import pytest
from parsing.engine import DatabaseEngine


# ══════════════════════════════════════════════════════════
# FIXTURE — crea un engine limpio para cada test
# ══════════════════════════════════════════════════════════

@pytest.fixture
def engine(tmp_path, monkeypatch):
    """
    Crea un DatabaseEngine con una carpeta data/ temporal.
    Se elimina automáticamente al terminar cada test.
    """
    # redirigir la carpeta data/ a un directorio temporal
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    return DatabaseEngine()


# ══════════════════════════════════════════════════════════
# CREATE TABLE
# ══════════════════════════════════════════════════════════

def test_create_table(engine):
    result = engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    assert "creada" in result

def test_create_table_duplicada(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    result = engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    assert "Error" in result

def test_create_crea_archivo_db(engine, tmp_path):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    assert os.path.exists(tmp_path / "data" / "usuarios.db")

def test_create_crea_catalog_json(engine, tmp_path):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    assert os.path.exists(tmp_path / "data" / "catalog.json")


# ══════════════════════════════════════════════════════════
# INSERT
# ══════════════════════════════════════════════════════════

def test_insert_basico(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    result = engine.execute("INSERT INTO usuarios VALUES (1, 'Ana')")
    assert "insertado" in result

def test_insert_tabla_inexistente(engine):
    result = engine.execute("INSERT INTO fantasma VALUES (1, 'Ana')")
    assert "Error" in result

def test_insert_multiples(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    for i in range(10):
        engine.execute(f"INSERT INTO usuarios VALUES ({i}, 'user{i}')")
    result = engine.execute("SELECT * FROM usuarios")
    assert len(result) == 10


# ══════════════════════════════════════════════════════════
# SELECT
# ══════════════════════════════════════════════════════════

def test_select_todos(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    engine.execute("INSERT INTO usuarios VALUES (1, 'Ana')")
    engine.execute("INSERT INTO usuarios VALUES (2, 'Luis')")
    result = engine.execute("SELECT * FROM usuarios")
    assert len(result) == 2

def test_select_where(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    engine.execute("INSERT INTO usuarios VALUES (1, 'Ana')")
    engine.execute("INSERT INTO usuarios VALUES (2, 'Luis')")
    result = engine.execute("SELECT * FROM usuarios WHERE id = 1")
    assert result == [[1, 'Ana']]

def test_select_where_inexistente(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    result = engine.execute("SELECT * FROM usuarios WHERE id = 99")
    assert result == []

def test_select_tabla_vacia(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    result = engine.execute("SELECT * FROM usuarios")
    assert result == []


# ══════════════════════════════════════════════════════════
# DELETE
# ══════════════════════════════════════════════════════════

def test_delete_basico(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    engine.execute("INSERT INTO usuarios VALUES (1, 'Ana')")
    engine.execute("DELETE FROM usuarios WHERE id = 1")
    result = engine.execute("SELECT * FROM usuarios WHERE id = 1")
    assert result == []

def test_delete_inexistente(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    result = engine.execute("DELETE FROM usuarios WHERE id = 99")
    assert "eliminado" in result  # no debe explotar

def test_delete_no_afecta_otros(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    engine.execute("INSERT INTO usuarios VALUES (1, 'Ana')")
    engine.execute("INSERT INTO usuarios VALUES (2, 'Luis')")
    engine.execute("DELETE FROM usuarios WHERE id = 1")
    result = engine.execute("SELECT * FROM usuarios WHERE id = 2")
    assert result == [[2, 'Luis']]


# ══════════════════════════════════════════════════════════
# DROP TABLE
# ══════════════════════════════════════════════════════════

def test_drop_table(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    result = engine.execute("DROP TABLE usuarios")
    assert "eliminada" in result

def test_drop_tabla_inexistente(engine):
    result = engine.execute("DROP TABLE fantasma")
    assert "Error" in result


# ══════════════════════════════════════════════════════════
# PERSISTENCIA — reinicio del motor
# ══════════════════════════════════════════════════════════

def test_persistencia_datos(tmp_path, monkeypatch):
    """
    Verifica que los datos sobreviven al reiniciar el motor.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    # sesión 1 — insertar datos
    engine1 = DatabaseEngine()
    engine1.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    engine1.execute("INSERT INTO usuarios VALUES (1, 'Ana')")
    engine1.execute("INSERT INTO usuarios VALUES (2, 'Luis')")

    # sesión 2 — nuevo motor, mismos datos
    engine2 = DatabaseEngine()
    result = engine2.execute("SELECT * FROM usuarios")
    assert len(result) == 2

def test_persistencia_catalogo(tmp_path, monkeypatch):
    """
    Verifica que el catálogo sobrevive al reiniciar el motor.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()

    engine1 = DatabaseEngine()
    engine1.execute("CREATE TABLE productos (id INT, precio FLOAT)")

    engine2 = DatabaseEngine()
    assert engine2.catalog.table_exists("productos")

def test_insert_tipo_invalido(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    result = engine.execute("INSERT INTO usuarios VALUES ('hola', 'Ana')")
    assert "Error" in result

def test_insert_tipo_valido(engine):
    engine.execute("CREATE TABLE usuarios (id INT, nombre STR)")
    result = engine.execute("INSERT INTO usuarios VALUES (1, 'Ana')")
    assert "insertado" in result