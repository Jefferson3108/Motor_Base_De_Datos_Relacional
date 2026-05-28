from catalog.catalog import Catalog
from tree.BPlusTree import BPlusTree
from .lexer import Lexer
from .parser import Parser
from catalog.catalog import Catalog

class DatabaseEngine:
    """
    Motor de base de datos. Mantiene un conjunto de tablas en memoria,
    cada una indexada por un árbol B+.

    Flujo de una consulta:
      1. execute(sql)  → llama al Lexer y al Parser
      2. dispatch(ast) → decide qué operación ejecutar
      3. do_*(ast)     → ejecuta contra el árbol B+ correspondiente

    El catálogo (self.catalog) se mantiene sincronizado automáticamente:
      - do_create registra la tabla y sus columnas
      - do_drop   elimina la entrada del catálogo
    """

    def __init__(self):
        # Diccionario de tablas: nombre (str) → BPlusTree
        # Cada tabla es un árbol B+ independiente
        self.tables = {}
        # Catálogo del sistema: guarda metadatos (columnas y tipos)
        self.catalog = Catalog("data/catalog.json")
        # Al iniciar el motor, cargamos las tablas existentes del catálogo
        for table_name in self.catalog._tables:
            self.tables[table_name] = BPlusTree(order=4)

    # ══════════════════════════════════════════════════════════
    # PUNTO DE ENTRADA PRINCIPAL
    # ══════════════════════════════════════════════════════════

    def execute(self, sql: str):
        """
        Recibe una consulta SQL como texto y retorna el resultado.
        Maneja errores de sintaxis y de ejecución por separado para
        dar mensajes claros al usuario.
        """
        try:
            tokens = Lexer(sql).tokenize()
            ast    = Parser(tokens).parse()
            return self.dispatch(ast)
        except SyntaxError as e:
            return f"[Error de sintaxis] {e}"
        except Exception as e:
            return f"[Error de ejecución] {e}"

    def dispatch(self, ast):
        """
        Enruta el AST al método correcto según el tipo de operación.
        Actúa como un switch/case sobre ast.type.
        """
        if ast.type == 'CREATE': return self.do_create(ast)
        if ast.type == 'DROP':   return self.do_drop(ast)
        if ast.type == 'INSERT': return self.do_insert(ast)
        if ast.type == 'SELECT': return self.do_select(ast)
        if ast.type == 'UPDATE': return self.do_update(ast)
        if ast.type == 'DELETE': return self.do_delete(ast)
        return f"Operación no soportada: {ast.type}"

    # ══════════════════════════════════════════════════════════
    # GESTIÓN DE TABLAS
    # ══════════════════════════════════════════════════════════

    def do_create(self, ast):
        """
        CREATE TABLE: crea un nuevo árbol B+ para la tabla y la registra
        en el catálogo con sus columnas y tipos.
        Falla si la tabla ya existe (no sobrescribir datos).
        """
        if ast.table in self.tables:
            return f"[Error] La tabla '{ast.table}' ya existe"
        # orden=4 significa máximo 4 claves por nodo en el árbol B+
        self.tables[ast.table] = BPlusTree(order=4)
        # registrar metadatos en el catálogo
        self.catalog.register_table(ast.table, ast.columns)
        return f"Tabla '{ast.table}' creada exitosamente."

    def do_drop(self, ast):
        """
        DROP TABLE: elimina el árbol B+ y todos sus datos, y borra la
        entrada del catálogo.
        Falla si la tabla no existe.
        """
        if ast.table not in self.tables:
            return f"[Error] La tabla '{ast.table}' no existe"
        del self.tables[ast.table]
        self.catalog.drop_table(ast.table)
        return f"Tabla '{ast.table}' eliminada."

    # ══════════════════════════════════════════════════════════
    # OPERACIONES CRUD
    # ══════════════════════════════════════════════════════════

    def do_insert(self, ast):
        """
        INSERT: inserta un registro en el árbol B+.
        El primer valor de la lista es la clave primaria (key).
        El registro completo (todos los valores) se guarda como valor.
        """
        if ast.table not in self.tables:
            return f"[Error] La tabla '{ast.table}' no existe"
        key    = ast.values[0]   # clave primaria = primer campo
        record = ast.values      # registro completo
        self.tables[ast.table].insert(key, record)
        return f"1 registro insertado en '{ast.table}'."

    def do_select(self, ast):
        """
        SELECT: busca registros en el árbol B+.
        
        - Con WHERE campo = valor → búsqueda puntual O(log n)
        - Sin WHERE               → recorrido completo por las hojas O(n)
        
        El recorrido por hojas aprovecha la lista enlazada del árbol B+:
        se llega a la hoja más izquierda y se recorre con .next
        """
        if ast.table not in self.tables:
            return f"[Error] La tabla '{ast.table}' no existe"
        tree = self.tables[ast.table]

        if ast.where:
            # Búsqueda por clave primaria: O(log n)
            key    = ast.where['value']
            result = tree.search(key)
            return [result] if result is not None else []

        # Sin WHERE: recorrido completo O(n) usando la lista enlazada de hojas
        results = []
        node = tree.root
        if node is None:
            return []
        # bajar hasta la hoja más a la izquierda
        while not node.is_leaf:
            node = node.children[0]
        # recorrer todas las hojas con el puntero .next
        while node is not None:
            results.extend(node.records)
            node = node.next
        return results

    def do_update(self, ast):
        """
        UPDATE: modifica el registro asociado a una clave existente.
        Usa tree.update() del árbol B+ para actualizar el valor.
        Solo soporta UPDATE con WHERE sobre la clave primaria.
        """
        if ast.table not in self.tables:
            return f"[Error] La tabla '{ast.table}' no existe"
        tree = self.tables[ast.table]

        if not ast.where:
            return "[Error] UPDATE requiere una cláusula WHERE"

        key    = ast.where['value']
        record = tree.search(key)

        if record is None:
            return f"0 registros actualizados (clave {key} no encontrada)."

        # Actualizar el primer valor del assignment
        new_value = ast.assignments[0]['value']
        tree.update(key, new_value)
        return f"1 registro actualizado en '{ast.table}'."

    def do_delete(self, ast):
        """
        DELETE: elimina un registro del árbol B+ por clave primaria.
        Solo soporta DELETE con WHERE sobre la clave primaria.
        """
        if ast.table not in self.tables:
            return f"[Error] La tabla '{ast.table}' no existe"
        if not ast.where:
            return "[Error] DELETE requiere una cláusula WHERE"

        key = ast.where['value']
        self.tables[ast.table].delete(key)
        return f"Registro con clave {key} eliminado de '{ast.table}'."