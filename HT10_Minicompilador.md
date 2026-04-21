# HT10 - Minicompilador Pseudo-C

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

## 1. Analisis lexico
Tokens definidos:

- `RESERVADA`: inicio, fin, si, entonces, finsi, escribir.
- `IDENTIFICADOR`: nombres de variables como a, b, c, d.
- `NUMERO`: constantes enteras.
- `OPERADOR`: =, +, -, *, /, >, <, >=, <=, ==, !=.
- `DELIMITADOR`: parentesis y coma.

Secuencia de tokens:

```json
[
  {
    "tipo": "RESERVADA",
    "valor": "inicio",
    "linea": 2,
    "columna": 1
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "a",
    "linea": 3,
    "columna": 5
  },
  {
    "tipo": "OPERADOR",
    "valor": "=",
    "linea": 3,
    "columna": 7
  },
  {
    "tipo": "NUMERO",
    "valor": "10",
    "linea": 3,
    "columna": 9
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "b",
    "linea": 4,
    "columna": 5
  },
  {
    "tipo": "OPERADOR",
    "valor": "=",
    "linea": 4,
    "columna": 7
  },
  {
    "tipo": "NUMERO",
    "valor": "20",
    "linea": 4,
    "columna": 9
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "c",
    "linea": 5,
    "columna": 5
  },
  {
    "tipo": "OPERADOR",
    "valor": "=",
    "linea": 5,
    "columna": 7
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "a",
    "linea": 5,
    "columna": 9
  },
  {
    "tipo": "OPERADOR",
    "valor": "+",
    "linea": 5,
    "columna": 11
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "b",
    "linea": 5,
    "columna": 13
  },
  {
    "tipo": "OPERADOR",
    "valor": "*",
    "linea": 5,
    "columna": 15
  },
  {
    "tipo": "NUMERO",
    "valor": "2",
    "linea": 5,
    "columna": 17
  },
  {
    "tipo": "RESERVADA",
    "valor": "si",
    "linea": 6,
    "columna": 5
  },
  {
    "tipo": "DELIMITADOR",
    "valor": "(",
    "linea": 6,
    "columna": 8
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "c",
    "linea": 6,
    "columna": 9
  },
  {
    "tipo": "OPERADOR",
    "valor": ">",
    "linea": 6,
    "columna": 11
  },
  {
    "tipo": "NUMERO",
    "valor": "30",
    "linea": 6,
    "columna": 13
  },
  {
    "tipo": "DELIMITADOR",
    "valor": ")",
    "linea": 6,
    "columna": 15
  },
  {
    "tipo": "RESERVADA",
    "valor": "entonces",
    "linea": 6,
    "columna": 17
  },
  {
    "tipo": "RESERVADA",
    "valor": "escribir",
    "linea": 7,
    "columna": 9
  },
  {
    "tipo": "DELIMITADOR",
    "valor": "(",
    "linea": 7,
    "columna": 17
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "c",
    "linea": 7,
    "columna": 18
  },
  {
    "tipo": "DELIMITADOR",
    "valor": ")",
    "linea": 7,
    "columna": 19
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "d",
    "linea": 8,
    "columna": 9
  },
  {
    "tipo": "OPERADOR",
    "valor": "=",
    "linea": 8,
    "columna": 11
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "c",
    "linea": 8,
    "columna": 13
  },
  {
    "tipo": "OPERADOR",
    "valor": "-",
    "linea": 8,
    "columna": 15
  },
  {
    "tipo": "NUMERO",
    "valor": "10",
    "linea": 8,
    "columna": 17
  },
  {
    "tipo": "RESERVADA",
    "valor": "finsi",
    "linea": 9,
    "columna": 5
  },
  {
    "tipo": "RESERVADA",
    "valor": "escribir",
    "linea": 10,
    "columna": 5
  },
  {
    "tipo": "DELIMITADOR",
    "valor": "(",
    "linea": 10,
    "columna": 13
  },
  {
    "tipo": "IDENTIFICADOR",
    "valor": "d",
    "linea": 10,
    "columna": 14
  },
  {
    "tipo": "DELIMITADOR",
    "valor": ")",
    "linea": 10,
    "columna": 15
  },
  {
    "tipo": "RESERVADA",
    "valor": "fin",
    "linea": 11,
    "columna": 1
  }
]
```

## 2. Analisis sintactico y AST
El arbol usa nodos de programa, asignacion, si, escribir, operacion binaria, constante y variable. Este JSON se puede pegar en json-crack para visualizarlo.

```json
{
  "tipo": "programa",
  "funciones": [],
  "instrucciones": [
    {
      "tipo": "asignacion",
      "variable": "a",
      "expresion": {
        "tipo": "constante",
        "valor": 10
      }
    },
    {
      "tipo": "asignacion",
      "variable": "b",
      "expresion": {
        "tipo": "constante",
        "valor": 20
      }
    },
    {
      "tipo": "asignacion",
      "variable": "c",
      "expresion": {
        "tipo": "operacion_binaria",
        "operador": "+",
        "izquierda": {
          "tipo": "variable",
          "nombre": "a"
        },
        "derecha": {
          "tipo": "operacion_binaria",
          "operador": "*",
          "izquierda": {
            "tipo": "variable",
            "nombre": "b"
          },
          "derecha": {
            "tipo": "constante",
            "valor": 2
          }
        }
      }
    },
    {
      "tipo": "si",
      "condicion": {
        "tipo": "operacion_binaria",
        "operador": ">",
        "izquierda": {
          "tipo": "variable",
          "nombre": "c"
        },
        "derecha": {
          "tipo": "constante",
          "valor": 30
        }
      },
      "cuerpo": [
        {
          "tipo": "escribir",
          "expresion": {
            "tipo": "variable",
            "nombre": "c"
          }
        },
        {
          "tipo": "asignacion",
          "variable": "d",
          "expresion": {
            "tipo": "operacion_binaria",
            "operador": "-",
            "izquierda": {
              "tipo": "variable",
              "nombre": "c"
            },
            "derecha": {
              "tipo": "constante",
              "valor": 10
            }
          }
        }
      ]
    },
    {
      "tipo": "escribir",
      "expresion": {
        "tipo": "variable",
        "nombre": "d"
      }
    }
  ]
}
```

## 3. Analisis semantico
Tabla de simbolos despues del analisis:

```text
NOMBRE       TIPO     CATEGORIA   AMBITO     VALOR   NOTA
----------------------------------------------------------------------
a            entero   variable    global     10      entero
b            entero   variable    global     20      entero
c            entero   variable    global     50      entero
d            entero   variable    global     40      entero
```

Errores encontrados:

```text
No se encontraron errores semanticos para este programa.
```

La variable `d` se usa en `escribir(d)` despues del `finsi`. En un analisis general esto podria ser peligroso, porque `d` se asigna dentro del `si`. Sin embargo, en este programa los valores son conocidos: `a = 10`, `b = 20`, entonces `c = a + b * 2 = 50`. La condicion `c > 30` se evalua como verdadera, por eso el bloque del `si` siempre se ejecuta y `d = c - 10` queda inicializada con el valor `40` antes del ultimo `escribir`.

## 4. Codigo de 3 direcciones
Sin optimizar:

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

Optimizaciones aplicadas:

```text
Optimizacion 1: propagacion y plegado de constantes.
Optimizacion 2: eliminacion del salto y etiqueta del si porque la condicion se evalua como verdadera.
```

Resultado optimizado:

```text
a = 10
b = 20
c = 50
# condicion c > 30 verdadera; se conserva solo el cuerpo del si
escribir 50
d = 40
escribir 40
```

## 5. Traduccion a ensamblador MIPS simplificado
Convencion usada: las variables se almacenan en memoria en la seccion `.data`; los calculos usan registros temporales `$t0`, `$t1`, etc.; `escribir` se simula con syscall `1` para imprimir entero y syscall `4` para salto de linea.

```asm
.data
    a: .word 0
    b: .word 0
    c: .word 0
    d: .word 0
    salto: .asciiz "\n"

.text
.globl main
main:
    li $t0, 10
    sw $t0, a
    li $t1, 20
    sw $t1, b
    lw $t2, a
    lw $t3, b
    li $t4, 2
    mul $t5, $t3, $t4
    add $t6, $t2, $t5
    sw $t6, c
    lw $t7, c
    li $t8, 30
    ble $t7, $t8, L_fin_si_1
    lw $t9, c
    move $a0, $t9
    li $v0, 1
    syscall
    la $a0, salto
    li $v0, 4
    syscall
    lw $t0, c
    li $t1, 10
    sub $t2, $t0, $t1
    sw $t2, d
L_fin_si_1:
    lw $t3, d
    move $a0, $t3
    li $v0, 1
    syscall
    la $a0, salto
    li $v0, 4
    syscall
    li $v0, 10
    syscall
```

## 6. Extension: funcion simple
Se agrega una funcion `suma(x, y)` que retorna `x + y` y se llama desde el programa principal.

Programa extendido:

```text
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
```

Cambios en AST: aparece el nodo `funcion`, el nodo `retornar` y el nodo `llamada_funcion`.

```json
{
  "tipo": "programa",
  "funciones": [
    {
      "tipo": "funcion",
      "nombre": "suma",
      "parametros": [
        "x",
        "y"
      ],
      "cuerpo": [
        {
          "tipo": "retornar",
          "expresion": {
            "tipo": "operacion_binaria",
            "operador": "+",
            "izquierda": {
              "tipo": "variable",
              "nombre": "x"
            },
            "derecha": {
              "tipo": "variable",
              "nombre": "y"
            }
          }
        }
      ]
    }
  ],
  "instrucciones": [
    {
      "tipo": "asignacion",
      "variable": "a",
      "expresion": {
        "tipo": "constante",
        "valor": 10
      }
    },
    {
      "tipo": "asignacion",
      "variable": "b",
      "expresion": {
        "tipo": "constante",
        "valor": 20
      }
    },
    {
      "tipo": "asignacion",
      "variable": "c",
      "expresion": {
        "tipo": "operacion_binaria",
        "operador": "+",
        "izquierda": {
          "tipo": "llamada_funcion",
          "nombre": "suma",
          "argumentos": [
            {
              "tipo": "variable",
              "nombre": "a"
            },
            {
              "tipo": "variable",
              "nombre": "b"
            }
          ]
        },
        "derecha": {
          "tipo": "variable",
          "nombre": "b"
        }
      }
    },
    {
      "tipo": "si",
      "condicion": {
        "tipo": "operacion_binaria",
        "operador": ">",
        "izquierda": {
          "tipo": "variable",
          "nombre": "c"
        },
        "derecha": {
          "tipo": "constante",
          "valor": 30
        }
      },
      "cuerpo": [
        {
          "tipo": "escribir",
          "expresion": {
            "tipo": "variable",
            "nombre": "c"
          }
        },
        {
          "tipo": "asignacion",
          "variable": "d",
          "expresion": {
            "tipo": "operacion_binaria",
            "operador": "-",
            "izquierda": {
              "tipo": "variable",
              "nombre": "c"
            },
            "derecha": {
              "tipo": "constante",
              "valor": 10
            }
          }
        }
      ]
    },
    {
      "tipo": "escribir",
      "expresion": {
        "tipo": "variable",
        "nombre": "d"
      }
    }
  ]
}
```

Nueva tabla de simbolos con ambito:

```text
NOMBRE       TIPO     CATEGORIA   AMBITO     VALOR   NOTA
----------------------------------------------------------------------
suma         entero   funcion     global     -       retorna entero
x            entero   parametro   suma       -       entero
y            entero   parametro   suma       -       entero
a            entero   variable    global     10      entero
b            entero   variable    global     20      entero
c            entero   variable    global     50      entero
d            entero   variable    global     40      entero
```

Errores en la extension:

```text
No se encontraron errores semanticos en la extension.
```

En MIPS, la llamada usa `jal suma` y la funcion regresa con `jr $ra`.
