from dataclasses import dataclass

from lexico import identificar_tokens
from sintactico_ast import (
    Parser,
    NodoAsignacion,
    NodoDeclaracion,
    NodoFor,
    NodoFuncion,
    NodoIdentificador,
    NodoIf,
    NodoNumero,
    NodoOperacion,
    NodoPrint,
    NodoReturn,
    NodoString,
    NodoWhile,
)


@dataclass
class Simbolo:
    nombre: str
    tipo: str
    categoria: str
    ambito: str


class TablaSimbolos:
    def __init__(self):
        self.simbolos = {}

    def agregar(self, simbolo):
        if simbolo.nombre in self.simbolos:
            return False
        self.simbolos[simbolo.nombre] = simbolo
        return True

    def buscar(self, nombre):
        return self.simbolos.get(nombre)

    def como_texto(self):
        lineas = ["NOMBRE          TIPO       CATEGORIA   AMBITO"]
        lineas.append("-" * 50)
        for simbolo in self.simbolos.values():
            lineas.append(
                f"{simbolo.nombre:<15} {simbolo.tipo:<10} "
                f"{simbolo.categoria:<11} {simbolo.ambito}"
            )
        return "\n".join(lineas)


class AnalizadorSemantico:
    TIPOS_VALIDOS = {"int", "float", "void"}
    OPS_ARITMETICOS = {"+", "-", "*", "/"}
    OPS_RELACIONALES = {"==", "<", ">", "<=", ">="}

    def __init__(self):
        self.tabla = TablaSimbolos()
        self.errores = []
        self.tipo_retorno = "void"

    def analizar(self, arbol):
        if not isinstance(arbol, NodoFuncion):
            self.errores.append("El programa debe iniciar con una funcion.")
            return self.tabla, self.errores

        self.tipo_retorno = arbol.tipo
        self._validar_tipo(arbol.tipo, f"funcion {arbol.nombre}")
        self.tabla.agregar(Simbolo(arbol.nombre, arbol.tipo, "funcion", "global"))

        for parametro in arbol.parametros:
            self._validar_tipo(parametro.tipo, f"parametro {parametro.nombre}")
            if parametro.tipo == "void":
                self.errores.append(f"El parametro '{parametro.nombre}' no puede ser void.")
            agregado = self.tabla.agregar(
                Simbolo(parametro.nombre, parametro.tipo, "parametro", arbol.nombre)
            )
            if not agregado:
                self.errores.append(f"Parametro duplicado: '{parametro.nombre}'.")

        for instruccion in arbol.cuerpo:
            self._analizar_instruccion(instruccion, arbol.nombre)

        return self.tabla, self.errores

    def tipo_expresion(self, nodo):
        if isinstance(nodo, NodoNumero):
            return "float" if "." in nodo.valor else "int"

        if isinstance(nodo, NodoString):
            return "string"

        if isinstance(nodo, NodoIdentificador):
            simbolo = self.tabla.buscar(nodo.nombre)
            if simbolo is None:
                self.errores.append(f"Variable no declarada: '{nodo.nombre}'.")
                return "error"
            return simbolo.tipo

        if isinstance(nodo, NodoOperacion):
            tipo_izq = self.tipo_expresion(nodo.izquierda)
            tipo_der = self.tipo_expresion(nodo.derecha)

            if "error" in {tipo_izq, tipo_der}:
                return "error"

            if nodo.operador in self.OPS_ARITMETICOS:
                if not self._es_numerico(tipo_izq) or not self._es_numerico(tipo_der):
                    self.errores.append(
                        f"Operacion aritmetica invalida: {tipo_izq} "
                        f"{nodo.operador} {tipo_der}."
                    )
                    return "error"
                return "float" if "float" in {tipo_izq, tipo_der} else "int"

            if nodo.operador in self.OPS_RELACIONALES:
                if not self._es_numerico(tipo_izq) or not self._es_numerico(tipo_der):
                    self.errores.append(
                        f"Comparacion invalida: {tipo_izq} {nodo.operador} {tipo_der}."
                    )
                    return "error"
                return "int"

        self.errores.append(f"Expresion no soportada: {type(nodo).__name__}.")
        return "error"

    def _analizar_instruccion(self, nodo, ambito):
        if isinstance(nodo, NodoDeclaracion):
            self._validar_tipo(nodo.tipo, f"variable {nodo.nombre}")
            if nodo.tipo == "void":
                self.errores.append(f"La variable '{nodo.nombre}' no puede ser void.")

            agregado = self.tabla.agregar(Simbolo(nodo.nombre, nodo.tipo, "variable", ambito))
            if not agregado:
                self.errores.append(f"Variable duplicada: '{nodo.nombre}'.")

            tipo_expr = self.tipo_expresion(nodo.expresion)
            if not self._tipos_compatibles(nodo.tipo, tipo_expr):
                self.errores.append(
                    f"No se puede asignar {tipo_expr} a variable "
                    f"'{nodo.nombre}' de tipo {nodo.tipo}."
                )
            return

        if isinstance(nodo, NodoAsignacion):
            simbolo = self.tabla.buscar(nodo.nombre)
            if simbolo is None:
                self.errores.append(f"Variable no declarada: '{nodo.nombre}'.")
                self.tipo_expresion(nodo.expresion)
                return

            tipo_expr = self.tipo_expresion(nodo.expresion)
            if not self._tipos_compatibles(simbolo.tipo, tipo_expr):
                self.errores.append(
                    f"No se puede asignar {tipo_expr} a variable "
                    f"'{nodo.nombre}' de tipo {simbolo.tipo}."
                )
            return

        if isinstance(nodo, NodoPrint):
            for expresion in nodo.expresiones:
                self.tipo_expresion(expresion)
            return

        if isinstance(nodo, NodoIf):
            self._validar_condicion(nodo.condicion, "if")
            for instruccion in nodo.cuerpo_if:
                self._analizar_instruccion(instruccion, ambito)
            for instruccion in nodo.cuerpo_else:
                self._analizar_instruccion(instruccion, ambito)
            return

        if isinstance(nodo, NodoWhile):
            self._validar_condicion(nodo.condicion, "while")
            for instruccion in nodo.cuerpo:
                self._analizar_instruccion(instruccion, ambito)
            return

        if isinstance(nodo, NodoFor):
            self._analizar_instruccion(nodo.inicializacion, ambito)
            self._validar_condicion(nodo.condicion, "for")
            self._analizar_instruccion(nodo.incremento, ambito)
            for instruccion in nodo.cuerpo:
                self._analizar_instruccion(instruccion, ambito)
            return

        if isinstance(nodo, NodoReturn):
            tipo_expr = self.tipo_expresion(nodo.expresion)
            if not self._tipos_compatibles(self.tipo_retorno, tipo_expr):
                self.errores.append(
                    f"El return entrega {tipo_expr}, pero la funcion espera "
                    f"{self.tipo_retorno}."
                )
            return

        self.errores.append(f"Instruccion no soportada: {type(nodo).__name__}.")

    def _validar_condicion(self, expresion, instruccion):
        tipo = self.tipo_expresion(expresion)
        if tipo != "error" and not self._es_numerico(tipo):
            self.errores.append(f"La condicion de {instruccion} debe ser numerica.")

    def _validar_tipo(self, tipo, descripcion):
        if tipo not in self.TIPOS_VALIDOS:
            self.errores.append(f"Tipo invalido en {descripcion}: {tipo}.")

    def _tipos_compatibles(self, destino, origen):
        if origen == "error":
            return True
        if destino == origen:
            return True
        if destino == "float" and origen == "int":
            return True
        return False

    def _es_numerico(self, tipo):
        return tipo in {"int", "float"}


codigo_fuente = """
int main() {
    int contador = 0;
    float subtotal = 12.50;
    float impuesto = subtotal * 0.12;
    float total = subtotal + impuesto;

    while (contador < 3) {
        println(total);
        contador = contador + 1;
    }

    return 0;
}
"""


def main():
    tokens = identificar_tokens(codigo_fuente)
    arbol = Parser(tokens).parsear()

    analizador = AnalizadorSemantico()
    tabla, errores = analizador.analizar(arbol)

    print("--- TABLA DE SIMBOLOS ---")
    print(tabla.como_texto())

    print("\n--- ANALISIS SEMANTICO ---")
    if errores:
        for error in errores:
            print(f"ERROR: {error}")
    else:
        print("Programa semanticamente correcto.")


if __name__ == "__main__":
    main()
