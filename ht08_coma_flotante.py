import itertools

from lexico import identificar_tokens
from sintactico_ast import (
    Parser,
    NodoAsignacion,
    NodoDeclaracion,
    NodoFor,
    NodoIdentificador,
    NodoIf,
    NodoNumero,
    NodoOperacion,
    NodoPrint,
    NodoReturn,
    NodoString,
    NodoWhile,
)
from ht09_tabla_simbolos_semantico import AnalizadorSemantico


class GeneradorFloatASM:
    def __init__(self, analizador):
        self.analizador = analizador
        self.data = [
            'fmt_int db "%ld", 0',
            'fmt_float db "%f", 0',
            'fmt_str db "%s", 0',
            "fmt_newline db 10, 0",
        ]
        self.bss = set()
        self.const_id = itertools.count()
        self.string_id = itertools.count()
        self.label_id = itertools.count()
        self.etiqueta_salida = "L_fin_main"

    def generar(self, arbol):
        cuerpo = "".join(self._instruccion(instr) for instr in arbol.cuerpo)

        seccion_data = ["default rel", "section .data"]
        seccion_data.extend(f"    {linea}" for linea in self.data)

        seccion_bss = ["section .bss"]
        for var in sorted(self.bss):
            seccion_bss.append(f"    {var} resq 1")

        return "\n".join(
            [
                "\n".join(seccion_data),
                "",
                "\n".join(seccion_bss),
                "",
                "section .text",
                "    extern printf",
                "    global main",
                "",
                "main:",
                "    push rbp",
                "    mov rbp, rsp",
                cuerpo.rstrip(),
                "    mov eax, 0",
                f"{self.etiqueta_salida}:",
                "    leave",
                "    ret",
                "",
            ]
        )

    def _instruccion(self, nodo):
        if isinstance(nodo, NodoDeclaracion):
            var = f"var_{nodo.nombre}"
            self.bss.add(var)
            asm, tipo_expr = self._expresion(nodo.expresion)
            asm += self._guardar_en_variable(var, nodo.tipo, tipo_expr)
            return asm

        if isinstance(nodo, NodoAsignacion):
            simbolo = self.analizador.tabla.buscar(nodo.nombre)
            tipo_destino = simbolo.tipo if simbolo else "int"
            asm, tipo_expr = self._expresion(nodo.expresion)
            asm += self._guardar_en_variable(f"var_{nodo.nombre}", tipo_destino, tipo_expr)
            return asm

        if isinstance(nodo, NodoPrint):
            asm = ""
            for expresion in nodo.expresiones:
                asm += self._imprimir_expresion(expresion)
            if nodo.salto_linea:
                asm += self._llamar_printf("fmt_newline", cantidad_xmm=0)
            return asm

        if isinstance(nodo, NodoIf):
            etiqueta_else = f"L_else_{next(self.label_id)}"
            etiqueta_fin = f"L_if_fin_{next(self.label_id)}"
            asm, tipo = self._expresion(nodo.condicion)
            asm += self._condicion_a_rax(tipo)
            asm += "    cmp rax, 0\n"
            asm += f"    je {etiqueta_else}\n"
            asm += "".join(self._instruccion(instr) for instr in nodo.cuerpo_if)
            asm += f"    jmp {etiqueta_fin}\n"
            asm += f"{etiqueta_else}:\n"
            asm += "".join(self._instruccion(instr) for instr in nodo.cuerpo_else)
            asm += f"{etiqueta_fin}:\n"
            return asm

        if isinstance(nodo, NodoWhile):
            etiqueta_inicio = f"L_while_ini_{next(self.label_id)}"
            etiqueta_fin = f"L_while_fin_{next(self.label_id)}"
            asm = f"{etiqueta_inicio}:\n"
            asm_cond, tipo = self._expresion(nodo.condicion)
            asm += asm_cond
            asm += self._condicion_a_rax(tipo)
            asm += "    cmp rax, 0\n"
            asm += f"    je {etiqueta_fin}\n"
            asm += "".join(self._instruccion(instr) for instr in nodo.cuerpo)
            asm += f"    jmp {etiqueta_inicio}\n"
            asm += f"{etiqueta_fin}:\n"
            return asm

        if isinstance(nodo, NodoFor):
            etiqueta_inicio = f"L_for_ini_{next(self.label_id)}"
            etiqueta_fin = f"L_for_fin_{next(self.label_id)}"
            asm = self._instruccion(nodo.inicializacion)
            asm += f"{etiqueta_inicio}:\n"
            asm_cond, tipo = self._expresion(nodo.condicion)
            asm += asm_cond
            asm += self._condicion_a_rax(tipo)
            asm += "    cmp rax, 0\n"
            asm += f"    je {etiqueta_fin}\n"
            asm += "".join(self._instruccion(instr) for instr in nodo.cuerpo)
            asm += self._instruccion(nodo.incremento)
            asm += f"    jmp {etiqueta_inicio}\n"
            asm += f"{etiqueta_fin}:\n"
            return asm

        if isinstance(nodo, NodoReturn):
            asm, tipo = self._expresion(nodo.expresion)
            if tipo == "float":
                asm += "    cvttsd2si rax, xmm0\n"
            asm += f"    jmp {self.etiqueta_salida}\n"
            return asm

        raise NotImplementedError(f"Instruccion no soportada: {type(nodo).__name__}")

    def _expresion(self, nodo):
        tipo = self.analizador.tipo_expresion(nodo)

        if isinstance(nodo, NodoNumero):
            if tipo == "float":
                etiqueta = f"float_const_{next(self.const_id)}"
                self.data.append(f"{etiqueta} dq {nodo.valor}")
                return f"    movsd xmm0, [{etiqueta}]\n", "float"
            return f"    mov rax, {nodo.valor}\n", "int"

        if isinstance(nodo, NodoIdentificador):
            if tipo == "float":
                return f"    movsd xmm0, [var_{nodo.nombre}]\n", "float"
            return f"    mov rax, [var_{nodo.nombre}]\n", "int"

        if isinstance(nodo, NodoOperacion):
            if nodo.operador in {"==", "<", ">", "<=", ">="}:
                return self._comparacion(nodo)

            asm_izq, tipo_izq = self._expresion(nodo.izquierda)
            asm_der, tipo_der = self._expresion(nodo.derecha)
            tipo_resultado = "float" if "float" in {tipo_izq, tipo_der} else "int"

            if tipo_resultado == "float":
                asm = asm_izq
                asm += self._apilar_resultado(tipo_izq)
                asm += asm_der
                asm += self._mover_a_xmm0(tipo_der)
                asm += self._desapilar_en_xmm1(tipo_izq)
                asm += self._operacion_float(nodo.operador)
                return asm, "float"

            asm = asm_izq
            asm += "    push rax\n"
            asm += asm_der
            asm += "    mov rbx, rax\n"
            asm += "    pop rax\n"
            asm += self._operacion_int(nodo.operador)
            return asm, "int"

        if isinstance(nodo, NodoString):
            etiqueta = f"str_{next(self.string_id)}"
            contenido = nodo.valor[1:-1]
            bytes_texto = ", ".join(str(ord(caracter)) for caracter in contenido)
            self.data.append(f"{etiqueta} db {bytes_texto}, 0")
            return f"    lea rax, [{etiqueta}]\n", "string"

        raise NotImplementedError(f"Expresion no soportada: {type(nodo).__name__}")

    def _comparacion(self, nodo):
        asm_izq, tipo_izq = self._expresion(nodo.izquierda)
        asm_der, tipo_der = self._expresion(nodo.derecha)

        if "float" in {tipo_izq, tipo_der}:
            asm = asm_izq
            asm += self._apilar_resultado(tipo_izq)
            asm += asm_der
            asm += self._mover_a_xmm0(tipo_der)
            asm += self._desapilar_en_xmm1(tipo_izq)
            asm += "    ucomisd xmm1, xmm0\n"
            asm += self._set_por_operador(nodo.operador)
            return asm, "int"

        asm = asm_izq
        asm += "    push rax\n"
        asm += asm_der
        asm += "    mov rbx, rax\n"
        asm += "    pop rax\n"
        asm += "    cmp rax, rbx\n"
        asm += self._set_por_operador(nodo.operador)
        return asm, "int"

    def _guardar_en_variable(self, var, tipo_destino, tipo_expr):
        if tipo_destino == "float":
            asm = self._mover_a_xmm0(tipo_expr)
            asm += f"    movsd [{var}], xmm0\n"
            return asm
        return f"    mov [{var}], rax\n"

    def _imprimir_expresion(self, nodo):
        asm, tipo = self._expresion(nodo)
        if tipo == "float":
            asm += self._llamar_printf("fmt_float", cantidad_xmm=1)
            return asm
        if tipo == "string":
            asm += "    mov rsi, rax\n"
            asm += self._llamar_printf("fmt_str", cantidad_xmm=0)
            return asm
        asm += "    mov rsi, rax\n"
        asm += self._llamar_printf("fmt_int", cantidad_xmm=0)
        return asm

    def _llamar_printf(self, formato, cantidad_xmm):
        asm = f"    lea rdi, [{formato}]\n"
        asm += f"    mov eax, {cantidad_xmm}\n"
        asm += "    call printf\n"
        return asm

    def _apilar_resultado(self, tipo):
        if tipo == "float":
            return "    sub rsp, 8\n    movsd [rsp], xmm0\n"
        return "    push rax\n"

    def _desapilar_en_xmm1(self, tipo_original):
        if tipo_original == "float":
            return "    movsd xmm1, [rsp]\n    add rsp, 8\n"
        return "    pop rbx\n    cvtsi2sd xmm1, rbx\n"

    def _mover_a_xmm0(self, tipo_actual):
        if tipo_actual == "float":
            return ""
        return "    cvtsi2sd xmm0, rax\n"

    def _operacion_float(self, operador):
        instrucciones = {
            "+": "addsd",
            "-": "subsd",
            "*": "mulsd",
            "/": "divsd",
        }
        instruccion = instrucciones[operador]
        return f"    {instruccion} xmm1, xmm0\n    movsd xmm0, xmm1\n"

    def _operacion_int(self, operador):
        if operador == "+":
            return "    add rax, rbx\n"
        if operador == "-":
            return "    sub rax, rbx\n"
        if operador == "*":
            return "    imul rax, rbx\n"
        if operador == "/":
            return "    cqo\n    idiv rbx\n"
        raise NotImplementedError(f"Operador no soportado: {operador}")

    def _set_por_operador(self, operador):
        saltos = {
            "==": "sete",
            "<": "setb",
            ">": "seta",
            "<=": "setbe",
            ">=": "setae",
        }
        return f"    {saltos[operador]} al\n    movzx rax, al\n"

    def _condicion_a_rax(self, tipo):
        if tipo == "float":
            return (
                "    pxor xmm1, xmm1\n"
                "    ucomisd xmm0, xmm1\n"
                "    setne al\n"
                "    movzx rax, al\n"
            )
        return ""


codigo_fuente = """
int main() {
    float precio = 125.50;
    float descuento = 15.25;
    float impuesto = (precio - descuento) * 0.12;
    float total = precio - descuento + impuesto;

    print("Total con coma flotante: ");
    println(total);
    return 0;
}
"""


def main():
    tokens = identificar_tokens(codigo_fuente)
    arbol = Parser(tokens).parsear()

    analizador = AnalizadorSemantico()
    tabla, errores = analizador.analizar(arbol)
    if errores:
        print("No se genero ASM porque hay errores semanticos:")
        for error in errores:
            print(f"ERROR: {error}")
        return

    asm = GeneradorFloatASM(analizador).generar(arbol)
    with open("salida_ht08_float.asm", "w", encoding="utf-8") as archivo:
        archivo.write(asm)

    print("--- TABLA DE SIMBOLOS ---")
    print(tabla.como_texto())
    print("\nSe genero salida_ht08_float.asm con operaciones de coma flotante.")
    print("Compilacion sugerida en Linux/WSL:")
    print("nasm -f elf64 salida_ht08_float.asm -o salida_ht08_float.o")
    print("gcc -no-pie salida_ht08_float.o -o salida_ht08_float")
    print("./salida_ht08_float")


if __name__ == "__main__":
    main()
