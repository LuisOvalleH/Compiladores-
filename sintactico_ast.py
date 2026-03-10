import itertools


class NodoAST:
    def traducir_python(self):
        raise NotImplementedError()

    def traducir_lua(self):
        raise NotImplementedError()

    def to_dict(self):
        raise NotImplementedError()

    def traducir_asm(self, ctx):
        return ""


class NodoString(NodoAST):
    def __init__(self, token):
        self.valor = token[1]

    def traducir_python(self):
        return self.valor

    def traducir_lua(self):
        return self.valor

    def to_dict(self):
        return {"tipo": "string", "valor": self.valor}

    def traducir_asm(self, ctx):
        ident = f"str_{next(ctx['string_id'])}"
        contenido = self.valor[1:-1].replace("'", "\\'")
        ctx["data"].append(f"{ident} db '{contenido}', 0")
        ctx["data"].append(f"{ident}_len equ $ - {ident} - 1")
        return (
            "    mov rax, 1\n"
            "    mov rdi, 1\n"
            f"    mov rsi, {ident}\n"
            f"    mov rdx, {ident}_len\n"
            "    syscall\n"
        )


class NodoNumero(NodoAST):
    def __init__(self, token):
        self.valor = token[1]

    def traducir_python(self):
        return self.valor

    def traducir_lua(self):
        return self.valor

    def to_dict(self):
        return {"tipo": "numero", "valor": self.valor}

    def traducir_asm(self, ctx):
        return f"    mov rax, {self.valor}\n"


class NodoIdentificador(NodoAST):
    def __init__(self, token):
        self.nombre = token[1]

    def traducir_python(self):
        return self.nombre

    def traducir_lua(self):
        return self.nombre

    def to_dict(self):
        return {"tipo": "identificador", "nombre": self.nombre}

    def traducir_asm(self, ctx):
        return f"    mov rax, [var_{self.nombre}]\n"


class NodoOperacion(NodoAST):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

    def traducir_python(self):
        return f"{self.izquierda.traducir_python()} {self.operador} {self.derecha.traducir_python()}"

    def traducir_lua(self):
        op = self.operador
        if op == "==":
            op = "=="
        return f"{self.izquierda.traducir_lua()} {op} {self.derecha.traducir_lua()}"

    def to_dict(self):
        return {
            "tipo": "operacion",
            "operador": self.operador,
            "izquierda": self.izquierda.to_dict(),
            "derecha": self.derecha.to_dict(),
        }

    def traducir_asm(self, ctx):
        asm = self.izquierda.traducir_asm(ctx)
        asm += "    push rax\n"
        asm += self.derecha.traducir_asm(ctx)
        asm += "    mov rbx, rax\n"
        asm += "    pop rax\n"

        if self.operador == "+":
            asm += "    add rax, rbx\n"
        elif self.operador == "-":
            asm += "    sub rax, rbx\n"
        elif self.operador == "*":
            asm += "    imul rax, rbx\n"
        elif self.operador == "/":
            asm += "    cqo\n"
            asm += "    idiv rbx\n"
        elif self.operador in {"==", "<", ">", "<=", ">="}:
            asm += "    cmp rax, rbx\n"
            if self.operador == "==":
                asm += "    sete al\n"
            elif self.operador == "<":
                asm += "    setl al\n"
            elif self.operador == ">":
                asm += "    setg al\n"
            elif self.operador == "<=":
                asm += "    setle al\n"
            elif self.operador == ">=":
                asm += "    setge al\n"
            asm += "    movzx rax, al\n"
        else:
            asm += "    ; operador no soportado en ASM\n"
        return asm


class NodoDeclaracion(NodoAST):
    def __init__(self, tipo, nombre, expresion):
        self.tipo = tipo
        self.nombre = nombre
        self.expresion = expresion

    def traducir_python(self):
        return f"{self.nombre} = {self.expresion.traducir_python()}"

    def traducir_lua(self):
        return f"local {self.nombre} = {self.expresion.traducir_lua()}"

    def to_dict(self):
        return {
            "tipo": "declaracion",
            "dato": self.tipo,
            "variable": self.nombre,
            "expresion": self.expresion.to_dict(),
        }

    def traducir_asm(self, ctx):
        var = f"var_{self.nombre}"
        ctx["bss"].add(var)
        return self.expresion.traducir_asm(ctx) + f"    mov [{var}], rax\n"


class NodoAsignacion(NodoAST):
    def __init__(self, nombre, expresion):
        self.nombre = nombre
        self.expresion = expresion

    def traducir_python(self):
        return f"{self.nombre} = {self.expresion.traducir_python()}"

    def traducir_lua(self):
        return f"{self.nombre} = {self.expresion.traducir_lua()}"

    def to_dict(self):
        return {
            "tipo": "asignacion",
            "variable": self.nombre,
            "expresion": self.expresion.to_dict(),
        }

    def traducir_asm(self, ctx):
        return self.expresion.traducir_asm(ctx) + f"    mov [var_{self.nombre}], rax\n"


class NodoPrint(NodoAST):
    def __init__(self, expresiones, salto_linea):
        self.expresiones = expresiones
        self.salto_linea = salto_linea

    def traducir_python(self):
        args = ", ".join(x.traducir_python() for x in self.expresiones)
        if self.salto_linea:
            return f"print({args})"
        return f"print({args}, end='')"

    def traducir_lua(self):
        args = " .. ' ' .. ".join(x.traducir_lua() for x in self.expresiones)
        if self.salto_linea:
            return f"print({args})"
        return f"io.write({args})"

    def to_dict(self):
        return {
            "tipo": "print",
            "println": self.salto_linea,
            "argumentos": [x.to_dict() for x in self.expresiones],
        }

    def traducir_asm(self, ctx):
        asm = ""
        for expr in self.expresiones:
            if isinstance(expr, NodoString):
                asm += expr.traducir_asm(ctx)
            else:
                asm += expr.traducir_asm(ctx)
                asm += "    call print_int\n"
        if self.salto_linea:
            asm += "    call print_newline\n"
        return asm


class NodoIf(NodoAST):
    def __init__(self, condicion, cuerpo_if, cuerpo_else=None):
        self.condicion = condicion
        self.cuerpo_if = cuerpo_if
        self.cuerpo_else = cuerpo_else or []

    def traducir_python(self):
        bloque_if = "\n    ".join(x.traducir_python() for x in self.cuerpo_if) or "pass"
        resultado = f"if {self.condicion.traducir_python()}:\n    {bloque_if}"
        if self.cuerpo_else:
            bloque_else = "\n    ".join(x.traducir_python() for x in self.cuerpo_else) or "pass"
            resultado += f"\nelse:\n    {bloque_else}"
        return resultado

    def traducir_lua(self):
        bloque_if = "\n  ".join(x.traducir_lua() for x in self.cuerpo_if)
        resultado = f"if {self.condicion.traducir_lua()} then\n  {bloque_if}"
        if self.cuerpo_else:
            bloque_else = "\n  ".join(x.traducir_lua() for x in self.cuerpo_else)
            resultado += f"\nelse\n  {bloque_else}"
        resultado += "\nend"
        return resultado

    def to_dict(self):
        data = {
            "tipo": "if",
            "condicion": self.condicion.to_dict(),
            "cuerpo_if": [x.to_dict() for x in self.cuerpo_if],
        }
        if self.cuerpo_else:
            data["cuerpo_else"] = [x.to_dict() for x in self.cuerpo_else]
        return data

    def traducir_asm(self, ctx):
        etiqueta_else = f"L_else_{next(ctx['label_id'])}"
        etiqueta_fin = f"L_if_fin_{next(ctx['label_id'])}"

        asm = self.condicion.traducir_asm(ctx)
        asm += "    cmp rax, 0\n"
        asm += f"    je {etiqueta_else}\n"
        for instr in self.cuerpo_if:
            asm += instr.traducir_asm(ctx)
        asm += f"    jmp {etiqueta_fin}\n"
        asm += f"{etiqueta_else}:\n"
        for instr in self.cuerpo_else:
            asm += instr.traducir_asm(ctx)
        asm += f"{etiqueta_fin}:\n"
        return asm


class NodoWhile(NodoAST):
    def __init__(self, condicion, cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo

    def traducir_python(self):
        cuerpo = "\n    ".join(x.traducir_python() for x in self.cuerpo) or "pass"
        return f"while {self.condicion.traducir_python()}:\n    {cuerpo}"

    def traducir_lua(self):
        cuerpo = "\n  ".join(x.traducir_lua() for x in self.cuerpo)
        return f"while {self.condicion.traducir_lua()} do\n  {cuerpo}\nend"

    def to_dict(self):
        return {
            "tipo": "while",
            "condicion": self.condicion.to_dict(),
            "cuerpo": [x.to_dict() for x in self.cuerpo],
        }

    def traducir_asm(self, ctx):
        etiqueta_inicio = f"L_while_ini_{next(ctx['label_id'])}"
        etiqueta_fin = f"L_while_fin_{next(ctx['label_id'])}"

        asm = f"{etiqueta_inicio}:\n"
        asm += self.condicion.traducir_asm(ctx)
        asm += "    cmp rax, 0\n"
        asm += f"    je {etiqueta_fin}\n"
        for instr in self.cuerpo:
            asm += instr.traducir_asm(ctx)
        asm += f"    jmp {etiqueta_inicio}\n"
        asm += f"{etiqueta_fin}:\n"
        return asm


class NodoFor(NodoAST):
    def __init__(self, inicializacion, condicion, incremento, cuerpo):
        self.inicializacion = inicializacion
        self.condicion = condicion
        self.incremento = incremento
        self.cuerpo = cuerpo

    def traducir_python(self):
        cuerpo = "\n    ".join(x.traducir_python() for x in self.cuerpo)
        if cuerpo:
            cuerpo += "\n    " + self.incremento.traducir_python()
        else:
            cuerpo = self.incremento.traducir_python()
        return (
            f"{self.inicializacion.traducir_python()}\n"
            f"while {self.condicion.traducir_python()}:\n"
            f"    {cuerpo}"
        )

    def traducir_lua(self):
        cuerpo = "\n  ".join(x.traducir_lua() for x in self.cuerpo)
        return (
            f"{self.inicializacion.traducir_lua()}\n"
            f"while {self.condicion.traducir_lua()} do\n"
            f"  {cuerpo}\n"
            f"  {self.incremento.traducir_lua()}\n"
            "end"
        )

    def to_dict(self):
        return {
            "tipo": "for",
            "inicializacion": self.inicializacion.to_dict(),
            "condicion": self.condicion.to_dict(),
            "incremento": self.incremento.to_dict(),
            "cuerpo": [x.to_dict() for x in self.cuerpo],
        }

    def traducir_asm(self, ctx):
        etiqueta_inicio = f"L_for_ini_{next(ctx['label_id'])}"
        etiqueta_fin = f"L_for_fin_{next(ctx['label_id'])}"

        asm = self.inicializacion.traducir_asm(ctx)
        asm += f"{etiqueta_inicio}:\n"
        asm += self.condicion.traducir_asm(ctx)
        asm += "    cmp rax, 0\n"
        asm += f"    je {etiqueta_fin}\n"
        for instr in self.cuerpo:
            asm += instr.traducir_asm(ctx)
        asm += self.incremento.traducir_asm(ctx)
        asm += f"    jmp {etiqueta_inicio}\n"
        asm += f"{etiqueta_fin}:\n"
        return asm


class NodoReturn(NodoAST):
    def __init__(self, expresion):
        self.expresion = expresion

    def traducir_python(self):
        return f"return {self.expresion.traducir_python()}"

    def traducir_lua(self):
        return f"return {self.expresion.traducir_lua()}"

    def to_dict(self):
        return {"tipo": "return", "expresion": self.expresion.to_dict()}

    def traducir_asm(self, ctx):
        asm = self.expresion.traducir_asm(ctx)
        asm += f"    jmp {ctx['etiqueta_salida']}\n"
        return asm


class NodoParametro(NodoAST):
    def __init__(self, tipo, nombre):
        self.tipo = tipo
        self.nombre = nombre

    def traducir_python(self):
        return self.nombre

    def traducir_lua(self):
        return self.nombre

    def to_dict(self):
        return {"tipo": "parametro", "dato": self.tipo, "nombre": self.nombre}


class NodoFuncion(NodoAST):
    def __init__(self, tipo, nombre, parametros, cuerpo):
        self.tipo = tipo
        self.nombre = nombre
        self.parametros = parametros
        self.cuerpo = cuerpo

    def traducir_python(self):
        params = ", ".join(x.traducir_python() for x in self.parametros)
        cuerpo = "\n    ".join(x.traducir_python() for x in self.cuerpo) or "pass"
        return f"def {self.nombre}({params}):\n    {cuerpo}"

    def traducir_lua(self):
        params = ", ".join(x.traducir_lua() for x in self.parametros)
        cuerpo = "\n  ".join(x.traducir_lua() for x in self.cuerpo)
        return f"function {self.nombre}({params})\n  {cuerpo}\nend"

    def to_dict(self):
        return {
            "tipo": "funcion",
            "nombre": self.nombre,
            "retorno": self.tipo,
            "parametros": [x.to_dict() for x in self.parametros],
            "cuerpo": [x.to_dict() for x in self.cuerpo],
        }

    def traducir_asm(self, ctx):
        ctx["etiqueta_salida"] = "L_programa_fin"
        cuerpo = ""
        for instr in self.cuerpo:
            cuerpo += instr.traducir_asm(ctx)

        asm = "global _start\n"
        asm += "_start:\n"
        asm += cuerpo
        asm += "    mov rax, 0\n"
        asm += f"{ctx['etiqueta_salida']}:\n"
        asm += "    mov rdi, rax\n"
        asm += "    mov rax, 60\n"
        asm += "    syscall\n"
        return asm


class Parser:
    OPS_BINARIOS = {"+", "-", "*", "/", "==", "<", ">", "<=", ">="}

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def actual(self):
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def ver(self, tipo=None, valor=None):
        tok = self.actual()
        if tok is None:
            return False
        if tipo is not None and tok[0] != tipo:
            return False
        if valor is not None and tok[1] != valor:
            return False
        return True

    def consumir(self, tipo=None, valor=None):
        tok = self.actual()
        if tok is None:
            raise SyntaxError("Fin de entrada inesperado")
        if tipo is not None and tok[0] != tipo:
            raise SyntaxError(f"Se esperaba tipo {tipo} y se encontro {tok}")
        if valor is not None and tok[1] != valor:
            raise SyntaxError(f"Se esperaba '{valor}' y se encontro {tok}")
        self.pos += 1
        return tok

    def parsear(self):
        return self.parsear_funcion()

    def parsear_funcion(self):
        tipo = self.consumir("KEYWORD")[1]
        nombre = self.consumir("IDENTIFIER")[1]
        self.consumir("DELIMITER", "(")
        parametros = self.parsear_parametros()
        self.consumir("DELIMITER", ")")
        self.consumir("DELIMITER", "{")
        cuerpo = self.parsear_bloque()
        self.consumir("DELIMITER", "}")
        return NodoFuncion(tipo, nombre, parametros, cuerpo)

    def parsear_parametros(self):
        params = []
        if self.ver("DELIMITER", ")"):
            return params
        while True:
            tipo = self.consumir("KEYWORD")[1]
            nombre = self.consumir("IDENTIFIER")[1]
            params.append(NodoParametro(tipo, nombre))
            if self.ver("DELIMITER", ","):
                self.consumir("DELIMITER", ",")
                continue
            break
        return params

    def parsear_bloque(self):
        instrucciones = []
        while self.actual() and not self.ver("DELIMITER", "}"):
            instrucciones.append(self.parsear_instruccion())
        return instrucciones

    def parsear_instruccion(self):
        tok = self.actual()
        if tok is None:
            raise SyntaxError("Instruccion inesperada al final")

        if self.ver("KEYWORD", "return"):
            self.consumir("KEYWORD", "return")
            expr = self.parsear_expresion()
            self.consumir("DELIMITER", ";")
            return NodoReturn(expr)

        if self.ver("KEYWORD", "print") or self.ver("KEYWORD", "println"):
            return self.parsear_print()

        if self.ver("KEYWORD", "if"):
            return self.parsear_if()

        if self.ver("KEYWORD", "while"):
            return self.parsear_while()

        if self.ver("KEYWORD", "for"):
            return self.parsear_for()

        if tok[0] == "KEYWORD":
            return self.parsear_declaracion(requiere_pyc=True)

        if tok[0] == "IDENTIFIER":
            nodo = self.parsear_asignacion(requiere_pyc=True)
            return nodo

        raise SyntaxError(f"Instruccion no reconocida: {tok}")

    def parsear_print(self):
        comando = self.consumir("KEYWORD")[1]
        salto = comando == "println"
        self.consumir("DELIMITER", "(")
        args = []
        if not self.ver("DELIMITER", ")"):
            while True:
                args.append(self.parsear_expresion())
                if self.ver("DELIMITER", ","):
                    self.consumir("DELIMITER", ",")
                    continue
                break
        self.consumir("DELIMITER", ")")
        self.consumir("DELIMITER", ";")
        return NodoPrint(args, salto)

    def parsear_if(self):
        self.consumir("KEYWORD", "if")
        self.consumir("DELIMITER", "(")
        condicion = self.parsear_expresion()
        self.consumir("DELIMITER", ")")
        self.consumir("DELIMITER", "{")
        cuerpo_if = self.parsear_bloque()
        self.consumir("DELIMITER", "}")

        cuerpo_else = []
        if self.ver("KEYWORD", "else"):
            self.consumir("KEYWORD", "else")
            self.consumir("DELIMITER", "{")
            cuerpo_else = self.parsear_bloque()
            self.consumir("DELIMITER", "}")

        return NodoIf(condicion, cuerpo_if, cuerpo_else)

    def parsear_while(self):
        self.consumir("KEYWORD", "while")
        self.consumir("DELIMITER", "(")
        condicion = self.parsear_expresion()
        self.consumir("DELIMITER", ")")
        self.consumir("DELIMITER", "{")
        cuerpo = self.parsear_bloque()
        self.consumir("DELIMITER", "}")
        return NodoWhile(condicion, cuerpo)

    def parsear_for(self):
        self.consumir("KEYWORD", "for")
        self.consumir("DELIMITER", "(")

        if self.actual()[0] == "KEYWORD":
            inicializacion = self.parsear_declaracion(requiere_pyc=False)
        else:
            inicializacion = self.parsear_asignacion(requiere_pyc=False)
        self.consumir("DELIMITER", ";")

        condicion = self.parsear_expresion()
        self.consumir("DELIMITER", ";")

        incremento = self.parsear_asignacion(requiere_pyc=False)
        self.consumir("DELIMITER", ")")

        self.consumir("DELIMITER", "{")
        cuerpo = self.parsear_bloque()
        self.consumir("DELIMITER", "}")

        return NodoFor(inicializacion, condicion, incremento, cuerpo)

    def parsear_declaracion(self, requiere_pyc):
        tipo = self.consumir("KEYWORD")[1]
        nombre = self.consumir("IDENTIFIER")[1]
        self.consumir("OPERATOR", "=")
        expr = self.parsear_expresion()
        if requiere_pyc:
            self.consumir("DELIMITER", ";")
        return NodoDeclaracion(tipo, nombre, expr)

    def parsear_asignacion(self, requiere_pyc):
        nombre = self.consumir("IDENTIFIER")[1]
        self.consumir("OPERATOR", "=")
        expr = self.parsear_expresion()
        if requiere_pyc:
            self.consumir("DELIMITER", ";")
        return NodoAsignacion(nombre, expr)

    def parsear_expresion(self):
        izquierda = self.parsear_primario()
        while self.actual() and self.actual()[0] == "OPERATOR" and self.actual()[1] in self.OPS_BINARIOS:
            op = self.consumir("OPERATOR")[1]
            derecha = self.parsear_primario()
            izquierda = NodoOperacion(izquierda, op, derecha)
        return izquierda

    def parsear_primario(self):
        tok = self.actual()
        if tok is None:
            raise SyntaxError("Expresion incompleta")
        if tok[0] == "NUMBER":
            return NodoNumero(self.consumir("NUMBER"))
        if tok[0] == "STRING":
            return NodoString(self.consumir("STRING"))
        if tok[0] == "IDENTIFIER":
            return NodoIdentificador(self.consumir("IDENTIFIER"))
        if tok[0] == "DELIMITER" and tok[1] == "(":
            self.consumir("DELIMITER", "(")
            expr = self.parsear_expresion()
            self.consumir("DELIMITER", ")")
            return expr
        raise SyntaxError(f"Token inesperado en expresion: {tok}")


def crear_contexto_asm():
    return {
        "data": [],
        "bss": set(),
        "string_id": itertools.count(),
        "label_id": itertools.count(),
        "etiqueta_salida": "",
    }
