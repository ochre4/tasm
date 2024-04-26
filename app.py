from flask import Flask, render_template, request

app = Flask(__name__)

class Emulator:
    def __init__(self):
        self.registers = [0] * 8  # Регистры al, bl, cl, dl, el, fl, gl, hl
        self.variables = {}  # Словарь для переменных
        self.register_map = {
            "al": 0, "bl": 1, "cl": 2, "dl": 3,
            "el": 4, "fl": 5, "gl": 6, "hl": 7
        }
        self.code_section = []  # Секция кода
        self.data_section = []  # Секция данных
        self.in_code_section = False  # Флаг секции кода
        self.missing_elements = []

    def parse_program(self, program):
        has_data = has_code = has_start = has_end = False
        lines = program.splitlines()
        for line in lines:
            stripped_line = line.strip().lower()
            if stripped_line == ".data":
                has_data = True
            elif stripped_line == ".code":
                has_code = True
            elif stripped_line == "_start:":
                has_start = True
                self.in_code_section = True
            elif stripped_line == "end _start":
                has_end = True
                self.in_code_section = False
            if self.in_code_section:
                self.code_section.append(line.strip())
            elif has_data or has_code:
                self.data_section.append(line.strip())

        # Проверка на наличие всех необходимых секций
        self.missing_elements = [
            ".data" if not has_data else None,
            ".code" if not has_code else None,
            "_start:" if not has_start else None,
            "end _start" if not has_end else None
        ]
        self.missing_elements = [element for element in self.missing_elements if element is not None]

    def load_variables(self):
        for line in self.data_section:
            parts = line.split()
            if len(parts) == 3 and parts[1].lower() == "db":
                self.variables[parts[0]] = int(parts[2])

    def execute_program(self):
        if self.missing_elements:
            return None  # Возвращаем None, если есть пропущенные элементы
        for instruction in self.code_section:
            instruction = instruction.split()
            if instruction[0].lower() == "call" and instruction[1].lower() == "exitprocess":
                break  # Выход из программы
            self.process_instruction(instruction)
        return self.dump_registers_formatted()  # Возвращаем отформатированные регистры

    def process_instruction(self, instruction):
        cmd = instruction[0].lower()
        if cmd == "mov":
            dest = self.register_map[instruction[1]]
            src = instruction[2]
            if src.isdigit():
                self.registers[dest] = int(src)
            else:
                self.registers[dest] = self.variables[src]
        elif cmd == "add":
            reg1 = self.register_map[instruction[1]]
            reg2 = self.register_map[instruction[2]]
            self.registers[reg1] += self.registers[reg2]
        elif cmd == "sub":
            reg1 = self.register_map[instruction[1]]
            reg2 = self.register_map[instruction[2]]
            self.registers[reg1] -= self.registers[reg2]
        elif cmd == "mul":
            ax_index = self.register_map['al']
            bx_index = self.register_map[instruction[1]]
            self.registers[ax_index] *= self.registers[bx_index]

    def dump_registers(self):
        return ', '.join(f"{name}={value}" for name, value in zip(self.register_map.keys(), self.registers))

    def dump_registers_formatted(self):
        # Формируем строку в нужном формате
        registers_info = (
            f"eax {self.registers[self.register_map['al']]:08X}\n"
            f"ebx {self.registers[self.register_map['bl']]:08X}\n"
            f"ecx {self.registers[self.register_map['cl']]:08X}\n"
            f"edx {self.registers[self.register_map['dl']]:08X}\n"
            f"esi {self.registers[self.register_map['el']]:08X}\n"
            f"edi {self.registers[self.register_map['fl']]:08X}\n"
            f"ebp {self.registers[self.register_map['gl']]:08X}\n"
            f"esp {self.registers[self.register_map['hl']]:08X}\n"
            f"ds  002B\n"  # Допустим, эти значения статичны
            f"es  002B\n"
            f"fs  0053\n"
            f"gs  002B\n"
            f"ss  002B\n"
            f"cs  0023\n"
            f"eip 00401019\n"  # Пример адреса после выполнения кода
        )
        return registers_info

@app.route('/', methods=['GET', 'POST'])
def home():
    program_text = ""
    missing_elements_text = ""  # Переменная для текста о пропущенных элементах
    if request.method == 'POST':
        program_text = request.form['program']
        emulator = Emulator()
        emulator.parse_program(program_text)
        emulator.load_variables()
        result = emulator.execute_program()
        if emulator.missing_elements:
            missing_elements_text = "Отсутствует элемент(ы): " + ", ".join(emulator.missing_elements)
        if not result:
            result = emulator.dump_registers_formatted()
    else:
        result = (
            "eax 00000000\n"
            "ebx 00000000\n"
            "ecx 00000000\n"
            "edx 00000000\n"
            "esi 00000000\n"
            "edi 00000000\n"
            "ebp 00000000\n"
            "esp 00000000\n"
            "ds  002B\n"
            "es  002B\n"
            "fs  0053\n"
            "gs  002B\n"
            "ss  002B\n"
            "cs  0023\n"
            "eip 00401000\n"
        )
    return render_template('index.html', result=result, program_text=program_text, missing_elements_text=missing_elements_text)

if __name__ == '__main__':
    app.run(debug=True)