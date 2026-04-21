# HT10 - Minicompilador

Archivo principal: `ht10_minicompilador.py`

Para ejecutarlo:

```bash
python ht10_minicompilador.py
```

El programa toma el codigo Pseudo-C del enunciado y muestra en consola:

1. Secuencia de tokens.
2. AST en JSON para visualizarlo en json-crack.
3. Tabla de simbolos y validacion semantica.
4. Codigo de 3 direcciones.
5. Codigo optimizado.
6. Ensamblador MIPS simplificado.

## Programa fuente

```text
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
```

## Tokens definidos

- `RESERVADA`: inicio, fin, si, entonces, finsi, escribir.
- `IDENTIFICADOR`: nombres de variables.
- `NUMERO`: constantes enteras.
- `OPERADOR`: =, +, -, *, /, >, <, >=, <=, ==, !=.
- `DELIMITADOR`: parentesis.

## AST

El AST se imprime como JSON al correr el programa. Sus nodos principales son:

- `programa`
- `asignacion`
- `si`
- `escribir`
- `binaria`
- `constante`
- `variable`

## Analisis semantico

Tabla esperada despues del analisis:

```text
a: entero = 10
b: entero = 20
c: entero = 50
d: entero = 40
```

No hay error semantico en este programa especifico. Aunque `d` se asigna dentro del `si`, los valores son constantes:

```text
c = a + b * 2
c = 10 + 20 * 2
c = 50
```

Como `50 > 30`, el cuerpo del `si` siempre se ejecuta y `d` queda definida antes de `escribir(d)`.

## Codigo de 3 direcciones sin optimizar

```text
a = 10
b = 20
t1 = b * 2
t2 = a + t1
c = t2
t3 = c > 30
if_false t3 goto L1
escribir c
t4 = c - 10
d = t4
L1:
escribir d
```

## Optimizaciones

Se aplican dos optimizaciones simples:

- Plegado y propagacion de constantes.
- Eliminacion del salto del `si` porque la condicion se conoce como verdadera.

Resultado optimizado:

```text
a = 10
b = 20
c = 50
# condicion verdadera, se elimina el salto
escribir 50
d = 40
escribir 40
```

## Ensamblador MIPS

El MIPS completo se imprime al ejecutar el archivo. Usa esta convencion:

- Variables en memoria dentro de `.data`.
- Operaciones con registros `$t0`, `$t1`, etc.
- `escribir` con syscall `1`.
- Salto de linea con syscall `4`.
- Condicional con salto inverso, por ejemplo `ble`.
