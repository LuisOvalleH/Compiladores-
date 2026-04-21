import json
import re


codigo = """
inicio
    a = 10
    b = 20
    c = a + b * 2
    si (c > 30) entonces
        escribir(c)
        d = c - 10
    finsi
    escribir(d)
fin
"""


token_regex = re.compile(
    r"(?P<NUM>\d+)|"
    r"(?P<ID>[a-zA-Z_][a-zA-Z0-9_]*)|"
    r"(?P<OP>>=|<=|==|!=|[+\-*/=<>])|"
    r"(?P<PAR>[()])"
)

reservadas = {"inicio", "fin", "si", "entonces", "finsi", "escribir"}


def lexico(texto):
    tokens = []
    for linea, contenido in enumerate(texto.splitlines(), start=1):
        for match in token_regex.finditer(contenido):
            valor = match.group()
            if match.lastgroup == "ID" and valor in reservadas:
                tipo = "RESERVADA"
            elif match.lastgroup == "ID":
                tipo = "IDENTIFICADOR"
            elif match.lastgroup == "NUM":
                tipo = "NUMERO"
            elif match.lastgroup == "OP":
                tipo = "OPERADOR"
            else:
                tipo = "DELIMITADOR"
            tokens.append((tipo, valor, linea))
    tokens.append(("EOF", "EOF", -1))
    return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def actual(self):
        return self.tokens[self.pos]

    def ver(self, tipo, valor=None):
        tok = self.actual()
        if tok[0] != tipo:
            return False
        return valor is None or tok[1] == valor

    def consumir(self, tipo, valor=None):
        tok = self.actual()
        if not self.ver(tipo, valor):
            esperado = valor if valor else tipo
            raise SyntaxError(f"Se esperaba {esperado} y se encontro {tok}")
        self.pos += 1
        return tok

    def parsear(self):
        self.consumir("RESERVADA", "inicio")
        instrucciones = []
        while not self.ver("RESERVADA", "fin"):
            instrucciones.append(self.instruccion())
        self.consumir("RESERVADA", "fin")
        return {"tipo": "programa", "instrucciones": instrucciones}

    def instruccion(self):
        if self.ver("IDENTIFICADOR"):
            nombre = self.consumir("IDENTIFICADOR")[1]
            self.consumir("OPERADOR", "=")
            return {"tipo": "asignacion", "variable": nombre, "expr": self.expresion()}

        if self.ver("RESERVADA", "escribir"):
            self.consumir("RESERVADA", "escribir")
            self.consumir("DELIMITADOR", "(")
            expr = self.expresion()
            self.consumir("DELIMITADOR", ")")
            return {"tipo": "escribir", "expr": expr}

        if self.ver("RESERVADA", "si"):
            self.consumir("RESERVADA", "si")
            self.consumir("DELIMITADOR", "(")
            condicion = self.expresion()
            self.consumir("DELIMITADOR", ")")
            self.consumir("RESERVADA", "entonces")
            cuerpo = []
            while not self.ver("RESERVADA", "finsi"):
                cuerpo.append(self.instruccion())
            self.consumir("RESERVADA", "finsi")
            return {"tipo": "si", "condicion": condicion, "cuerpo": cuerpo}

        raise SyntaxError(f"Instruccion no valida: {self.actual()}")

    def expresion(self):
        return self.comparacion()

    def comparacion(self):
        nodo = self.suma()
        while self.ver("OPERADOR") and self.actual()[1] in {">", "<", ">=", "<=", "==", "!="}:
            op = self.consumir("OPERADOR")[1]
            nodo = {"tipo": "binaria", "op": op, "izq": nodo, "der": self.suma()}
        return nodo

    def suma(self):
        nodo = self.producto()
        while self.ver("OPERADOR") and self.actual()[1] in {"+", "-"}:
            op = self.consumir("OPERADOR")[1]
            nodo = {"tipo": "binaria", "op": op, "izq": nodo, "der": self.producto()}
        return nodo

    def producto(self):
        nodo = self.primario()
        while self.ver("OPERADOR") and self.actual()[1] in {"*", "/"}:
            op = self.consumir("OPERADOR")[1]
            nodo = {"tipo": "binaria", "op": op, "izq": nodo, "der": self.primario()}
        return nodo

    def primario(self):
        if self.ver("NUMERO"):
            return {"tipo": "constante", "valor": int(self.consumir("NUMERO")[1])}
        if self.ver("IDENTIFICADOR"):
            return {"tipo": "variable", "nombre": self.consumir("IDENTIFICADOR")[1]}
        if self.ver("DELIMITADOR", "("):
            self.consumir("DELIMITADOR", "(")
            nodo = self.expresion()
            self.consumir("DELIMITADOR", ")")
            return nodo
        raise SyntaxError(f"Expresion no valida: {self.actual()}")


def operar(op, a, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return a // b
    if op == ">":
        return a > b
    if op == "<":
        return a < b
    if op == ">=":
        return a >= b
    if op == "<=":
        return a <= b
    if op == "==":
        return a == b
    if op == "!=":
        return a != b
    raise ValueError(op)


def evaluar(expr, valores):
    if expr["tipo"] == "constante":
        return expr["valor"]
    if expr["tipo"] == "variable":
        return valores.get(expr["nombre"])
    izq = evaluar(expr["izq"], valores)
    der = evaluar(expr["der"], valores)
    if izq is None or der is None:
        return None
    return operar(expr["op"], izq, der)


def variables_en(expr):
    if expr["tipo"] == "variable":
        return [expr["nombre"]]
    if expr["tipo"] == "binaria":
        return variables_en(expr["izq"]) + variables_en(expr["der"])
    return []


def semantico(ast):
    tabla = {}
    errores = []
    valores = {}

    def revisar(instrucciones):
        for inst in instrucciones:
            if inst["tipo"] == "asignacion":
                for var in variables_en(inst["expr"]):
                    if var not in tabla:
                        errores.append(f"Variable {var} usada antes de asignarse")
                valor = evaluar(inst["expr"], valores)
                tabla[inst["variable"]] = {"tipo": "entero", "valor": valor}
                valores[inst["variable"]] = valor

            elif inst["tipo"] == "escribir":
                for var in variables_en(inst["expr"]):
                    if var not in tabla:
                        errores.append(f"Variable {var} usada antes de asignarse")

            elif inst["tipo"] == "si":
                for var in variables_en(inst["condicion"]):
                    if var not in tabla:
                        errores.append(f"Variable {var} usada antes de asignarse")

                condicion = evaluar(inst["condicion"], valores)
                if condicion is True:
                    revisar(inst["cuerpo"])
                elif condicion is None:
                    # En un compilador mas estricto, las variables creadas aqui serian condicionales.
                    revisar(inst["cuerpo"])

    revisar(ast["instrucciones"])
    return tabla, errores, valores


def tres_direcciones(ast):
    lineas = []
    temp = 1
    label = 1

    def nuevo_temp():
        nonlocal temp
        nombre = f"t{temp}"
        temp += 1
        return nombre

    def nuevo_label():
        nonlocal label
        nombre = f"L{label}"
        label += 1
        return nombre

    def expr(e):
        if e["tipo"] == "constante":
            return str(e["valor"])
        if e["tipo"] == "variable":
            return e["nombre"]
        izq = expr(e["izq"])
        der = expr(e["der"])
        t = nuevo_temp()
        lineas.append(f"{t} = {izq} {e['op']} {der}")
        return t

    def inst(instrucciones):
        for i in instrucciones:
            if i["tipo"] == "asignacion":
                lineas.append(f"{i['variable']} = {expr(i['expr'])}")
            elif i["tipo"] == "escribir":
                lineas.append(f"escribir {expr(i['expr'])}")
            elif i["tipo"] == "si":
                cond = expr(i["condicion"])
                fin = nuevo_label()
                lineas.append(f"if_false {cond} goto {fin}")
                inst(i["cuerpo"])
                lineas.append(f"{fin}:")

    inst(ast["instrucciones"])
    return lineas


def optimizado(ast):
    valores = {}
    lineas = []

    def texto(e):
        if e["tipo"] == "constante":
            return str(e["valor"])
        if e["tipo"] == "variable":
            return e["nombre"]
        return f"{texto(e['izq'])} {e['op']} {texto(e['der'])}"

    def inst(instrucciones):
        for i in instrucciones:
            if i["tipo"] == "asignacion":
                valor = evaluar(i["expr"], valores)
                if valor is not None:
                    valores[i["variable"]] = valor
                    lineas.append(f"{i['variable']} = {valor}")
                else:
                    lineas.append(f"{i['variable']} = {texto(i['expr'])}")
            elif i["tipo"] == "escribir":
                valor = evaluar(i["expr"], valores)
                lineas.append(f"escribir {valor if valor is not None else texto(i['expr'])}")
            elif i["tipo"] == "si":
                cond = evaluar(i["condicion"], valores)
                if cond is True:
                    lineas.append("# condicion verdadera, se elimina el salto")
                    inst(i["cuerpo"])
                elif cond is False:
                    lineas.append("# condicion falsa, se elimina el cuerpo")
                else:
                    lineas.append(f"if_false {texto(i['condicion'])} goto L1")
                    inst(i["cuerpo"])
                    lineas.append("L1:")

    inst(ast["instrucciones"])
    return lineas


def mips(ast):
    lineas = [
        ".data",
        "    a: .word 0",
        "    b: .word 0",
        "    c: .word 0",
        "    d: .word 0",
        "    salto: .asciiz \"\\n\"",
        ".text",
        ".globl main",
        "main:",
    ]
    reg = 0
    label = 1

    def nuevo_reg():
        nonlocal reg
        nombre = f"$t{reg % 10}"
        reg += 1
        return nombre

    def expr(e):
        if e["tipo"] == "constante":
            r = nuevo_reg()
            lineas.append(f"    li {r}, {e['valor']}")
            return r
        if e["tipo"] == "variable":
            r = nuevo_reg()
            lineas.append(f"    lw {r}, {e['nombre']}")
            return r

        r1 = expr(e["izq"])
        r2 = expr(e["der"])
        r3 = nuevo_reg()
        if e["op"] == "+":
            lineas.append(f"    add {r3}, {r1}, {r2}")
        elif e["op"] == "-":
            lineas.append(f"    sub {r3}, {r1}, {r2}")
        elif e["op"] == "*":
            lineas.append(f"    mul {r3}, {r1}, {r2}")
        elif e["op"] == "/":
            lineas.append(f"    div {r1}, {r2}")
            lineas.append(f"    mflo {r3}")
        return r3

    def salto_falso(cond, etiqueta):
        r1 = expr(cond["izq"])
        r2 = expr(cond["der"])
        saltos = {">": "ble", "<": "bge", ">=": "blt", "<=": "bgt", "==": "bne", "!=": "beq"}
        lineas.append(f"    {saltos[cond['op']]} {r1}, {r2}, {etiqueta}")

    def inst(instrucciones):
        nonlocal label
        for i in instrucciones:
            if i["tipo"] == "asignacion":
                r = expr(i["expr"])
                lineas.append(f"    sw {r}, {i['variable']}")
            elif i["tipo"] == "escribir":
                r = expr(i["expr"])
                lineas.extend([
                    f"    move $a0, {r}",
                    "    li $v0, 1",
                    "    syscall",
                    "    la $a0, salto",
                    "    li $v0, 4",
                    "    syscall",
                ])
            elif i["tipo"] == "si":
                etiqueta = f"L_fin_si_{label}"
                label += 1
                salto_falso(i["condicion"], etiqueta)
                inst(i["cuerpo"])
                lineas.append(f"{etiqueta}:")

    inst(ast["instrucciones"])
    lineas.extend(["    li $v0, 10", "    syscall"])
    return lineas


def imprimir_titulo(titulo):
    print("\n" + "=" * 60)
    print(titulo)
    print("=" * 60)


def main():
    tokens = lexico(codigo)
    ast = Parser(tokens).parsear()
    tabla, errores, valores = semantico(ast)
    tac = tres_direcciones(ast)
    opt = optimizado(ast)
    asm = mips(ast)

    imprimir_titulo("PROGRAMA FUENTE")
    print(codigo.strip())

    imprimir_titulo("1. TOKENS")
    for token in tokens[:-1]:
        print(token)

    imprimir_titulo("2. AST JSON")
    print(json.dumps(ast, indent=2, ensure_ascii=False))

    imprimir_titulo("3. TABLA DE SIMBOLOS Y SEMANTICA")
    for nombre, datos in tabla.items():
        print(f"{nombre}: tipo={datos['tipo']}, valor={datos['valor']}")
    if errores:
        print("Errores:")
        for error in errores:
            print("-", error)
    else:
        print("No hay errores semanticos.")
        print("d se puede usar despues del finsi porque c = 50, por lo tanto c > 30 es verdadero.")

    imprimir_titulo("4. CODIGO DE 3 DIRECCIONES")
    print("\n".join(tac))

    imprimir_titulo("4. CODIGO OPTIMIZADO")
    print("Optimizaciones: plegado/propagacion de constantes y eliminacion del salto del si.")
    print("\n".join(opt))

    imprimir_titulo("5. ENSAMBLADOR MIPS SIMPLIFICADO")
    print("\n".join(asm))


if __name__ == "__main__":
    main()
