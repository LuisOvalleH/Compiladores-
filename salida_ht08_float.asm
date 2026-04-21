default rel
section .data
    fmt_int db "%ld", 0
    fmt_float db "%f", 0
    fmt_str db "%s", 0
    fmt_newline db 10, 0
    float_const_0 dq 125.50
    float_const_1 dq 15.25
    float_const_2 dq 0.12
    str_0 db 84, 111, 116, 97, 108, 32, 99, 111, 110, 32, 99, 111, 109, 97, 32, 102, 108, 111, 116, 97, 110, 116, 101, 58, 32, 0

section .bss
    var_descuento resq 1
    var_impuesto resq 1
    var_precio resq 1
    var_total resq 1

section .text
    extern printf
    global main

main:
    push rbp
    mov rbp, rsp
    movsd xmm0, [float_const_0]
    movsd [var_precio], xmm0
    movsd xmm0, [float_const_1]
    movsd [var_descuento], xmm0
    movsd xmm0, [var_precio]
    sub rsp, 8
    movsd [rsp], xmm0
    movsd xmm0, [var_descuento]
    movsd xmm1, [rsp]
    add rsp, 8
    subsd xmm1, xmm0
    movsd xmm0, xmm1
    sub rsp, 8
    movsd [rsp], xmm0
    movsd xmm0, [float_const_2]
    movsd xmm1, [rsp]
    add rsp, 8
    mulsd xmm1, xmm0
    movsd xmm0, xmm1
    movsd [var_impuesto], xmm0
    movsd xmm0, [var_precio]
    sub rsp, 8
    movsd [rsp], xmm0
    movsd xmm0, [var_descuento]
    movsd xmm1, [rsp]
    add rsp, 8
    subsd xmm1, xmm0
    movsd xmm0, xmm1
    sub rsp, 8
    movsd [rsp], xmm0
    movsd xmm0, [var_impuesto]
    movsd xmm1, [rsp]
    add rsp, 8
    addsd xmm1, xmm0
    movsd xmm0, xmm1
    movsd [var_total], xmm0
    lea rax, [str_0]
    mov rsi, rax
    lea rdi, [fmt_str]
    mov eax, 0
    call printf
    movsd xmm0, [var_total]
    lea rdi, [fmt_float]
    mov eax, 1
    call printf
    lea rdi, [fmt_newline]
    mov eax, 0
    call printf
    mov rax, 0
    jmp L_fin_main
    mov eax, 0
L_fin_main:
    leave
    ret
