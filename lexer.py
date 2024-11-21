import re
import os

optimization = True

# Словарь замен
repl = {
    # std functions
    r"log\((.*?)\).end": r'cout << \1 << " ";',
    r"log\((.*?)\)": r"cout << \1 << endl;",
    r"put\('(.*?)'\) as (\w+) (\w+)": r'cout << "\1";\n    cin >> \3;',

    # boolean conversion
    r"\bTrue\b": "true",
    r"\bFalse\b": "false",
    r"\bNone\b": '"none"',

    # time
    r"wait\((\d)\)": r'sleep_for(seconds(\1));',

    # variable operations
    r'(\w+)\s*\+\= 1': r'\1++;',
    r'(\w+)\s*\-\= 1': r'\1--;',

    # symbols
    r"'": r'"',  # Replace single quotes with double quotes
    r"#": "//",  # Replace comments
}

imports = {
    r"\bwait\b": "#include <thread>\n#include <chrono>\nusing namespace this_thread;\nusing namespace chrono;",
}

# Функция определения типа переменной
def get_var_type(value: str):
    value = value.strip()

    # Преобразуем строки с одинарных кавычек на двойные
    if value.startswith("'") and value.endswith("'"):
        value = f'"{value[1:-1]}"'

    # Проверяем на целое число
    if re.match(r"^\d+$", value):
        return "int", value
    # Проверяем на число с плавающей точкой
    elif re.match(r"^\d+\.\d+$", value):
        return "float", value
    # Проверяем на строку
    elif value.startswith('"') and value.endswith('"'):
        return "string", value
    # Проверяем на булевое значение
    elif value in {"true", "false"}:
        return "bool", value
    # Проверяем на списки
    elif value.startswith("[") and value.endswith("]"):
        return "list", value
    # Проверяем на множества
    elif value.startswith("{") and value.endswith("}"):
        return "set", value
    # Тип auto: если переменная не попадает в вышеописанные типы, пытаемся вывести auto
    else:  # Идентификаторы, как переменные или имена функций
        return "auto", value

# Функция обработки шаблонов <...> в строках
def process_placeholders(line):
    # Ищем все конструкции вида <...>
    matches = re.findall(r"<(.*?)>", line)
    for match in matches:
        # Заменяем <var> на << var << в C++.
        line = line.replace(f"<{match}>", f'" << {match} << "')
    return line

def optimize_cpp_code(cpp_code: str) -> str:
    """
    Optimizes the C++ code by removing unnecessary spaces, formatting includes,
    and ensuring minimal but correct structure.
    """
    # List of transformations to apply
    transformations = [
        (r"\s+", " "),  # Replace multiple spaces with one

        (r"\s*{\s*", "{"),  # Remove spaces before and after '{'
        (r"\s*}\s*", "}"),  # Remove spaces before and after '}'
        (r"\s*\(\s*", "("),  # Remove spaces before and after '('
        (r"\s*\)\s*", ")"),  # Remove spaces before and after ')'

        (r"\s*;\s*", ";"),  # Remove spaces before and after ';'

        (r'"{2} << ', ""),  # Remove "" << for redundant stream operations
        (r'"{2} >> ', ""),  # Remove "" >> for redundant stream operations

        (r" << ", "<<"),  # Remove spaces around '<<'
        (r" >> ", ">>"),  # Remove spaces around '>>'

        (r" = ", "="),  # Remove spaces around '='
        (r" < ", "<"),  # Remove spaces around '<'
        (r" > ", ">"),  # Remove spaces around '>'

        (r"(#include <.*?>)", r"\1\n"),  # Ensure each include is on its own line
    ]

    # Apply all transformations
    optimized = cpp_code
    for pattern, replacement in transformations:
        optimized = re.sub(pattern, replacement, optimized)

    return optimized

# Главная функция компиляции
def compile_lint_to_cpp(input_file: str, output_file: str):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' does not exist.")

    # Считываем код из файла
    with open(input_file, "r") as file:
        lint_code = file.readlines()

    # Определяем, какие include нужно добавить
    variable_declarations = set()  # Set to track already declared variables
    cpp_code = []
    used_imports = set()  # Множество для хранения использованных импортов

    for line in lint_code:
        stripped_line = line.strip()  # Убираем лишние пробелы

        # Проверяем, если строка соответствует ключам в imports
        for pattern, import_code in imports.items():
            if re.search(pattern, stripped_line) and pattern not in used_imports:
                used_imports.add(pattern)  # Помечаем, что импорт добавлен

        # Обрабатываем f-строки с шаблонами
        stripped_line = process_placeholders(stripped_line)

        # Переменные
        var_match = re.match(r"(\w+)\s*:\s*(.+)", stripped_line)
        if var_match:
            var_name, var_value = var_match.groups()
            var_value = var_value.strip()

            # Check if variable has already been declared
            if var_name not in variable_declarations:
                var_type, var_value = get_var_type(var_value)
                cpp_code.append(f"    {var_type} {var_name} = {var_value};")
                variable_declarations.add(var_name)  # Mark variable as declared
            else:
                cpp_code.append(f"    {var_name} = {var_value};")
            continue  # Skip further processing for this line

        # Циклы
        if stripped_line.startswith("loop {"):
            cpp_code.append("    while (true) {")
            continue
        elif stripped_line == "}":
            cpp_code.append("    }")
            continue
        loop_for_match = re.match(r"loop (\w+) for (\d+) {", stripped_line)
        if loop_for_match:
            var_name, count = loop_for_match.groups()
            if var_name not in variable_declarations:
                cpp_code.append(f"    for (int {var_name} = 0; {var_name} < {count}; {var_name}++) {{")
                variable_declarations.add(var_name)  # Mark loop variable as declared
            else:
                cpp_code.append(f"    for ({var_name} = 0; {var_name} < {count}; {var_name}++) {{")
            continue
        elif "stop" in stripped_line:
            cpp_code.append("    break;")
            continue

        # Проверки
        stripped_line = re.sub(r"\bif\s+(.*?)\s*{", r"if (\1) {", stripped_line)
        stripped_line = re.sub(r"\belif\s+(.*?)\s*{", r"else if (\1) {", stripped_line)
        stripped_line = re.sub(r"\belse\s*{", r"else {", stripped_line)

        # Заменяем and/or
        stripped_line = stripped_line.replace(" and ", " && ")
        stripped_line = stripped_line.replace(" or ", " || ")

        # Применяем замены из словаря
        for pattern, replacement in repl.items():
            stripped_line = re.sub(pattern, replacement, stripped_line)

        cpp_code.append(f"    {stripped_line}")  # Добавляем отступ

    # Формируем итоговый код
    complete_code = "#include <iostream>\nusing namespace std;\n"

    # Добавляем импорты, если они использовались
    for imp in used_imports:
        complete_code += imports[imp] + "\n"

    complete_code += "int main() {\n"

    # Добавляем остальной код
    for line in cpp_code:
        complete_code += line + "\n"

    complete_code += "    return 0;\n}\n"

    if optimization:
        complete_code = optimize_cpp_code(complete_code)

    # Сохраняем скомпилированный и оптимизированный код
    with open(output_file, "w") as file:
        file.write(complete_code)

    print(f"Compilation and optimization complete. Output saved to '{output_file}'")
