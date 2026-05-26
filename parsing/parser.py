class ASTNode:
    """
    Nodo del Árbol de Sintaxis Abstracta (AST).
    
    Cada consulta SQL se convierte en un ASTNode con:
      - type        → tipo de operación: SELECT, INSERT, UPDATE, DELETE, CREATE, DROP
      - atributos   → dependen del tipo (table, fields, where, values, etc.)
    
    Ejemplos:
      SELECT → ASTNode(type='SELECT', fields=['nombre'], table='usuarios', where={...})
      INSERT → ASTNode(type='INSERT', table='usuarios', values=[1, 'Ana'])
    """
    def __init__(self, type_, **kwargs):
        self.type = type_
        self.__dict__.update(kwargs)   # agregar atributos dinámicamente

    def __repr__(self):
        info = {k: v for k, v in self.__dict__.items() if k != 'type'}
        return f"ASTNode({self.type}, {info})"


class Parser:
    """
    Analiza una lista de tokens y produce un ASTNode.
    
    Uso:
        tokens = Lexer("SELECT * FROM t").tokenize()
        ast    = Parser(tokens).parse()
    """
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0   # índice del token que se está analizando ahora

    # ══════════════════════════════════════════════════════════
    # MÉTODOS DE NAVEGACIÓN
    # ══════════════════════════════════════════════════════════

    def current(self):
        """
        Devuelve el token en la posición actual SIN avanzar.
        Retorna None si ya se llegó al final de la lista.
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None, expected_value=None):
        """
        Consume el token actual (lo retorna y avanza pos en 1).
        Si se especifican expected_type o expected_value, verifica
        que el token actual coincida; si no, lanza SyntaxError.
        
        Ejemplos:
            consume()                    → consume cualquier token
            consume('KEYWORD')           → consume solo si es KEYWORD
            consume('KEYWORD', 'SELECT') → consume solo si es SELECT
        """
        token = self.current()
        if token is None:
            raise SyntaxError("Se esperaban más tokens pero se llegó al final")
        if expected_type and token.type != expected_type:
            raise SyntaxError(
                f"Se esperaba tipo '{expected_type}', "
                f"se obtuvo '{token.type}' (valor: '{token.value}')"
            )
        if expected_value and token.value.upper() != expected_value.upper():
            raise SyntaxError(
                f"Se esperaba '{expected_value}', "
                f"se obtuvo '{token.value}'"
            )
        self.pos += 1
        return token

    # ══════════════════════════════════════════════════════════
    # PUNTO DE ENTRADA
    # ══════════════════════════════════════════════════════════

    def parse(self):
        """
        Lee el primer token para saber qué tipo de sentencia es
        y delega al método correspondiente.
        """
        token = self.current()
        if token is None:
            raise SyntaxError("Consulta vacía")

        cmd = token.value.upper()
        if cmd == 'SELECT': return self.parse_select()
        if cmd == 'INSERT': return self.parse_insert()
        if cmd == 'UPDATE': return self.parse_update()
        if cmd == 'DELETE': return self.parse_delete()
        if cmd == 'CREATE': return self.parse_create()
        if cmd == 'DROP':   return self.parse_drop()
        raise SyntaxError(f"Comando no reconocido: '{token.value}'")

    # ══════════════════════════════════════════════════════════
    # PARSERS ESPECÍFICOS POR COMANDO
    # ══════════════════════════════════════════════════════════

    def parse_select(self):
        """
        Gramática: SELECT <campos> FROM <tabla> [WHERE <condición>]
        <campos> = * | campo, campo, ...
        """
        self.consume('KEYWORD', 'SELECT')
        fields = self.parse_field_list()           # qué columnas traer
        self.consume('KEYWORD', 'FROM')
        table  = self.consume('IDENTIFIER').value  # nombre de la tabla
        where  = None
        if self.current() and self.current().value.upper() == 'WHERE':
            where = self.parse_where()
        return ASTNode('SELECT', fields=fields, table=table, where=where)

    def parse_insert(self):
        """
        Gramática: INSERT INTO <tabla> VALUES (<val1>, <val2>, ...)
        """
        self.consume('KEYWORD', 'INSERT')
        self.consume('KEYWORD', 'INTO')
        table = self.consume('IDENTIFIER').value
        self.consume('KEYWORD', 'VALUES')
        self.consume('LPAREN')
        values = self.parse_value_list()
        self.consume('RPAREN')
        return ASTNode('INSERT', table=table, values=values)

    def parse_update(self):
        """
        Gramática: UPDATE <tabla> SET campo=val [, campo=val] [WHERE <condición>]
        """
        self.consume('KEYWORD', 'UPDATE')
        table = self.consume('IDENTIFIER').value
        self.consume('KEYWORD', 'SET')
        assignments = self.parse_assignments()     # pares campo=valor
        where = None
        if self.current() and self.current().value.upper() == 'WHERE':
            where = self.parse_where()
        return ASTNode('UPDATE', table=table, assignments=assignments, where=where)

    def parse_delete(self):
        """
        Gramática: DELETE FROM <tabla> [WHERE <condición>]
        """
        self.consume('KEYWORD', 'DELETE')
        self.consume('KEYWORD', 'FROM')
        table = self.consume('IDENTIFIER').value
        where = None
        if self.current() and self.current().value.upper() == 'WHERE':
            where = self.parse_where()
        return ASTNode('DELETE', table=table, where=where)

    def parse_create(self):
        """
        Gramática: CREATE TABLE <tabla> (col tipo, col tipo, ...)
        """
        self.consume('KEYWORD', 'CREATE')
        self.consume('KEYWORD', 'TABLE')
        table = self.consume('IDENTIFIER').value
        self.consume('LPAREN')
        columns = self.parse_column_defs()
        self.consume('RPAREN')
        return ASTNode('CREATE', table=table, columns=columns)

    def parse_drop(self):
        """
        Gramática: DROP TABLE <tabla>
        """
        self.consume('KEYWORD', 'DROP')
        self.consume('KEYWORD', 'TABLE')
        table = self.consume('IDENTIFIER').value
        return ASTNode('DROP', table=table)

    # ══════════════════════════════════════════════════════════
    # HELPERS COMPARTIDOS
    # ══════════════════════════════════════════════════════════

    def parse_field_list(self):
        """
        Parsea la lista de columnas de un SELECT.
        Puede ser * o una lista separada por comas: col1, col2, col3
        """
        if self.current() and self.current().type == 'STAR':
            self.consume('STAR')
            return ['*']
        fields = [self.consume('IDENTIFIER').value]
        while self.current() and self.current().type == 'COMMA':
            self.consume('COMMA')
            fields.append(self.consume('IDENTIFIER').value)
        return fields

    def parse_value_list(self):
        """
        Parsea lista de valores: val1, val2, val3
        Cada valor puede ser NUMBER, STRING o IDENTIFIER
        """
        values = [self.parse_value()]
        while self.current() and self.current().type == 'COMMA':
            self.consume('COMMA')
            values.append(self.parse_value())
        return values

    def parse_value(self):
        """
        Parsea un valor individual:
          - NUMBER     → int o float
          - STRING     → texto sin comillas
          - IDENTIFIER → nombre (usado en UPDATE SET campo=otrocampo)
        """
        token = self.current()
        if token is None:
            raise SyntaxError("Se esperaba un valor")
        if token.type == 'NUMBER':
            self.consume()
            return float(token.value) if '.' in token.value else int(token.value)
        if token.type == 'STRING':
            self.consume()
            return token.value.strip("'")   # quitar comillas
        if token.type == 'IDENTIFIER':
            self.consume()
            return token.value
        raise SyntaxError(f"Valor inesperado: '{token.value}' (tipo {token.type})")

    def parse_assignments(self):
        """
        Parsea asignaciones del UPDATE: col1 = val1, col2 = val2
        Retorna lista de dicts: [{'field': 'col1', 'value': val1}, ...]
        """
        assignments = []
        while True:
            field = self.consume('IDENTIFIER').value
            self.consume('OPERATOR', '=')
            value = self.parse_value()
            assignments.append({'field': field, 'value': value})
            if self.current() and self.current().type == 'COMMA':
                self.consume('COMMA')
            else:
                break
        return assignments

    def parse_column_defs(self):
        """
        Parsea definición de columnas del CREATE TABLE.
        Formato: nombre tipo, nombre tipo, ...
        Retorna lista de dicts: [{'name': 'id', 'type': 'int'}, ...]
        """
        columns = []
        while True:
            name  = self.consume('IDENTIFIER').value
            type_ = self.consume('IDENTIFIER').value
            columns.append({'name': name, 'type': type_})
            if self.current() and self.current().type == 'COMMA':
                self.consume('COMMA')
            else:
                break
        return columns

    def parse_where(self):
        """
        Parsea cláusula WHERE: WHERE campo operador valor
        Retorna dict: {'field': campo, 'operator': op, 'value': val}
        """
        self.consume('KEYWORD', 'WHERE')
        field    = self.consume('IDENTIFIER').value
        operator = self.consume('OPERATOR').value
        value    = self.parse_value()
        return {'field': field, 'operator': operator, 'value': value}