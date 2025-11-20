#!/usr/bin/python3
# --- encoding UTF-8 ---
""" A simple interpretator of the esoteric language Brainfuck """

from sys import argv, exit as sysexit, stdin
from os.path import exists, abspath, isfile
from time import time
from getch import getche

REG_SIZE_MAX = 30_000
CHAR_SIZE_MAX = 256


class Register:
    """ Simple register """

    def __init__(self) -> None:
        self.reg = [0 for _ in range(REG_SIZE_MAX)]
        self.size = len(self.reg)
        self.pointer = 0

    def reset(self) -> None:
        """ Resetting the register and pointer """
        self.reg = [0 for _ in range(REG_SIZE_MAX)]
        self.size = len(self.reg)
        self.pointer = 0

    def move_left(self, n: int = 1) -> None:
        """ Move pointer to the left """
        self.pointer -= n
        if self.pointer < 0:
            self.pointer = self.size - 1

    def move_right(self, n: int = 1) -> None:
        """ Move pointer to the right """
        self.pointer += n
        if self.pointer >= self.size:
            self.pointer = 0

    def read(self) -> int:
        """ Return the value in current cell """
        return self.reg[self.pointer]

    def write(self, char: str) -> None:
        """ Write value to current cell if possible
            Return True if successful, False otherwise """
        if len(char) > 1:
            char = char[0]
        if char == '\x04':
            num: int = 0
        else:
            num: int = int(ord(char))
        if num < 0:
            num = CHAR_SIZE_MAX + num
        if num >= CHAR_SIZE_MAX:
            num = 0
        self.reg[self.pointer] = num

    def increment(self, n: int = 1) -> None:
        """ Increments a value in the current cell """
        self.reg[self.pointer] += n
        if self.read() >= CHAR_SIZE_MAX:
            self.reg[self.pointer] = CHAR_SIZE_MAX - 1

    def decrement(self, n: int = 1) -> None:
        """ Decrements a value in the current cell """
        self.reg[self.pointer] -= n
        if self.read() <= 0:
            self.reg[self.pointer] = 0

    def print_reg(self, n: int = 5):
        """ Print register cells in 'n' radius """
        lower: int = max(self.pointer - n, 0)
        upper: int = min(self.pointer + n, REG_SIZE_MAX)
        cellsn = ''.join(f"#{i} " for i in range(lower, upper))
        separator = "-" * (len(cellsn) + 1)
        print(separator)
        print(cellsn)
        print(separator)
        print(''.join(f"{i}  " for i in self.reg[lower:upper]))
        print(separator)
        print("pointer: ", self.pointer)


class BFInterpreter:
    """ Class of BFI """

    def __init__(self, isstep: bool = False, use_outinput: bool = False):
        self.register: Register = Register()
        self.text_pos: int = 0
        self.step: bool = isstep
        self.use_outinput: bool = use_outinput
        self.outinput: bytes = b''
        if self.use_outinput:
            print("[INT] Using preinput. To finish input, press CTRL+D")
            self.outinput = stdin.buffer.read()
            print(flush=True)

    def reset(self, isstep: bool | None = None,
              use_outinput: bool | None = None):
        """ Reset """
        self.register.reset()
        self.text_pos = 0
        if isstep is not None:
            self.step = isstep
        if use_outinput is not None and use_outinput:
            print("[INT] Using preinput. To finish input, press CTRL+D")
            self.outinput = stdin.buffer.read()
            print(flush=True)

    def parse(self, text: str, lookup="+-,.<>[]") -> str:
        """ Parse brainfuck program, removing all unessesery chars """
        return ''.join(c for c in text if c in lookup)

    def map_braces(self, program_text: str) -> None:
        """ Find map pairs in program text """
        raw_lbrace: list[int] = []
        raw_rbrace: list[int] = []
        pos: int = 0
        for char in program_text:
            if char == '[':
                raw_lbrace.insert(0, pos)
            elif char == ']':
                raw_rbrace.append(pos)
            pos += 1
        if len(raw_lbrace) != len(raw_rbrace):
            print("\n[ERR] Syntax error: braces mismatch.")
            sysexit(5)
        return self._find_brace_pair(raw_lbrace, raw_rbrace, program_text)

    def _find_brace_pair(self, raw_lbrace: list[int], raw_rbrace: list[int],
                         program_text: str) -> dict[int: int]:
        brace_map: dict[int: int] = {}
        if len(raw_lbrace) == 0:
            return brace_map
        while len(raw_lbrace) > 0:
            complexity: int = 0
            first: int = raw_lbrace[-1]
            last: int = raw_rbrace[-1]
            for i in range(first, last+1):
                char: str = program_text[i]
                if char == "[":
                    complexity += 1
                if char != "]":
                    continue
                complexity -= 1
                if complexity <= 0:
                    map_key = raw_lbrace.pop()
                    map_value = raw_rbrace.pop(raw_rbrace.index(i))
                    program_text = str(program_text[:map_key] + 'x'
                                       + program_text[map_key+1:map_value]+'x'
                                       + program_text[map_value+1:])
                    brace_map[map_key] = map_value
                    break
        return brace_map

    def get_map_key(self, mymap: dict[int: int], map_value: int) -> int:
        """ Get key by value from braces pair map """
        keyval_id = 0
        for val in mymap.values():
            if val == map_value:
                break
            keyval_id += 1
        else:
            raise KeyError("Value not found in dict.")
        return list(mymap.keys())[keyval_id]

    def interprete(self, word: str, brace_map: dict[int: int],
                   no_input: bool = False) -> bool:
        """ Interpretes Brainfuck commands """
        if 0 <= len(word) > 1:
            print("\n[ERR] interpreter got nothing!")
            sysexit(3)
        match word:
            case "+":
                self.register.increment()
            case "-":
                self.register.decrement()
            case "<":
                self.register.move_left()
            case ">":
                self.register.move_right()
            case ".":
                uout = self.register.read()
                print(chr(uout), end='', flush=True)
                if self.step:
                    print(" <- output")
            case ",":
                if self.step:
                    print("> ", end='', flush=True)
                if self.use_outinput and len(self.outinput) > 0:
                    uin = chr(self.outinput[0])
                    self.outinput = self.outinput[1:]\
                        if len(self.outinput) > 1 else b''
                elif no_input or (self.use_outinput and
                                  len(self.outinput) < 1):
                    uin = '\x00'
                else:
                    uin = str(getche())
                if uin in {'', '\x00'}:
                    if uin == '':
                        uin = '\x00'
                    print(flush=True)
                elif uin == '\x04':
                    print("\n[INF] Input interupting symbol. Aborting.")
                    return False
                self.register.write(uin)
                if self.step:
                    print(" <- input" if not self.use_outinput
                          else f"{uin} <- input")
            case "[":  # ]
                if self.register.read() == 0:
                    self.text_pos = brace_map[self.text_pos]
            case "]":
                if self.register.read() != 0:
                    back_pos = self.get_map_key(brace_map, self.text_pos)
                    self.text_pos = back_pos
        return True


class Main:
    """ Main class """

    def __init__(self, get_argv):
        args: list = get_argv[1:] if len(get_argv) > 1 else []
        if len(args) == 0:
            self.print_help()
            sysexit(2)
        if not exists(abspath(args[-1]))\
                or not isfile(abspath(args[-1])):
            print("[ERR] No valid filepath provided.")
            self.print_help()
            sysexit(2)

        self.options = {"step": False, "no-input": False,
                        "dump": False, "preinput": False}
        if '-h' in args or '--help' in args:
            self.print_help()
            sysexit(0)
        if '-s' in args or '--step' in args:
            self.options['step'] = True
        if '-n' in args or '--no-input' in args:
            self.options['no-input'] = True
        if '-d' in args or '--dump' in args:
            self.options['dump'] = True
        if '-p' in args or '--prein' in args:
            self.options['preinput'] = True

        self.filename: str = args[-1]
        self.text: str = ''
        self.text_pos: int = 0
        self.interpreter = BFInterpreter(self.options['step'],
                                         self.options['preinput'])
        self.brace_map: dict[int: int] = {}

    def print_help(self):
        """ Prints Help message """
        print("Brainfuck interpreter written in python3 (quite slow tbh)")
        print("Usage:\n\t[python3] interpreter.py [opts] <file>")
        print("Options:\n\t--help or -h\t\tShow this message")
        print("\t--step or -s\t\tRun in step by step mode")
        print("\t--dump or -d\t\tDump register cells after execution")
        print("\t--no-input or -n\tIgnore any input")
        print("\t--preinput or -p\tProvade an imput before interpreting")
        print("\tNote: file must always be at the end")

    def dump_reg(self):
        """ Dump register cells of the bf program """
        dump_name = self.filename + '.DMP'
        counter = 0
        max_counter = 256
        while exists(abspath(dump_name)) and isfile(abspath(dump_name)):
            if counter == max_counter:
                print("[ERR] Could not set name for dump.",
                      "Please delete old dumps")
                sysexit(1)
            counter += 1
            dump_name = self.filename + '.DMP' + str(counter)
        print("[INF] Dumping bf register.")
        with open(dump_name, 'x', encoding='utf-8') as f:
            lines = "register = [\n"
            lines += ", ".join(str(item) for item in
                               self.interpreter.register.reg)
            lines += '\n]\n'
            f.writelines(lines)
        print("[INF] Done. Saved as", dump_name)

    def run(self, filename: str = None, rerun: bool = False) -> None:
        """ Main function """
        self.interpreter.reset()
        if filename is not None:
            self.filename: str = filename
        if not exists(abspath(self.filename))\
                or not isfile(abspath(self.filename)):
            raise FileNotFoundError("Provided invalid file or it was deleted.")

        self.text_pos = self.interpreter.text_pos

        if not rerun:
            loaded_program = ''
            with open(self.filename, 'r', encoding='utf-8') as file:
                loaded_program = (str(file.read()))
                self.text = loaded_program
        filesize = len(self.text)
        print(f"[INF] File '{self.filename}' loaded",
              f"({str(filesize / 1024) + " KB" if filesize > 1024
                  else str(filesize) + ' B'})")
        print("[INF] Parsing...")
        self.text = self.interpreter.parse(self.text)
        filesize = len(self.text)
        self.brace_map = self.interpreter.map_braces(self.text)
        print("[INF] Program parsed",
              f"({str(filesize / 1024) + " KB" if filesize > 1024
                  else str(filesize) + ' B'} parsed)")
        print("[INF] Use CTRL+C or CTRL+D to interrupt the",
              "program. If need to write 0 to cell, use CTRL+2" if
              not self.options['no-input'] and not self.options['preinput']
              else "program")

        start_time = time()
        while self.text_pos < filesize:
            symbol = self.text[self.text_pos]
            if isinstance(symbol, str) and symbol != '':
                if not self.interpreter.interprete(symbol, self.brace_map,
                                                   self.options["no-input"]):
                    break
            self.text_pos = self.interpreter.text_pos
            self.text_pos += 1
            self.interpreter.text_pos = self.text_pos
            if self.options["step"]:
                self.interpreter.register.print_reg()
                print("symbol:", symbol, ", text_pos: ", self.text_pos)
                input()
        elapsed = time() - start_time
        el_mins = elapsed // 60
        el_sec = elapsed % 60
        print(f"\n[INF] Done. Elapsed {el_mins}m {el_sec}s")
        if self.options['dump']:
            self.dump_reg()


if __name__ == "__main__":
    main = Main(argv)
    try:
        main.run()
    except (EOFError, KeyboardInterrupt):
        print("\n[INF] Execution interupted")
        if main.options['dump']:
            main.dump_reg()
        sysexit(69)
