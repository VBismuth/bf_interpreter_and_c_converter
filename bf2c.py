#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Brainfuck to C translator """
from sys import argv, exit as sysexit
from os.path import isfile

BF_SYNTAX = {'+', '-', '[', ']', '.', ',', '<', '>'}
C_HEAD = "#include <stdio.h>\n" +\
    "char array[0xffff];" +\
    "int main(){" +\
    "char *ptr = array;" +\
    "setvbuf(stdout, NULL, _IONBF, 0);" +\
    "int c;\n"
C_TAIL = "\nputchar('\\n');\nreturn *ptr;}"


def bf_strip(program: str) -> str:
    """ return only bf chars """
    return "".join(str(i) for i in program if
                   i in BF_SYNTAX)


def bf_parse(program: str) -> str:
    """ Parsing program stripped text into C language """
    res: str = C_HEAD
    for command in program:
        if command not in BF_SYNTAX:
            continue
        match command:
            case "+":
                res += '++*ptr;'
            case "-":
                res += '--*ptr;'
            case "[":
                res += '\nwhile (*ptr) {'
            case "]":
                res += '}\n'
            case "<":
                res += '--ptr;'
            case ">":
                res += '++ptr;'
            case ".":
                res += 'putchar(*ptr);'
            case ",":
                res += 'c=getchar();\nif (c >= 0) *ptr=c;'
            case _:
                print(f"Unrecognazed pattern '{command}' at bf_parse() !")
                sysexit(-1)
    res += C_TAIL
    return res


def bf_minimize(unminimized: str) -> str:
    """ Minimizing brainfuck program
        by deleting meaningless instructs """
    res: str = unminimized
    max_iters: int = len(res)
    bad_patterns: set[str] = {"<>", "><", '+-', '-+'}
    while any(i in res for i in bad_patterns) and max_iters > 0:
        max_iters -= 1
        for pattern in bad_patterns:
            if pattern not in res:
                continue
            res = res.replace(pattern, '')
    program_start: int = 0
    if res.startswith('['):  # ] first [] in the program will be skipped
        open_braces_count: int = 0
        for idx, char in enumerate(res):
            if char == '[':  # ]
                open_braces_count += 1
            elif char == ']':
                open_braces_count -= 1
            elif open_braces_count <= 0:
                break
            if open_braces_count <= 0:
                program_start = min(idx + 1, len(res) - 1)
    res = _bf_braces_cleaner(res[program_start:])
    return res


def _bf_braces_cleaner(unsolved: str) -> str:
    current: str = unsolved
    first_brace: int = -1
    pointer: int = 0
    f_changed: bool = False
    f_stop = False

    while not f_stop:
        found: str = current[pointer]
        if found == '[':  # ]
            first_brace = pointer
        elif found == ']' and first_brace >= 0:
            current = current[:first_brace] + current[pointer + 1:]
            first_brace = -1
            f_changed = True

        if first_brace >= 0 and pointer - first_brace >= 1:
            first_brace = -1

        pointer += 1

        if pointer >= len(current):
            pointer = 0
            f_stop = not f_changed
            f_changed = False
    return current


def bf_optimize(unoptimized: str) -> str:
    """ Optimize bf code to intermidate bfo before C """
    res: str = ''
    if len(unoptimized) == 0:
        return ''
    char: str = unoptimized[0]
    count: int = 1
    for symbol in unoptimized[1:]:
        if char != symbol or char in {'[', ']', '.', ','}:
            res += _opti_instruct(char, count)
            char = symbol
            count = 1
        else:
            count += 1
    if char != '':
        res += _opti_instruct(char, count)
    return res


def _opti_instruct(instruct: str, repeat: int) -> str:
    full_separator: str = ';'
    num_separator: str = '='
    res: str = ''
    match instruct:
        case "+":
            res = 'a'
            res += full_separator if repeat <= 1\
                else num_separator + str(repeat) + full_separator
        case "-":
            res = 's'
            res += full_separator if repeat <= 1\
                else num_separator + str(repeat) + full_separator
        case "[":
            res = '{' + full_separator
        case "]":
            res = '}' + full_separator
        case "<":
            res = 'ml'
            res += full_separator if repeat <= 1\
                else num_separator + str(repeat) + full_separator
        case ">":
            res = 'mr'
            res += full_separator if repeat <= 1\
                else num_separator + str(repeat) + full_separator
        case ".":
            res = 'ptch' + full_separator
        case ",":
            res = 'gtch' + full_separator
        case _:
            print(f"Unrecognazed pattern '{instruct}' at _opti_instruct() !")
            sysexit(-1)
    return res


def bf_optiparse(optimized: str) -> str:
    """ Parse optimized program """
    res: str = C_HEAD
    program: list[str] = optimized.split(';')
    for command in program:
        if command == '':
            continue
        num_split: str = command.split('=')
        token: str = num_split[0] if len(num_split) > 0 else ''
        repeat: str = num_split[1] if len(num_split) == 2 else '1'
        match token:
            case "a":
                if repeat == '1':
                    res += '++*ptr;'
                else:
                    res += f'*ptr+={repeat};'
            case "s":
                if repeat == '1':
                    res += '--*ptr;'
                else:
                    res += f'*ptr-={repeat};'
            case "{":
                res += '\nwhile (*ptr) {'
            case "}":
                res += '}\n'
            case "ml":
                if repeat == '1':
                    res += '--ptr;'
                else:
                    res += f'ptr-={repeat};'
            case "mr":
                if repeat == '1':
                    res += '++ptr;'
                else:
                    res += f'ptr+={repeat};'
            case "ptch":
                res += 'putchar(*ptr);'
            case "gtch":
                res += 'c=getchar();\nif (c >= 0) *ptr=c;'
            case '':
                print("Got '' from program! Command:", command)
            case _:
                print(f"Unrecognazed pattern '{token}' at bf_optiparse() !")
                sysexit(-1)
    res += C_TAIL
    return res


def _print_help():
    print("Brainfuck to C translator V0.9")
    print("Usage:\tbf2c [options] <file>")
    print("Options:",
          "\n\t-h or --help\t\t\tPrints",
          "this message",
          "\n\t-o or --optimize\t\tUse",
          "optimized, non 1-to-1 translation to C code",
          "\n\t\t--o-save\t\tSave",
          "optimized intercode into file <file>o. Needs -o",
          "\n\t-s or --save-code\t\tSave",
          "stripped and minimized code into file <file>_mini.bf",
          )


if __name__ == "__main__":
    args: list[str] = argv
    if '-h' in args or "--help" in args:
        _print_help()
        sysexit(0)
    if len(args) < 2:
        print("ERROR: no file provided!")
        _print_help()
        sysexit(-2)
    if not str(args[-1]).endswith(('.bf', '.b')):
        print(f"ERROR: this is not bf file: '{args[-1]}'!")
        _print_help()
        sysexit(-3)
    if not isfile(args[-1]):
        print(f"ERROR: file '{args[-1]}' not found!")
        _print_help()
        sysexit(-3)
    IS_OPTIMIZE: bool = "-o" in args or '--optimise' in args
    IS_KEEP_CODE: bool = "-s" in args or '--save-code' in args
    IS_KEEP_OPTI: bool = IS_OPTIMIZE and '--o-save' in args
    FILENAME = args[-1]
    SAVENAME = FILENAME
    SAVENAME = SAVENAME.replace('.bf', '.c')\
        if SAVENAME.endswith('.bf') else SAVENAME.replace('.b', '.c')

    BFPROGRAM = ''
    with open(FILENAME, 'r', encoding='utf-8') as f:
        BFPROGRAM = f.read()
    print(f"Program {FILENAME} loaded.")
    print("Parsing...")
    BFPROGRAM = bf_strip(BFPROGRAM)
    BFPROGRAM = bf_minimize(BFPROGRAM)
    if IS_OPTIMIZE:
        BFOPROGRAM: str = bf_optimize(BFPROGRAM)
        CPROGRAM = bf_optiparse(BFOPROGRAM)
    else:
        CPROGRAM = bf_parse(BFPROGRAM)
    print("Parsing done")

    if IS_KEEP_CODE:
        SAVENAME_MIN_BF = FILENAME.replace(".b", '_mini.b')
        print(f"Saving minimized code as {SAVENAME_MIN_BF}")
        with open(SAVENAME_MIN_BF, 'w+', encoding='utf-8') as f:
            f.write(BFPROGRAM)

    if IS_KEEP_OPTI:
        SAVENAME_OPTI = FILENAME + 'o'
        print(f"Saving optimized code as {SAVENAME_OPTI}")
        with open(SAVENAME_OPTI, 'w+', encoding='utf-8') as f:
            f.write(BFOPROGRAM)

    print(f"Saving as {SAVENAME}")
    with open(SAVENAME, 'w+', encoding='utf-8') as f:
        f.write(CPROGRAM)
    print("Done")
    sysexit(0)
