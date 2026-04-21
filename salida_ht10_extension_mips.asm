.data
    a: .word 0
    b: .word 0
    c: .word 0
    d: .word 0
    salto: .asciiz "\n"

.text
.globl main

suma:
    add $v0, $a0, $a1
    jr $ra

main:
    li $t0, 10
    sw $t0, a
    li $t1, 20
    sw $t1, b
    lw $a0, a
    lw $a1, b
    jal suma
    lw $t2, b
    add $t3, $v0, $t2
    sw $t3, c
    li $t4, 30
    ble $t3, $t4, L_fin_si
    move $a0, $t3
    li $v0, 1
    syscall
    la $a0, salto
    li $v0, 4
    syscall
    li $t5, 10
    sub $t6, $t3, $t5
    sw $t6, d
L_fin_si:
    lw $a0, d
    li $v0, 1
    syscall
    li $v0, 10
    syscall
