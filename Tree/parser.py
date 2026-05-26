# parser.py

class ASTNode:
    """Nodo del Árbol de Sintaxis Abstracta"""
    def __init__(self, type_, **kwargs):
        self.type = type_
        self.__dict__.update(kwargs)

    def __repr__(self):
        info = {k: v for k, v in self.__dict__.items() if k != 'type'}
        return f"ASTNode({self.type}, {info})"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0         # posición actual en la lista de tokens

    # ── helpers ──────────────────────────────────────────────────

    def current(self):
        """Token actual sin consumirlo"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None, expected_value=None):
        """Consumir el token actual; lanza error si no coincide"""
        token = self.current()
        if token is None:
            raise SyntaxError("Se esperaba más tokens pero se llegó al final")
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"Se esperaba tipo {expected_type}, se obtuvo {token.type} ('{token.value}')")
        if expected_value and token.value.upper() != expected_value.upper():
            raise SyntaxError(f"Se esperaba '{expected_value}', se obtuvo '{token.value}'")
        self.pos += 1
        return token

    # ── punto de entrada ─────────────────────────────────────────

    def parse(self):
        """Detecta qué tipo de sentencia es y delega"""
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
        raise SyntaxError(f"Comando desconocido: {token.value}")

    # ── SELECT ───────────────────────────────────────────────────

    def parse_select(self):
        self.consume('KEYWORD', 'SELECT')
        fields = self.parse_field_list()
        self.consume('KEYWORD', 'FROM')
        table  = self.consume('IDENTIFIER').value
        where  = self.parse_where() if (self.current() and self.current().value.upper() == 'WHERE') else None
        return ASTNode('SELECT', fields=fields, table=table, where=where)

    # ── INSERT ───────────────────────────────────────────────────

    def parse_insert(self):
        self.consume('KEYWORD', 'INSERT')
        self.consume('KEYWORD', 'INTO')
        table = self.consume('IDENTIFIER').value
        self.consume('KEYWORD', 'VALUES')
        self.consume('LPAREN')
        values = self.parse_value_list()
        self.consume('RPAREN')
        return ASTNode('INSERT', table=table, values=values)

    # ── UPDATE ───────────────────────────────────────────────────

    def parse_update(self):
        self.consume('KEYWORD', 'UPDATE')
        table = self.consume('IDENTIFIER').value
        self.consume('KEYWORD', 'SET')
        assignments = self.parse_assignments()
        where = self.parse_where() if (self.current() and self.current().value.upper() == 'WHERE') else None
        return ASTNode('UPDATE', table=table, assignments=assignments, where=where)

    # ── DELETE ───────────────────────────────────────────────────

    def parse_delete(self):
        self.consume('KEYWORD', 'DELETE')
        self.consume('KEYWORD', 'FROM')
        table = self.consume('IDENTIFIER').value
        where = self.parse_where() if (self.current() and self.current().value.upper() == 'WHERE') else None
        return ASTNode('DELETE', table=table, where=where)

    # ── CREATE TABLE ─────────────────────────────────────────────

    def parse_create(self):
        self.consume('KEYWORD', 'CREATE')
        self.consume('KEYWORD', 'TABLE')
        table = self.consume('IDENTIFIER').value
        self.consume('LPAREN')
        columns = self.parse_column_defs()
        self.consume('RPAREN')
        return ASTNode('CREATE', table=table, columns=columns)

    def parse_column_defs(self):
        """nombre tipo, nombre tipo, ..."""
        columns = []
        while True:
            name = self.consume('IDENTIFIER').value
            type_ = self.consume('IDENTIFIER').value   # int, text, real, boolean
            columns.append({'name': name, 'type': type_})
            if self.current() and self.current().type == 'COMMA':
                self.consume('COMMA')
            else:
                break
        return columns

    # ── DROP TABLE ───────────────────────────────────────────────

    def parse_drop(self):
        self.consume('KEYWORD', 'DROP')
        self.consume('KEYWORD', 'TABLE')
        table = self.consume('IDENTIFIER').value
        return ASTNode('DROP', table=table)

    # ── helpers compartidos ───────────────────────────────────────

    def parse_field_list(self):
        """* ó campo, campo, ..."""
        if self.current() and self.current().type == 'STAR':
            self.consume('STAR')
            return ['*']
        fields = [self.consume('IDENTIFIER').value]
        while self.current() and self.current().type == 'COMMA':
            self.consume('COMMA')
            fields.append(self.consume('IDENTIFIER').value)
        return fields

    def parse_value_list(self):
        """1, 'texto', 3.14, ..."""
        values = [self.parse_value()]
        while self.current() and self.current().type == 'COMMA':
            self.consume('COMMA')
            values.append(self.parse_value())
        return values

    def parse_value(self):
        token = self.current()
        if token.type == 'NUMBER':
            self.consume()
            return float(token.value) if '.' in token.value else int(token.value)
        if token.type == 'STRING':
            self.consume()
            return token.value.strip("'")
        if token.type == 'IDENTIFIER':
            self.consume()
            return token.value
        raise SyntaxError(f"Valor inesperado: {token.value}")

    def parse_assignments(self):
        """campo = valor, campo = valor, ..."""
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

    def parse_where(self):
        """WHERE campo operador valor"""
        self.consume('KEYWORD', 'WHERE')
        field    = self.consume('IDENTIFIER').value
        operator = self.consume('OPERATOR').value
        value    = self.parse_value()
        return {'field': field, 'operator': operator, 'value': value}