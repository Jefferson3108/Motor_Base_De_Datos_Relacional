# engine.py  (usa tu BPlusTree.py + lexer.py + parser.py)

from BPlusTree import BPlusTree
from lexer     import Lexer
from parser    import Parser

class DatabaseEngine:
    def __init__(self):
        self.tables = {}   # nombre → BPlusTree

    def execute(self, sql: str):
        """Punto de entrada: recibe SQL en texto, devuelve resultado"""
        try:
            tokens = Lexer(sql).tokenize()
            ast    = Parser(tokens).parse()
            return self.dispatch(ast)
        except SyntaxError as e:
            return f"Error de sintaxis: {e}"
        except Exception as e:
            return f"Error de ejecución: {e}"

    def dispatch(self, ast):
        if ast.type == 'CREATE': return self.do_create(ast)
        if ast.type == 'DROP':   return self.do_drop(ast)
        if ast.type == 'INSERT': return self.do_insert(ast)
        if ast.type == 'SELECT': return self.do_select(ast)
        if ast.type == 'UPDATE': return self.do_update(ast)
        if ast.type == 'DELETE': return self.do_delete(ast)

    def do_create(self, ast):
        if ast.table in self.tables:
            return f"Error: la tabla '{ast.table}' ya existe"
        self.tables[ast.table] = BPlusTree(order=4)
        return f"Tabla '{ast.table}' creada."

    def do_drop(self, ast):
        if ast.table not in self.tables:
            return f"Error: tabla '{ast.table}' no existe"
        del self.tables[ast.table]
        return f"Tabla '{ast.table}' eliminada."

    def do_insert(self, ast):
        if ast.table not in self.tables:
            return f"Error: tabla '{ast.table}' no existe"
        key    = ast.values[0]          # primera columna = clave primaria
        record = ast.values
        self.tables[ast.table].insert(key, record)
        return f"1 registro insertado en '{ast.table}'."

    def do_select(self, ast):
        if ast.table not in self.tables:
            return f"Error: tabla '{ast.table}' no existe"
        tree = self.tables[ast.table]
        if ast.where:
            key    = ast.where['value']
            result = tree.search(key)
            return [result] if result else []
        # sin WHERE: recorrer todas las hojas
        results = []
        node = tree.root
        while node and not node.is_leaf:
            node = node.children[0]
        while node:
            results.extend(node.records)
            node = node.next
        return results

    def do_update(self, ast):
        if ast.table not in self.tables:
            return f"Error: tabla '{ast.table}' no existe"
        tree = self.tables[ast.table]
        if ast.where:
            key    = ast.where['value']
            record = tree.search(key)
            if record:
                for a in ast.assignments:
                    tree.update(key, a['value'])
                return "1 registro actualizado."
        return "0 registros actualizados."

    def do_delete(self, ast):
        if ast.table not in self.tables:
            return f"Error: tabla '{ast.table}' no existe"
        if ast.where:
            key = ast.where['value']
            self.tables[ast.table].delete(key)
            return "Registro eliminado."
        return "Especifica una condición WHERE para DELETE."