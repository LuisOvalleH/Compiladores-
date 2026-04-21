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
