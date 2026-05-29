import json
import os
from pathlib import Path
class Catalog:
    """
    Catálogo del sistema (system catalog).

    Guarda metadatos sobre las tablas registradas en el motor:
      - nombre de la tabla
      - columnas con sus tipos (en el orden en que fueron declaradas)

    El catálogo NO almacena datos; solo describe la estructura.
    El motor (DatabaseEngine) es quien notifica al catálogo cuando
    se crea o elimina una tabla.

    Uso típico:
        catalog = Catalog()
        catalog.register_table('usuarios', [{'name': 'id', 'type': 'int'}])
        print(catalog.describe('usuarios'))
        catalog.drop_table('usuarios')
    """

    def __init__(self, path: str = "data/catalog.json"):
        # Diccionario: nombre_tabla (str) → lista de (nombre_col, tipo_col)
        self.path = Path(path)
        self._tables: dict[str, list[dict]] = {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")  # inicia con catálogo vacío
        self.load()


    
    def load(self) -> None:
     
     """Carga el catálogo desde disco al iniciar el motor.
     Si el archivo no existe, el catálogo arranca vacío."""

     if not os.path.exists(self.path):
        return  
     with open(self.path, 'r', encoding='utf-8') as f:
          self._tables = json.load(f)

    def save(self) -> None:
        with open(self.path, 'w', encoding='utf-8') as f:
             json.dump(self._tables, f, indent=2)
        
    # ══════════════════════════════════════════════════════════
    # REGISTRO Y ELIMINACIÓN
    # ══════════════════════════════════════════════════════════

    def register_table(self, table_name, columns):
        """
        Registra una tabla nueva en el catálogo.

        Parameters
        ----------
        table_name : str
            Nombre de la tabla.
        columns : list[dict]
            Lista de dicts con claves 'name' y 'type', tal como
            los produce Parser.parse_column_defs().
            Ejemplo: [{'name': 'id', 'type': 'int'}, {'name': 'nombre', 'type': 'str'}]

        Raises
        ------
        ValueError
            Si la tabla ya estaba registrada.
        """
        print("TABLA:", table_name)
        if table_name in self._tables:
            raise ValueError(f"La tabla '{table_name}' ya existe en el catálogo.")
        self._tables[table_name] = columns
        self.save()  # guardar cambios inmediatamente

    def drop_table(self, table_name: str) -> None:
        """
        Elimina la entrada de una tabla del catálogo.

        Raises
        ------
        KeyError
            Si la tabla no existe en el catálogo.
        """
        if table_name not in self._tables:
            raise KeyError(f"La tabla '{table_name}' no existe en el catálogo.")
        del self._tables[table_name]
        self.save()  # guardar cambios inmediatamente

    # ══════════════════════════════════════════════════════════
    # CONSULTAS
    # ══════════════════════════════════════════════════════════

    def table_exists(self, table_name: str) -> bool:
        """Retorna True si la tabla está registrada en el catálogo."""
        return table_name in self._tables

    def get_columns(self, table_name: str) -> list:
        """
        Retorna la lista de columnas de una tabla como lista de tuplas
        (nombre, tipo).

        Raises
        ------
        KeyError
            Si la tabla no existe.
        """
        if table_name not in self._tables:
            raise KeyError(f"La tabla '{table_name}' no existe en el catálogo.")
        return list(self._tables[table_name])  # copia defensiva

    def list_tables(self) -> list:
        """Retorna los nombres de todas las tablas registradas (orden de creación)."""
        return list(self._tables.keys())

    # ══════════════════════════════════════════════════════════
    # PRESENTACIÓN
    # ══════════════════════════════════════════════════════════

    def describe(self, table_name: str) -> str:
        """
        Devuelve una descripción legible de la estructura de una tabla.

        Ejemplo de salida:
            Tabla: usuarios
            ┌─────────┬────────┐
            │ Columna │  Tipo  │
            ├─────────┼────────┤
            │ id      │ int    │
            │ nombre  │ str    │
            └─────────┴────────┘
        """
        columns = self.get_columns(table_name)  # lanza KeyError si no existe

        col_w  = max(len('Columna'), max(len(c['name']) for c in columns))
        type_w = max(len('Tipo'),    max(len(c['type']) for c in columns))

        sep_top = f"┌{'─' * (col_w + 2)}┬{'─' * (type_w + 2)}┐"
        sep_mid = f"├{'─' * (col_w + 2)}┼{'─' * (type_w + 2)}┤"
        sep_bot = f"└{'─' * (col_w + 2)}┴{'─' * (type_w + 2)}┘"

        header = f"│ {'Columna':<{col_w}} │ {'Tipo':<{type_w}} │"
        rows   = [f"│ {c['name']:<{col_w}} │ {c['type']:<{type_w}} │" for c in columns]

        lines = [
            f"Tabla: {table_name}",
            sep_top,
            header,
            sep_mid,
            *rows,
            sep_bot,
        ]
        return '\n'.join(lines)

    def show_tables(self) -> str:
        """
        Devuelve una lista legible de todas las tablas registradas.

        Ejemplo de salida:
            Tablas registradas (2):
              • usuarios  (id, nombre)
              • productos  (codigo, descripcion, precio)
        """
        if not self._tables:
            return "No hay tablas registradas en el catálogo."

        lines = [f"Tablas registradas ({len(self._tables)}):"]
        for name, cols in self._tables.items():
            col_names = ', '.join(c['name'] for c in cols)
            lines.append(f"  • {name}  ({col_names})")
        return '\n'.join(lines)
