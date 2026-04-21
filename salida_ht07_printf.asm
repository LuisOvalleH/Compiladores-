default rel
section .data
    fmt_int db "%ld", 0
    fmt_str db "%s", 0
    fmt_newline db 10, 0
    str_0 db 73, 110, 105, 99, 105, 111, 32, 99, 111, 110, 32, 112, 114, 105, 110, 116, 102, 58, 32, 0
    str_1 db 84, 111, 116, 97, 108, 32, 97, 99, 117, 109, 117, 108, 97, 100, 111, 58, 0

section .bss
    var_i resq 1
    var_total resq 1
    var_x resq 1

section .text
    extern printf
    global main

main:
    push rbp
    mov rbp, rsp
    mov rax, 1
    mov [var_x], rax
    mov rax, 0
    mov [var_total], rax
    lea rsi, [str_0]
    lea rdi, [fmt_str]
    xor eax, eax
    call printf
    mov rax, [var_x]
    mov rsi, rax
    lea rdi, [fmt_int]
    xor eax, eax
    call printf
    lea rdi, [fmt_newline]
    xor eax, eax
    call printf
    mov rax, 0
    mov [var_i], rax
L_for_ini_0:
    mov rax, [var_i]
    push rax
    mov rax, 4
    mov rbx, rax
    pop rax
    cmp rax, rbx
    setl al
    movzx rax, al
    cmp rax, 0
    je L_for_fin_1
    mov rax, [var_total]
    push rax
    mov rax, [var_i]
    mov rbx, rax
    pop rax
    add rax, rbx
    mov [var_total], rax
    mov rax, [var_i]
    push rax
    mov rax, 1
    mov rbx, rax
    pop rax
    add rax, rbx
    mov [var_i], rax
    jmp L_for_ini_0
L_for_fin_1:
    lea rsi, [str_1]
    lea rdi, [fmt_str]
    xor eax, eax
    call printf
    lea rdi, [fmt_newline]
    xor eax, eax
    call printf
    mov rax, [var_total]
    mov rsi, rax
    lea rdi, [fmt_int]
    xor eax, eax
    call printf
    lea rdi, [fmt_newline]
    xor eax, eax
    call printf
    mov rax, 0
    jmp L_fin_main
    mov eax, 0
L_fin_main:
    leave
    ret
