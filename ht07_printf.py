import ast
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


class GeneradorPrintfASM:
    def __init__(self):
        self.data = [
            'fmt_int db "%ld", 0',
            'fmt_str db "%s", 0',
            "fmt_newline db 10, 0",
        ]
        self.bss = set()
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
            return self._expresion(nodo.expresion) + f"    mov [{var}], rax\n"

        if isinstance(nodo, NodoAsignacion):
            return self._expresion(nodo.expresion) + f"    mov [var_{nodo.nombre}], rax\n"

        if isinstance(nodo, NodoPrint):
            asm = ""
            for expresion in nodo.expresiones:
                asm += self._imprimir_expresion(expresion)
            if nodo.salto_linea:
                asm += self._llamar_printf("fmt_newline")
            return asm

        if isinstance(nodo, NodoIf):
            etiqueta_else = f"L_else_{next(self.label_id)}"
            etiqueta_fin = f"L_if_fin_{next(self.label_id)}"
            asm = self._expresion(nodo.condicion)
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
            asm += self._expresion(nodo.condicion)
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
            asm += self._expresion(nodo.condicion)
            asm += "    cmp rax, 0\n"
            asm += f"    je {etiqueta_fin}\n"
            asm += "".join(self._instruccion(instr) for instr in nodo.cuerpo)
            asm += self._instruccion(nodo.incremento)
            asm += f"    jmp {etiqueta_inicio}\n"
            asm += f"{etiqueta_fin}:\n"
            return asm

        if isinstance(nodo, NodoReturn):
            return self._expresion(nodo.expresion) + f"    jmp {self.etiqueta_salida}\n"

        raise NotImplementedError(f"Instruccion no soportada: {type(nodo).__name__}")

    def _expresion(self, nodo):
        if isinstance(nodo, NodoNumero):
            return f"    mov rax, {nodo.valor}\n"

        if isinstance(nodo, NodoIdentificador):
            return f"    mov rax, [var_{nodo.nombre}]\n"

        if isinstance(nodo, NodoOperacion):
            asm = self._expresion(nodo.izquierda)
            asm += "    push rax\n"
            asm += self._expresion(nodo.derecha)
            asm += "    mov rbx, rax\n"
            asm += "    pop rax\n"

            if nodo.operador == "+":
                asm += "    add rax, rbx\n"
            elif nodo.operador == "-":
                asm += "    sub rax, rbx\n"
            elif nodo.operador == "*":
                asm += "    imul rax, rbx\n"
            elif nodo.operador == "/":
                asm += "    cqo\n"
                asm += "    idiv rbx\n"
            elif nodo.operador in {"==", "<", ">", "<=", ">="}:
                asm += "    cmp rax, rbx\n"
                saltos = {
                    "==": "sete",
                    "<": "setl",
                    ">": "setg",
                    "<=": "setle",
                    ">=": "setge",
                }
                asm += f"    {saltos[nodo.operador]} al\n"
                asm += "    movzx rax, al\n"
            else:
                raise NotImplementedError(f"Operador no soportado: {nodo.operador}")
            return asm

        raise NotImplementedError(f"Expresion no soportada: {type(nodo).__name__}")

    def _imprimir_expresion(self, nodo):
        if isinstance(nodo, NodoString):
            etiqueta = self._agregar_string(nodo.valor)
            asm = f"    lea rsi, [{etiqueta}]\n"
            asm += self._llamar_printf("fmt_str", usa_argumento=True)
            return asm

        asm = self._expresion(nodo)
        asm += "    mov rsi, rax\n"
        asm += self._llamar_printf("fmt_int", usa_argumento=True)
        return asm

    def _llamar_printf(self, formato, usa_argumento=False):
        asm = f"    lea rdi, [{formato}]\n"
        if not usa_argumento:
            asm += "    xor eax, eax\n"
        else:
            asm += "    xor eax, eax\n"
        asm += "    call printf\n"
        return asm

    def _agregar_string(self, token_string):
        etiqueta = f"str_{next(self.string_id)}"
        contenido = ast.literal_eval(token_string)
        bytes_texto = ", ".join(str(ord(caracter)) for caracter in contenido)
        if bytes_texto:
            self.data.append(f"{etiqueta} db {bytes_texto}, 0")
        else:
            self.data.append(f"{etiqueta} db 0")
        return etiqueta


codigo_fuente = """
int main() {
    int x = 1;
    int total = 0;

    print("Inicio con printf: ");
    println(x);

    for (int i = 0; i < 4; i = i + 1) {
        total = total + i;
    }

    println("Total acumulado:");
    println(total);
    return 0;
}
"""


def main():
    tokens = identificar_tokens(codigo_fuente)
    arbol = Parser(tokens).parsear()

    asm = GeneradorPrintfASM().generar(arbol)
    with open("salida_ht07_printf.asm", "w", encoding="utf-8") as archivo:
        archivo.write(asm)

    print("Se genero salida_ht07_printf.asm usando printf externo.")
    print("Compilacion sugerida en Linux/WSL:")
    print("nasm -f elf64 salida_ht07_printf.asm -o salida_ht07_printf.o")
    print("gcc -no-pie salida_ht07_printf.o -o salida_ht07_printf")
    print("./salida_ht07_printf")


if __name__ == "__main__":
    main()
