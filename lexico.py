import re

PATRONES = [
    ("WHITESPACE", r"\s+"),
    ("COMMENT", r"//[^\n]*"),
    ("KEYWORD", r"\b(?:if|else|while|for|return|int|float|void|print|println)\b"),
    ("IDENTIFIER", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
    ("NUMBER", r"\b\d+(?:\.\d+)?\b"),
    ("STRING", r'"[^"\\]*(?:\\.[^"\\]*)*"'),
    ("OPERATOR", r"==|<=|>=|[+\-*/=<>]"),
    ("DELIMITER", r"[(),;{}]"),
]

MASTER_REGEX = re.compile("|".join(f"(?P<{nombre}>{patron})" for nombre, patron in PATRONES))


def identificar_tokens(texto):
    tokens = []
    posicion = 0

    while posicion < len(texto):
        match = MASTER_REGEX.match(texto, posicion)
        if not match:
            fragmento = texto[posicion:posicion + 20]
            raise SyntaxError(f"Token invalido cerca de: {fragmento!r}")

        tipo = match.lastgroup
        valor = match.group(tipo)
        if tipo not in {"WHITESPACE", "COMMENT"}:
            tokens.append((tipo, valor))

        posicion = match.end()

    return tokens
