from .engine import DatabaseEngine

# ─────────────────────────────────────────────────────────────
# Comandos especiales disponibles en el REPL
# (no son SQL — son comandos propios del sistema)
# ─────────────────────────────────────────────────────────────
HELP_TEXT = """
Comandos disponibles:
  SQL estándar:
    CREATE TABLE nombre (col tipo, ...)
    INSERT INTO nombre VALUES (val1, val2, ...)
    SELECT * FROM nombre [WHERE campo = valor]
    UPDATE nombre SET campo = valor WHERE campo = valor
    DELETE FROM nombre WHERE campo = valor
    DROP TABLE nombre

  Comandos especiales:
    .tables       → lista las tablas existentes
    .clear        → limpiar la pantalla (no borra datos)
    .help         → mostrar esta ayuda
    exit / quit   → salir del motor
"""

def format_result(result):
    """
    Formatea el resultado de una consulta para mostrarlo al usuario.
    - Listas de registros → una fila por línea
    - Mensajes de texto   → se muestran directamente
    - Lista vacía         → mensaje indicativo
    """
    if isinstance(result, list):
        if len(result) == 0:
            return "(sin resultados)"
        return '\n'.join(str(row) for row in result)
    return str(result)

def handle_special(command, db):
    """
    Maneja los comandos especiales del REPL (empiezan con punto).
    Retorna True si fue un comando especial, False si no.
    """
    cmd = command.strip().lower()

    if cmd == '.tables':
        if db.tables:
            print("Tablas existentes:")
            for name in db.tables:
                count = len(db.execute(f"SELECT * FROM {name}"))
                print(f"  {name}  ({count} registros)")
        else:
            print("  (no hay tablas creadas)")
        return True

    if cmd == '.help':
        print(HELP_TEXT)
        return True

    if cmd == '.clear':
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        return True

    return False  # no era un comando especial

def main():
    """
    Bucle principal del REPL.
    Crea un engine y entra en el bucle Read-Eval-Print.
    """
    db = DatabaseEngine()
    print("=" * 50)
    print("  Mini Motor SQL con Árbol B+")
    print("  Escribe .help para ver los comandos")
    print("  Escribe exit para salir")
    print("=" * 50)

    while True:
        try:
            # READ: leer la entrada del usuario
            sql = input("\nsql> ").strip()

            # ignorar líneas vacías
            if not sql:
                continue

            # salir del bucle
            if sql.lower() in ('exit', 'quit'):
                print("Hasta luego.")
                break

            # manejar comandos especiales (.tables, .help, etc.)
            if sql.startswith('.'):
                handle_special(sql, db)
                continue

            # EVAL: ejecutar la consulta SQL
            result = db.execute(sql)

            # PRINT: mostrar el resultado formateado
            print(format_result(result))

        except KeyboardInterrupt:
            # Ctrl+C no debe crashear el programa, solo salir limpiamente
            print("\nSaliendo...")
            break

if __name__ == '__main__':
    main()