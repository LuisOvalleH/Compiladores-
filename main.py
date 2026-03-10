import json
from lexico import identificar_tokens
from sintactico_ast import Parser, crear_contexto_asm

codigo_fuente = """
int main() {
    int x = 1;
    int total = 0;

    print("Inicio -> ");
    println(x);

    for (int i = 0; i < 3; i = i + 1) {
        total = total + i;
    }

    while (x < 4) {
        if (x == 2) {
            println("x vale dos");
        } else {
            print("x = ");
            println(x);
        }
        x = x + 1;
    }

    println(total);
    return 0;
}
"""


def generar_asm(arbol):
    ctx = crear_contexto_asm()
    codigo_texto = arbol.traducir_asm(ctx)

    seccion_data = ["section .data", "    newline db 10"]
    for entrada in ctx["data"]:
        seccion_data.append(f"    {entrada}")

    seccion_bss = ["section .bss", "    digit_buffer resb 32"]
    for var in sorted(ctx["bss"]):
        seccion_bss.append(f"    {var} resq 1")

    rutinas = """
print_newline:
    mov rax, 1
    mov rdi, 1
    mov rsi, newline
    mov rdx, 1
    syscall
    ret

print_int:
    mov rcx, digit_buffer
    add rcx, 31
    mov byte [rcx], 0
    mov rbx, 10

    cmp rax, 0
    jne .loop
    dec rcx
    mov byte [rcx], '0'
    mov rsi, rcx
    mov rdx, 1
    jmp .write

.loop:
    xor rdx, rdx
    div rbx
    add dl, '0'
    dec rcx
    mov [rcx], dl
    cmp rax, 0
    jne .loop
    mov rsi, rcx
    mov rdx, digit_buffer
    add rdx, 31
    sub rdx, rsi

.write:
    mov rax, 1
    mov rdi, 1
    syscall
    ret
""".strip("\n")

    partes = [
        "\n".join(seccion_data),
        "\n",
        "\n".join(seccion_bss),
        "\nsection .text",
        codigo_texto.rstrip(),
        "\n" + rutinas,
        "",
    ]
    return "\n".join(partes)


def main():
    tokens = identificar_tokens(codigo_fuente)
    arbol = Parser(tokens).parsear()

    print("--- TRADUCCION A LUA ---")
    print(arbol.traducir_lua())
    print("\n--- TRADUCCION A PYTHON ---")
    print(arbol.traducir_python())

    asm = generar_asm(arbol)
    with open("salida.asm", "w", encoding="utf-8") as archivo:
        archivo.write(asm)

    print("\n--- AST (JSON) ---")
    print(json.dumps(arbol.to_dict(), indent=2, ensure_ascii=False))

    print("\n--- ENSAMBLADOR GENERADO ---")
    print("Se creo el archivo 'salida.asm'.")

    print("\n--- COMPILACION EN LINUX (NASM + LD) ---")
    print("1. nasm -f elf64 salida.asm -o salida.o")
    print("2. ld salida.o -o programa")
    print("3. ./programa")


if __name__ == "__main__":
    main()
