# Analizador Lexico, Sintactico y Traductor (AST)

# LUIS OVALLE 1515922

## Resumen
Este proyecto implementa un compilador academico en Python con estas fases:

- Analisis lexico para palabras reservadas, identificadores, numeros, cadenas, operadores y delimitadores.
- Analisis sintactico con construccion de AST.
- Traduccion del AST a un lenguaje de alto nivel distinto de C (Lua).
- Traduccion del AST a ensamblador NASM x86-64.

## Instrucciones soportadas
Las tareas solicitadas se cubren para:

- `print`
- `println`
- `for`
- `while`
- `if`
- `else`

## Archivos principales
- `lexico.py`: tokenizacion.
- `sintactico_ast.py`: nodos AST, parser y traduccion (Lua, Python y ASM).
- `main.py`: ejemplo completo, salida AST JSON y generacion de `salida.asm`.

## Ejecucion
```bash
python main.py
```

## Compilacion de ensamblador (Linux/WSL)
```bash
nasm -f elf64 salida.asm -o salida.o
ld salida.o -o programa
./programa
```

## Nota
En este entorno no hay Python instalado, por eso aqui no se pudo ejecutar `main.py` para prueba dinamica. La validacion realizada fue estatica sobre el codigo.
