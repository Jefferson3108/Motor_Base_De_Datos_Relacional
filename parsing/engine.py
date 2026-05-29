import os

from catalog.catalog import Catalog
from storage.buffer_pool import BufferPool
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
        self.buffers = {}
        # Catálogo del sistema: guarda metadatos (columnas y tipos)
        self.catalog = Catalog("data/catalog.json")
        # Al iniciar el motor, cargamos las tablas existentes del catálogo
        for table_name in self.catalog._tables:
            self.tables[table_name] = BPlusTree(order=50)
            self.buffers[table_name] = BufferPool(f"data/{table_name}.db")
            self._load_table(table_name)

    # ══════════════════════════════════════════════════════════
    # PUNTO DE ENTRADA PRINCIPAL
    # ══════════════════════════════════════════════════════════

    def _load_table(self, table_name:str):
        buffer = self.buffers[table_name]
        columns = self.catalog.get_columns(table_name)
        type_map={'INT': int, 'STR': str, 'FLOAT': float, 'BOOL': bool}
        total_pages = buffer.disk.total_pages()
        for page_id in range(total_pages):
            page = buffer.fetch_page(page_id)
            for record in page.records:
                converted_record = []
                for i, col in enumerate(columns):
                    col_type=type_map.get(col['type'].upper(), str)
                    converted_record.append(col_type(record[i]))
                key = converted_record[0]  # Asumiendo que la clave primaria es el primer campo
                self.tables[table_name].insert(key, converted_record)

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
            print(f"[Error de ejecución] {e}")
            import traceback
            traceback.print_exc()
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
        if not ast.columns:
            return f"[Error] CREATE TABLE requiere al menos una columna"
        if ast.columns[0]['type'].upper()!='INT':
            return f"[Error] La primera columna debe ser de tipo INT para ser la clave primaria"
        self.tables[ast.table] = BPlusTree(order=50)
        # registrar metadatos en el catálogo
        self.buffers[ast.table] = BufferPool(f"data/{ast.table}.db")
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
        if ast.table in self.buffers:
            del self.buffers[ast.table]
        db_path = f"data/{ast.table}.db"
        if os.path.exists(db_path):
            os.remove(db_path)
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
        print(f"Valores a insertar: {ast.values}")
        print(f"Tipos esperados: {[type(v).__name__ for v in ast.values]}")
        if ast.table not in self.tables:
            return f"[Error] La tabla '{ast.table}' no existe"
        existing=self.tables[ast.table].search(ast.values[0])
        if existing is not None:
            return f"[Error] La clave primaria '{ast.values[0]}' ya existe en la tabla '{ast.table}'"
        
        columns = self.catalog.get_columns(ast.table)
        if len(ast.values) != len(columns):
            return f"[Error] La tabla '{ast.table}' espera {len(columns)} valores, pero se recibieron {len(ast.values)}"
        type_map={'INT': int, 'STR': str, 'FLOAT': float, 'BOOL': bool}
        for i, col in enumerate(columns):
            col_name, col_type = col['name'], col['type']
            expected_type = type_map.get(col_type.upper())
            if expected_type and not isinstance(ast.values[i], expected_type):
             return f"[Error] El valor '{ast.values[i]}' no coincide con el tipo esperado {col_type} para la columna '{col_name}'"

        key    = ast.values[0]   # clave primaria = primer campo
        record = ast.values      # registro completo
        self.tables[ast.table].insert(key, record)
        page = self.buffers[ast.table].get_page_with_space(record)
        self.buffers[ast.table].flush_page(page.page_id)
        page.add_record(record)
        print(f"Pagina {page.page_id} tiene ahora {page.records}")
        self.buffers[ast.table].flush_page(page.page_id)
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
            key=ast.where['value']
            operator=ast.where['operator']
            
            if operator == '=':
                result = tree.search(key)
                return [result] if result else []
            elif operator == '>':
                return tree.search_greater(key)
            elif operator == '<':
                return tree.search_less(key)
            elif operator=='BETWEEN':
                low, high = key
                return tree.range_search(low, high)
            
        return tree.get_all()
              

       

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
        columns= self.catalog.get_columns(ast.table)
        col_names= [col['name'] for col in columns]
        new_record = list(record)  # convertir tupla a lista para modificar
        for assignment in ast.assignments:
            field = assignment['field']
            value = assignment['value']
            if field not in col_names:
                return f"[Error] La columna '{field}' no existe en la tabla '{ast.table}'"
            idx = col_names.index(field)
            new_record[idx] = value

        tree.update(key, new_record)
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
        self.buffers[ast.table].flush_page(key)  # Asumiendo que la clave es el ID del registro
        return f"Registro con clave {key} eliminado de '{ast.table}'."