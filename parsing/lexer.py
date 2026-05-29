import re

# TIPOS DE TOKENS
# Cada entrada es: nombre → patrón regex
# El orden importa: KEYWORD debe ir antes de IDENTIFIER
# para que "SELECT" no sea clasificado como identificador.

TOKEN_TYPES = {
    'KEYWORD':    r'\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|INTO|VALUES|SET|CREATE|DROP|TABLE|AND|OR)\b',
    'BOOLEAN':    r'\b(true|false)\b',              # valores booleanos
    'IDENTIFIER': r'[a-zA-Z_][a-zA-Z0-9_]*',   # nombres de tablas y columnas
    'NUMBER':     r'\d+(\.\d+)?',               # enteros y decimales
    'STRING':     r"'[^']*'",                   # texto entre comillas simples
    'OPERATOR':   r'[=<>!]+',                   # =, !=, >=, <=, entre otros.
    'COMMA':      r',',
    'SEMICOLON':  r';',
    'LPAREN':     r'\(',                         # paréntesis izquierdo
    'RPAREN':     r'\)',                         # paréntesis derecho
    'STAR':       r'\*',                         # asterisco para SELECT *
}

class Token:
    """
    Unidad mínima de significado en SQL.
    type  → qué clase de token es (KEYWORD, IDENTIFIER, NUMBER, etcetera)
    value → el texto exacto que apareció en la consulta
    """
    def __init__(self, type_, value):
        self.type  = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


class Lexer:
    """
    Convierte una cadena SQL en una lista de Token.
    
    Uso:
        tokens = Lexer("SELECT * FROM users").tokenize()
    """
    def __init__(self, text):
        self.text = text.strip()   # eliminar espacios al inicio/final

    def tokenize(self):
        tokens = []
        text   = self.text

        # Construir el patrón maestro combinando todos los tipos.
        # Cada grupo tiene un nombre (?P<NOMBRE>patrón) para poder
        # saber cuál fue el que hizo match con match.lastgroup
        master_pattern = '|'.join(
            f'(?P<{name}>{pattern})'
            for name, pattern in TOKEN_TYPES.items()
        )

        for match in re.finditer(master_pattern, text, re.IGNORECASE):
            type_  = match.lastgroup          # nombre del grupo que hizo match
            value  = match.group()            # texto que coincidió

            # Normalizar keywords a mayúsculas para comparaciones uniformes
            if type_ == 'KEYWORD':
                value = value.upper()

            tokens.append(Token(type_, value))

        return tokens