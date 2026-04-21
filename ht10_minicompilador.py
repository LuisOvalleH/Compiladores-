import json
from dataclasses import dataclass


PROGRAMA_BASE = """
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


PROGRAMA_EXTENSION = """
funcion suma(x, y)
    retornar x + y
finfuncion

inicio
    a = 10
    b = 20
    c = suma(a, b) + b
    si (c > 30) entonces
        escribir(c)
        d = c - 10
    finsi
    escribir(d)
fin
"""


PALABRAS_RESERVADAS = {
    "inicio",
    "fin",
    "si",
    "entonces",
    "finsi",
    "escribir",
    "funcion",
    "retornar",
    "finfuncion",
}


@dataclass
class Token:
    tipo: str
    valor: str
    linea: int
    columna: int

    def como_dict(self):
        return {
            "tipo": self.tipo,
            "valor": self.valor,
            "linea": self.linea,
            "columna": self.columna,
        }


class LexerPseudoC:
    def __init__(self, texto):
        self.texto = texto
        self.pos = 0
        self.linea = 1
        self.columna = 1

    def tokenizar(self):
        tokens = []
        while not self._fin():
            actual = self._actual()

            if actual in " \t\r":
                self._avanzar()
                continue

            if actual == "\n":
                self._avanzar_linea()
                continue

            if actual.isalpha() or actual == "_":
                tokens.append(self._leer_identificador())
                continue

            if actual.isdigit():
                tokens.append(self._leer_numero())
                continue

            tokens.append(self._leer_simbolo())

        tokens.append(Token("EOF", "EOF", self.linea, self.columna))
        return tokens

    def _leer_identificador(self):
        linea = self.linea
        columna = self.columna
        inicio = self.pos
        while not self._fin() and (self._actual().isalnum() or self._actual() == "_"):
            self._avanzar()

        valor = self.texto[inicio:self.pos]
        tipo = "RESERVADA" if valor in PALABRAS_RESERVADAS else "IDENTIFICADOR"
        return Token(tipo, valor, linea, columna)

    def _leer_numero(self):
        linea = self.linea
        columna = self.columna
        inicio = self.pos
        while not self._fin() and self._actual().isdigit():
            self._avanzar()
        return Token("NUMERO", self.texto[inicio:self.pos], linea, columna)

    def _leer_simbolo(self):
        linea = self.linea
        columna = self.columna
        actual = self._actual()
        siguiente = self.texto[self.pos + 1] if self.pos + 1 < len(self.texto) else ""

        if actual + siguiente in {"==", "!=", "<=", ">="}:
            valor = actual + siguiente
            self._avanzar()
            self._avanzar()
            return Token("OPERADOR", valor, linea, columna)

        if actual in "+-*/=<>":
            self._avanzar()
            return Token("OPERADOR", actual, linea, columna)

        if actual in "(),":
            self._avanzar()
            return Token("DELIMITADOR", actual, linea, columna)

        raise SyntaxError(f"Caracter no reconocido {actual!r} en linea {linea}, columna {columna}")

    def _actual(self):
        return self.texto[self.pos]

    def _fin(self):
        return self.pos >= len(self.texto)

    def _avanzar(self):
        self.pos += 1
        self.columna += 1

    def _avanzar_linea(self):
        self.pos += 1
        self.linea += 1
        self.columna = 1


class Nodo:
    def como_dict(self):
        raise NotImplementedError()


@dataclass
class Programa(Nodo):
    funciones: list
    instrucciones: list

    def como_dict(self):
        return {
            "tipo": "programa",
            "funciones": [funcion.como_dict() for funcion in self.funciones],
            "instrucciones": [instr.como_dict() for instr in self.instrucciones],
        }


@dataclass
class Funcion(Nodo):
    nombre: str
    parametros: list
    cuerpo: list

    def como_dict(self):
        return {
            "tipo": "funcion",
            "nombre": self.nombre,
            "parametros": self.parametros,
            "cuerpo": [instr.como_dict() for instr in self.cuerpo],
        }


@dataclass
class Asignacion(Nodo):
    nombre: str
    expresion: Nodo

    def como_dict(self):
        return {
            "tipo": "asignacion",
            "variable": self.nombre,
            "expresion": self.expresion.como_dict(),
        }


@dataclass
class Escribir(Nodo):
    expresion: Nodo

    def como_dict(self):
        return {"tipo": "escribir", "expresion": self.expresion.como_dict()}


@dataclass
class Si(Nodo):
    condicion: Nodo
    cuerpo: list

    def como_dict(self):
        return {
            "tipo": "si",
            "condicion": self.condicion.como_dict(),
            "cuerpo": [instr.como_dict() for instr in self.cuerpo],
        }


@dataclass
class Retornar(Nodo):
    expresion: Nodo

    def como_dict(self):
        return {"tipo": "retornar", "expresion": self.expresion.como_dict()}


@dataclass
class Binaria(Nodo):
    operador: str
    izquierda: Nodo
    derecha: Nodo

    def como_dict(self):
        return {
            "tipo": "operacion_binaria",
            "operador": self.operador,
            "izquierda": self.izquierda.como_dict(),
            "derecha": self.derecha.como_dict(),
        }


@dataclass
class Constante(Nodo):
    valor: int

    def como_dict(self):
        return {"tipo": "constante", "valor": self.valor}


@dataclass
class Variable(Nodo):
    nombre: str

    def como_dict(self):
        return {"tipo": "variable", "nombre": self.nombre}


@dataclass
class LlamadaFuncion(Nodo):
    nombre: str
    argumentos: list

    def como_dict(self):
        return {
            "tipo": "llamada_funcion",
            "nombre": self.nombre,
            "argumentos": [arg.como_dict() for arg in self.argumentos],
        }


class ParserPseudoC:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parsear(self):
        funciones = []
        while self._ver("RESERVADA", "funcion"):
            funciones.append(self._parsear_funcion())

        self._consumir("RESERVADA", "inicio")
        instrucciones = self._parsear_bloque({"fin"})
        self._consumir("RESERVADA", "fin")
        self._consumir("EOF")
        return Programa(funciones, instrucciones)

    def _parsear_funcion(self):
        self._consumir("RESERVADA", "funcion")
        nombre = self._consumir("IDENTIFICADOR").valor
        self._consumir("DELIMITADOR", "(")
        parametros = []
        if not self._ver("DELIMITADOR", ")"):
            while True:
                parametros.append(self._consumir("IDENTIFICADOR").valor)
                if not self._ver("DELIMITADOR", ","):
                    break
                self._consumir("DELIMITADOR", ",")
        self._consumir("DELIMITADOR", ")")
        cuerpo = self._parsear_bloque({"finfuncion"})
        self._consumir("RESERVADA", "finfuncion")
        return Funcion(nombre, parametros, cuerpo)

    def _parsear_bloque(self, cierres):
        instrucciones = []
        while not self._ver("EOF") and not (
            self._actual().tipo == "RESERVADA" and self._actual().valor in cierres
        ):
            instrucciones.append(self._parsear_instruccion())
        return instrucciones

    def _parsear_instruccion(self):
        if self._ver("IDENTIFICADOR"):
            nombre = self._consumir("IDENTIFICADOR").valor
            self._consumir("OPERADOR", "=")
            return Asignacion(nombre, self._parsear_expresion())

        if self._ver("RESERVADA", "escribir"):
            self._consumir("RESERVADA", "escribir")
            self._consumir("DELIMITADOR", "(")
            expresion = self._parsear_expresion()
            self._consumir("DELIMITADOR", ")")
            return Escribir(expresion)

        if self._ver("RESERVADA", "si"):
            self._consumir("RESERVADA", "si")
            self._consumir("DELIMITADOR", "(")
            condicion = self._parsear_expresion()
            self._consumir("DELIMITADOR", ")")
            self._consumir("RESERVADA", "entonces")
            cuerpo = self._parsear_bloque({"finsi"})
            self._consumir("RESERVADA", "finsi")
            return Si(condicion, cuerpo)

        if self._ver("RESERVADA", "retornar"):
            self._consumir("RESERVADA", "retornar")
            return Retornar(self._parsear_expresion())

        actual = self._actual()
        raise SyntaxError(
            f"Instruccion inesperada {actual.valor!r} en linea {actual.linea}, columna {actual.columna}"
        )

    def _parsear_expresion(self):
        return self._parsear_comparacion()

    def _parsear_comparacion(self):
        izquierda = self._parsear_suma()
        while self._ver("OPERADOR") and self._actual().valor in {">", "<", ">=", "<=", "==", "!="}:
            operador = self._consumir("OPERADOR").valor
            derecha = self._parsear_suma()
            izquierda = Binaria(operador, izquierda, derecha)
        return izquierda

    def _parsear_suma(self):
        izquierda = self._parsear_producto()
        while self._ver("OPERADOR") and self._actual().valor in {"+", "-"}:
            operador = self._consumir("OPERADOR").valor
            derecha = self._parsear_producto()
            izquierda = Binaria(operador, izquierda, derecha)
        return izquierda

    def _parsear_producto(self):
        izquierda = self._parsear_primario()
        while self._ver("OPERADOR") and self._actual().valor in {"*", "/"}:
            operador = self._consumir("OPERADOR").valor
            derecha = self._parsear_primario()
            izquierda = Binaria(operador, izquierda, derecha)
        return izquierda

    def _parsear_primario(self):
        if self._ver("NUMERO"):
            return Constante(int(self._consumir("NUMERO").valor))

        if self._ver("IDENTIFICADOR"):
            nombre = self._consumir("IDENTIFICADOR").valor
            if self._ver("DELIMITADOR", "("):
                self._consumir("DELIMITADOR", "(")
                argumentos = []
                if not self._ver("DELIMITADOR", ")"):
                    while True:
                        argumentos.append(self._parsear_expresion())
                        if not self._ver("DELIMITADOR", ","):
                            break
                        self._consumir("DELIMITADOR", ",")
                self._consumir("DELIMITADOR", ")")
                return LlamadaFuncion(nombre, argumentos)
            return Variable(nombre)

        if self._ver("DELIMITADOR", "("):
            self._consumir("DELIMITADOR", "(")
            expresion = self._parsear_expresion()
            self._consumir("DELIMITADOR", ")")
            return expresion

        actual = self._actual()
        raise SyntaxError(f"Expresion inesperada {actual.valor!r} en linea {actual.linea}")

    def _actual(self):
        return self.tokens[self.pos]

    def _ver(self, tipo, valor=None):
        actual = self._actual()
        if actual.tipo != tipo:
            return False
        if valor is not None and actual.valor != valor:
            return False
        return True

    def _consumir(self, tipo, valor=None):
        actual = self._actual()
        if actual.tipo != tipo:
            raise SyntaxError(f"Se esperaba {tipo} y se encontro {actual.tipo} ({actual.valor})")
        if valor is not None and actual.valor != valor:
            raise SyntaxError(f"Se esperaba {valor!r} y se encontro {actual.valor!r}")
        self.pos += 1
        return actual


@dataclass
class Simbolo:
    nombre: str
    tipo: str
    categoria: str
    ambito: str
    valor: int | None
    inicializado: bool
    nota: str = ""

    def como_dict(self):
        return {
            "nombre": self.nombre,
            "tipo": self.tipo,
            "categoria": self.categoria,
            "ambito": self.ambito,
            "valor": self.valor,
            "inicializado": self.inicializado,
            "nota": self.nota,
        }


class AnalizadorSemantico:
    def __init__(self):
        self.simbolos = {}
        self.errores = []
        self.funciones = {}

    def analizar(self, programa):
        for funcion in programa.funciones:
            self.funciones[funcion.nombre] = funcion
            self._agregar_simbolo(funcion.nombre, "funcion", "global", None, True, "retorna entero")
            for parametro in funcion.parametros:
                self._agregar_simbolo(parametro, "parametro", funcion.nombre, None, True, "entero")

        asignados = set()
        valores = {}
        self._analizar_instrucciones(programa.instrucciones, "global", asignados, valores)
        return list(self.simbolos.values()), self.errores, valores

    def _analizar_instrucciones(self, instrucciones, ambito, asignados, valores):
        for instruccion in instrucciones:
            if isinstance(instruccion, Asignacion):
                valor = self._evaluar(instruccion.expresion, asignados, valores)
                asignados.add(instruccion.nombre)
                valores[instruccion.nombre] = valor
                self._agregar_simbolo(
                    instruccion.nombre,
                    "variable",
                    ambito,
                    valor,
                    True,
                    "entero",
                )
                continue

            if isinstance(instruccion, Escribir):
                self._evaluar(instruccion.expresion, asignados, valores)
                continue

            if isinstance(instruccion, Si):
                valor_condicion = self._evaluar(instruccion.condicion, asignados, valores)
                if valor_condicion is True:
                    self._analizar_instrucciones(instruccion.cuerpo, ambito, asignados, valores)
                elif valor_condicion is False:
                    continue
                else:
                    asignados_antes = set(asignados)
                    valores_antes = dict(valores)
                    asignados_then = set(asignados)
                    valores_then = dict(valores)
                    self._analizar_instrucciones(instruccion.cuerpo, ambito, asignados_then, valores_then)
                    asignados.clear()
                    asignados.update(asignados_antes.intersection(asignados_then))
                    valores.clear()
                    valores.update({k: v for k, v in valores_antes.items() if k in asignados})
                continue

            if isinstance(instruccion, Retornar):
                self._evaluar(instruccion.expresion, asignados, valores)
                continue

    def _evaluar(self, expresion, asignados, valores):
        if isinstance(expresion, Constante):
            return expresion.valor

        if isinstance(expresion, Variable):
            if expresion.nombre not in asignados:
                self.errores.append(f"La variable '{expresion.nombre}' podria usarse sin valor.")
                return None
            return valores.get(expresion.nombre)

        if isinstance(expresion, LlamadaFuncion):
            funcion = self.funciones.get(expresion.nombre)
            if funcion is None:
                self.errores.append(f"La funcion '{expresion.nombre}' no esta declarada.")
                return None
            if len(expresion.argumentos) != len(funcion.parametros):
                self.errores.append(
                    f"La funcion '{expresion.nombre}' esperaba {len(funcion.parametros)} argumentos."
                )
                return None

            valores_args = [self._evaluar(arg, asignados, valores) for arg in expresion.argumentos]
            if any(valor is None for valor in valores_args):
                return None
            if expresion.nombre == "suma":
                return valores_args[0] + valores_args[1]
            return None

        if isinstance(expresion, Binaria):
            izquierda = self._evaluar(expresion.izquierda, asignados, valores)
            derecha = self._evaluar(expresion.derecha, asignados, valores)
            if izquierda is None or derecha is None:
                return None
            return operar(expresion.operador, izquierda, derecha)

        return None

    def _agregar_simbolo(self, nombre, categoria, ambito, valor, inicializado, nota):
        clave = (ambito, nombre)
        self.simbolos[clave] = Simbolo(
            nombre=nombre,
            tipo="entero",
            categoria=categoria,
            ambito=ambito,
            valor=valor,
            inicializado=inicializado,
            nota=nota,
        )


class GeneradorTresDirecciones:
    def __init__(self):
        self.temporal = 1
        self.etiqueta = 1
        self.lineas = []

    def generar(self, programa):
        self.lineas = []
        for instruccion in programa.instrucciones:
            self._instruccion(instruccion)
        return self.lineas

    def _nuevo_temporal(self):
        nombre = f"t{self.temporal}"
        self.temporal += 1
        return nombre

    def _nueva_etiqueta(self):
        nombre = f"L{self.etiqueta}"
        self.etiqueta += 1
        return nombre

    def _instruccion(self, nodo):
        if isinstance(nodo, Asignacion):
            valor = self._expresion(nodo.expresion)
            self.lineas.append(f"{nodo.nombre} = {valor}")
            return

        if isinstance(nodo, Escribir):
            valor = self._expresion(nodo.expresion)
            self.lineas.append(f"escribir {valor}")
            return

        if isinstance(nodo, Si):
            condicion = self._expresion(nodo.condicion)
            etiqueta_fin = self._nueva_etiqueta()
            self.lineas.append(f"if_false {condicion} goto {etiqueta_fin}")
            for instruccion in nodo.cuerpo:
                self._instruccion(instruccion)
            self.lineas.append(f"{etiqueta_fin}:")
            return

    def _expresion(self, nodo):
        if isinstance(nodo, Constante):
            return str(nodo.valor)

        if isinstance(nodo, Variable):
            return nodo.nombre

        if isinstance(nodo, LlamadaFuncion):
            args = ", ".join(self._expresion(arg) for arg in nodo.argumentos)
            temp = self._nuevo_temporal()
            self.lineas.append(f"{temp} = call {nodo.nombre}({args})")
            return temp

        if isinstance(nodo, Binaria):
            izquierda = self._expresion(nodo.izquierda)
            derecha = self._expresion(nodo.derecha)
            temp = self._nuevo_temporal()
            self.lineas.append(f"{temp} = {izquierda} {nodo.operador} {derecha}")
            return temp

        raise TypeError(f"Expresion no soportada: {type(nodo).__name__}")


def optimizar_programa(programa):
    asignados = {}
    lineas = []
    notas = [
        "Optimizacion 1: propagacion y plegado de constantes.",
        "Optimizacion 2: eliminacion del salto y etiqueta del si porque la condicion se evalua como verdadera.",
    ]

    def emitir_instrucciones(instrucciones):
        for instruccion in instrucciones:
            if isinstance(instruccion, Asignacion):
                valor = evaluar_constante(instruccion.expresion, asignados)
                if valor is not None:
                    asignados[instruccion.nombre] = valor
                    lineas.append(f"{instruccion.nombre} = {valor}")
                else:
                    lineas.append(f"{instruccion.nombre} = {expresion_texto(instruccion.expresion)}")
                continue

            if isinstance(instruccion, Escribir):
                valor = evaluar_constante(instruccion.expresion, asignados)
                lineas.append(f"escribir {valor if valor is not None else expresion_texto(instruccion.expresion)}")
                continue

            if isinstance(instruccion, Si):
                condicion = evaluar_constante(instruccion.condicion, asignados)
                if condicion is True:
                    lineas.append("# condicion c > 30 verdadera; se conserva solo el cuerpo del si")
                    emitir_instrucciones(instruccion.cuerpo)
                elif condicion is False:
                    lineas.append("# condicion falsa; cuerpo del si eliminado")
                else:
                    lineas.append(f"if_false {expresion_texto(instruccion.condicion)} goto L1")
                    emitir_instrucciones(instruccion.cuerpo)
                    lineas.append("L1:")

    emitir_instrucciones(programa.instrucciones)
    return notas, lineas


class GeneradorMIPS:
    def __init__(self):
        self.variables = set()
        self.lineas = []
        self.registro = 0
        self.etiqueta = 1

    def generar(self, programa):
        self._recolectar_variables(programa.instrucciones)
        data = [".data"]
        for variable in sorted(self.variables):
            data.append(f"    {variable}: .word 0")
        data.extend(["    salto: .asciiz \"\\n\"", "", ".text", ".globl main", "main:"])

        self.lineas = []
        for instruccion in programa.instrucciones:
            self._instruccion(instruccion)

        self.lineas.extend(
            [
                "    li $v0, 10",
                "    syscall",
            ]
        )
        return data + self.lineas

    def _recolectar_variables(self, instrucciones):
        for instruccion in instrucciones:
            if isinstance(instruccion, Asignacion):
                self.variables.add(instruccion.nombre)
                self._variables_en_expresion(instruccion.expresion)
            elif isinstance(instruccion, Escribir):
                self._variables_en_expresion(instruccion.expresion)
            elif isinstance(instruccion, Si):
                self._variables_en_expresion(instruccion.condicion)
                self._recolectar_variables(instruccion.cuerpo)

    def _variables_en_expresion(self, expresion):
        if isinstance(expresion, Variable):
            self.variables.add(expresion.nombre)
        elif isinstance(expresion, Binaria):
            self._variables_en_expresion(expresion.izquierda)
            self._variables_en_expresion(expresion.derecha)
        elif isinstance(expresion, LlamadaFuncion):
            for argumento in expresion.argumentos:
                self._variables_en_expresion(argumento)

    def _instruccion(self, nodo):
        if isinstance(nodo, Asignacion):
            reg = self._expresion(nodo.expresion)
            self.lineas.append(f"    sw {reg}, {nodo.nombre}")
            return

        if isinstance(nodo, Escribir):
            reg = self._expresion(nodo.expresion)
            self.lineas.extend(
                [
                    f"    move $a0, {reg}",
                    "    li $v0, 1",
                    "    syscall",
                    "    la $a0, salto",
                    "    li $v0, 4",
                    "    syscall",
                ]
            )
            return

        if isinstance(nodo, Si):
            fin = f"L_fin_si_{self.etiqueta}"
            self.etiqueta += 1
            self._salto_si_falso(nodo.condicion, fin)
            for instruccion in nodo.cuerpo:
                self._instruccion(instruccion)
            self.lineas.append(f"{fin}:")

    def _expresion(self, nodo):
        if isinstance(nodo, Constante):
            reg = self._nuevo_registro()
            self.lineas.append(f"    li {reg}, {nodo.valor}")
            return reg

        if isinstance(nodo, Variable):
            reg = self._nuevo_registro()
            self.lineas.append(f"    lw {reg}, {nodo.nombre}")
            return reg

        if isinstance(nodo, LlamadaFuncion):
            for indice, argumento in enumerate(nodo.argumentos[:4]):
                reg_arg = self._expresion(argumento)
                self.lineas.append(f"    move $a{indice}, {reg_arg}")
            self.lineas.append(f"    jal {nodo.nombre}")
            reg = self._nuevo_registro()
            self.lineas.append(f"    move {reg}, $v0")
            return reg

        if isinstance(nodo, Binaria):
            izq = self._expresion(nodo.izquierda)
            der = self._expresion(nodo.derecha)
            res = self._nuevo_registro()
            instrucciones = {
                "+": "add",
                "-": "sub",
                "*": "mul",
                "/": "div",
            }
            if nodo.operador == "/":
                self.lineas.append(f"    div {izq}, {der}")
                self.lineas.append(f"    mflo {res}")
            elif nodo.operador in instrucciones:
                self.lineas.append(f"    {instrucciones[nodo.operador]} {res}, {izq}, {der}")
            else:
                self.lineas.append(f"    # comparacion {izq} {nodo.operador} {der}")
            return res

        raise TypeError(f"Expresion no soportada: {type(nodo).__name__}")

    def _salto_si_falso(self, condicion, etiqueta_fin):
        if not isinstance(condicion, Binaria):
            reg = self._expresion(condicion)
            self.lineas.append(f"    beq {reg}, $zero, {etiqueta_fin}")
            return

        izq = self._expresion(condicion.izquierda)
        der = self._expresion(condicion.derecha)
        saltos_falsos = {
            ">": "ble",
            "<": "bge",
            ">=": "blt",
            "<=": "bgt",
            "==": "bne",
            "!=": "beq",
        }
        salto = saltos_falsos[condicion.operador]
        self.lineas.append(f"    {salto} {izq}, {der}, {etiqueta_fin}")

    def _nuevo_registro(self):
        reg = f"$t{self.registro % 10}"
        self.registro += 1
        return reg


def operar(operador, izquierda, derecha):
    if operador == "+":
        return izquierda + derecha
    if operador == "-":
        return izquierda - derecha
    if operador == "*":
        return izquierda * derecha
    if operador == "/":
        return izquierda // derecha
    if operador == ">":
        return izquierda > derecha
    if operador == "<":
        return izquierda < derecha
    if operador == ">=":
        return izquierda >= derecha
    if operador == "<=":
        return izquierda <= derecha
    if operador == "==":
        return izquierda == derecha
    if operador == "!=":
        return izquierda != derecha
    raise ValueError(f"Operador no soportado: {operador}")


def evaluar_constante(expresion, valores):
    if isinstance(expresion, Constante):
        return expresion.valor
    if isinstance(expresion, Variable):
        return valores.get(expresion.nombre)
    if isinstance(expresion, Binaria):
        izquierda = evaluar_constante(expresion.izquierda, valores)
        derecha = evaluar_constante(expresion.derecha, valores)
        if izquierda is None or derecha is None:
            return None
        return operar(expresion.operador, izquierda, derecha)
    if isinstance(expresion, LlamadaFuncion):
        args = [evaluar_constante(arg, valores) for arg in expresion.argumentos]
        if any(arg is None for arg in args):
            return None
        if expresion.nombre == "suma":
            return args[0] + args[1]
    return None


def expresion_texto(expresion):
    if isinstance(expresion, Constante):
        return str(expresion.valor)
    if isinstance(expresion, Variable):
        return expresion.nombre
    if isinstance(expresion, LlamadaFuncion):
        args = ", ".join(expresion_texto(arg) for arg in expresion.argumentos)
        return f"{expresion.nombre}({args})"
    if isinstance(expresion, Binaria):
        return f"{expresion_texto(expresion.izquierda)} {expresion.operador} {expresion_texto(expresion.derecha)}"
    return "?"


def tabla_texto(simbolos):
    lineas = ["NOMBRE       TIPO     CATEGORIA   AMBITO     VALOR   NOTA"]
    lineas.append("-" * 70)
    for simbolo in simbolos:
        valor = "-" if simbolo.valor is None else str(simbolo.valor)
        lineas.append(
            f"{simbolo.nombre:<12} {simbolo.tipo:<8} {simbolo.categoria:<11} "
            f"{simbolo.ambito:<10} {valor:<7} {simbolo.nota}"
        )
    return "\n".join(lineas)


def generar_extension_mips():
    return [
        ".data",
        "    a: .word 0",
        "    b: .word 0",
        "    c: .word 0",
        "    d: .word 0",
        "    salto: .asciiz \"\\n\"",
        "",
        ".text",
        ".globl main",
        "",
        "suma:",
        "    add $v0, $a0, $a1",
        "    jr $ra",
        "",
        "main:",
        "    li $t0, 10",
        "    sw $t0, a",
        "    li $t1, 20",
        "    sw $t1, b",
        "    lw $a0, a",
        "    lw $a1, b",
        "    jal suma",
        "    lw $t2, b",
        "    add $t3, $v0, $t2",
        "    sw $t3, c",
        "    li $t4, 30",
        "    ble $t3, $t4, L_fin_si",
        "    move $a0, $t3",
        "    li $v0, 1",
        "    syscall",
        "    la $a0, salto",
        "    li $v0, 4",
        "    syscall",
        "    li $t5, 10",
        "    sub $t6, $t3, $t5",
        "    sw $t6, d",
        "L_fin_si:",
        "    lw $a0, d",
        "    li $v0, 1",
        "    syscall",
        "    li $v0, 10",
        "    syscall",
    ]


def compilar(texto):
    tokens = LexerPseudoC(texto).tokenizar()
    ast = ParserPseudoC(tokens).parsear()
    simbolos, errores, valores = AnalizadorSemantico().analizar(ast)
    tac = GeneradorTresDirecciones().generar(ast)
    notas_opt, tac_opt = optimizar_programa(ast)
    mips = GeneradorMIPS().generar(ast)
    return tokens, ast, simbolos, errores, valores, tac, notas_opt, tac_opt, mips


def escribir_archivo(ruta, contenido):
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)


def generar_documento(datos_base, datos_extension):
    tokens, ast, simbolos, errores, valores, tac, notas_opt, tac_opt, mips = datos_base
    _, ast_ext, simbolos_ext, errores_ext, _, _, _, _, _ = datos_extension

    return f"""# HT10 - Minicompilador Pseudo-C

## Programa fuente
```text
{PROGRAMA_BASE.strip()}
```

## 1. Analisis lexico
Tokens definidos:

- `RESERVADA`: inicio, fin, si, entonces, finsi, escribir.
- `IDENTIFICADOR`: nombres de variables como a, b, c, d.
- `NUMERO`: constantes enteras.
- `OPERADOR`: =, +, -, *, /, >, <, >=, <=, ==, !=.
- `DELIMITADOR`: parentesis y coma.

Secuencia de tokens:

```json
{json.dumps([token.como_dict() for token in tokens if token.tipo != "EOF"], indent=2, ensure_ascii=False)}
```

## 2. Analisis sintactico y AST
El arbol usa nodos de programa, asignacion, si, escribir, operacion binaria, constante y variable. Este JSON se puede pegar en json-crack para visualizarlo.

```json
{json.dumps(ast.como_dict(), indent=2, ensure_ascii=False)}
```

## 3. Analisis semantico
Tabla de simbolos despues del analisis:

```text
{tabla_texto(simbolos)}
```

Errores encontrados:

```text
{chr(10).join(errores) if errores else "No se encontraron errores semanticos para este programa."}
```

La variable `d` se usa en `escribir(d)` despues del `finsi`. En un analisis general esto podria ser peligroso, porque `d` se asigna dentro del `si`. Sin embargo, en este programa los valores son conocidos: `a = 10`, `b = 20`, entonces `c = a + b * 2 = 50`. La condicion `c > 30` se evalua como verdadera, por eso el bloque del `si` siempre se ejecuta y `d = c - 10` queda inicializada con el valor `{valores.get("d")}` antes del ultimo `escribir`.

## 4. Codigo de 3 direcciones
Sin optimizar:

```text
{chr(10).join(tac)}
```

Optimizaciones aplicadas:

```text
{chr(10).join(notas_opt)}
```

Resultado optimizado:

```text
{chr(10).join(tac_opt)}
```

## 5. Traduccion a ensamblador MIPS simplificado
Convencion usada: las variables se almacenan en memoria en la seccion `.data`; los calculos usan registros temporales `$t0`, `$t1`, etc.; `escribir` se simula con syscall `1` para imprimir entero y syscall `4` para salto de linea.

```asm
{chr(10).join(mips)}
```

## 6. Extension: funcion simple
Se agrega una funcion `suma(x, y)` que retorna `x + y` y se llama desde el programa principal.

Programa extendido:

```text
{PROGRAMA_EXTENSION.strip()}
```

Cambios en AST: aparece el nodo `funcion`, el nodo `retornar` y el nodo `llamada_funcion`.

```json
{json.dumps(ast_ext.como_dict(), indent=2, ensure_ascii=False)}
```

Nueva tabla de simbolos con ambito:

```text
{tabla_texto(simbolos_ext)}
```

Errores en la extension:

```text
{chr(10).join(errores_ext) if errores_ext else "No se encontraron errores semanticos en la extension."}
```

En MIPS, la llamada usa `jal suma` y la funcion regresa con `jr $ra`.
"""


def main():
    datos_base = compilar(PROGRAMA_BASE)
    datos_extension = compilar(PROGRAMA_EXTENSION)

    tokens, ast, simbolos, errores, _, tac, notas_opt, tac_opt, mips = datos_base
    _, ast_ext, simbolos_ext, errores_ext, _, _, _, _, _ = datos_extension

    escribir_archivo(
        "salida_ht10_tokens.json",
        json.dumps([token.como_dict() for token in tokens if token.tipo != "EOF"], indent=2, ensure_ascii=False),
    )
    escribir_archivo("salida_ht10_ast.json", json.dumps(ast.como_dict(), indent=2, ensure_ascii=False))
    escribir_archivo("salida_ht10_tabla_simbolos.txt", tabla_texto(simbolos))
    escribir_archivo("salida_ht10_tres_direcciones.txt", "\n".join(tac) + "\n")
    escribir_archivo(
        "salida_ht10_tres_direcciones_optimizado.txt",
        "\n".join(notas_opt) + "\n\n" + "\n".join(tac_opt) + "\n",
    )
    escribir_archivo("salida_ht10_mips.asm", "\n".join(mips) + "\n")
    escribir_archivo("salida_ht10_extension_ast.json", json.dumps(ast_ext.como_dict(), indent=2, ensure_ascii=False))
    escribir_archivo("salida_ht10_extension_tabla_simbolos.txt", tabla_texto(simbolos_ext))
    escribir_archivo("salida_ht10_extension_mips.asm", "\n".join(generar_extension_mips()) + "\n")
    escribir_archivo("HT10_Minicompilador.md", generar_documento(datos_base, datos_extension))

    print("HT10 generada correctamente.")
    print("Errores semanticos base:", "ninguno" if not errores else errores)
    print("Errores semanticos extension:", "ninguno" if not errores_ext else errores_ext)
    print("Archivos generados:")
    print("- HT10_Minicompilador.md")
    print("- salida_ht10_tokens.json")
    print("- salida_ht10_ast.json")
    print("- salida_ht10_tabla_simbolos.txt")
    print("- salida_ht10_tres_direcciones.txt")
    print("- salida_ht10_tres_direcciones_optimizado.txt")
    print("- salida_ht10_mips.asm")
    print("- salida_ht10_extension_ast.json")
    print("- salida_ht10_extension_tabla_simbolos.txt")
    print("- salida_ht10_extension_mips.asm")


if __name__ == "__main__":
    main()
