# Python Compiler Toolkit

Academic compiler project built in Python. It includes lexical analysis, syntax analysis, AST construction, semantic checks, symbol table handling, and translation examples to Lua, Python, and NASM x86-64 assembly.

## Features

- Lexical analysis for reserved words, identifiers, numbers, strings, operators, and delimiters
- Parser with AST construction
- Semantic validation with a symbol table
- Translation from AST to Lua and Python
- NASM x86-64 assembly generation
- Extra examples for `printf`, floating-point arithmetic, semantic analysis, and a Pseudo-C minicompiler

## Supported Instructions

- `print`
- `println`
- `for`
- `while`
- `if`
- `else`

## Main Files

- `lexico.py`: tokenization and lexical analysis
- `sintactico_ast.py`: AST nodes, parser, and translation logic
- `main.py`: complete example, AST JSON output, and assembly generation
- `ht07_printf.py`: NASM x86-64 output using external `printf`
- `ht08_coma_flotante.py`: floating-point arithmetic with SSE registers
- `ht09_tabla_simbolos_semantico.py`: symbol table and semantic validation
- `ht10_minicompilador.py`: Pseudo-C minicompiler with tokens, AST JSON, symbol table, optimized three-address code, and MIPS output
- `HT10_Minicompilador.md`: written report for the HT10 assignment

## Usage

Run the main compiler example:

```bash
python main.py
```

Run the additional examples:

```bash
python ht07_printf.py
python ht08_coma_flotante.py
python ht09_tabla_simbolos_semantico.py
python ht10_minicompilador.py
```

## Assembly Compilation

On Linux or WSL:

```bash
nasm -f elf64 salida.asm -o salida.o
ld salida.o -o programa
./programa
```

## Notes

The Python scripts were validated with Python 3.12. To test the generated ASM files, use Linux or WSL with NASM and GCC installed.
