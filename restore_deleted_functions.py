import os
import re
import ast
from datetime import datetime

BACKUP_DIR = '/backups/unused_code'
LOG_FILE = 'removed_functions_log.md'
RESTORE_LOG = 'restoration_log.md'

def list_backups():
    if not os.path.isdir(BACKUP_DIR):
        print(f"Backup directory '{BACKUP_DIR}' not found.")
        return []
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.py')]
    files.sort()
    return files

def select_from_list(items, prompt):
    if not items:
        return None
    for idx, item in enumerate(items, 1):
        print(f"{idx}. {item}")
    while True:
        choice = input(prompt)
        if not choice.isdigit():
            print("Please enter a valid number.")
            continue
        idx = int(choice) - 1
        if 0 <= idx < len(items):
            return items[idx]
        print("Choice out of range.")

# Parsing removed_functions_log.md
FUNC_PATTERN = re.compile(r'^[-*]\s*(?P<name>\w+)(?:\s*@\s*line\s*(?P<line>\d+))?')
FILE_PATTERN = re.compile(r'file:\s*(.*\.py)', re.IGNORECASE)


def parse_removed_log():
    if not os.path.isfile(LOG_FILE):
        print(f"Log file '{LOG_FILE}' not found.")
        return []
    entries = []
    current_file = None
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            file_match = FILE_PATTERN.search(line)
            if file_match:
                current_file = file_match.group(1)
                continue
            func_match = FUNC_PATTERN.match(line)
            if func_match and current_file:
                func_name = func_match.group('name')
                line_no = func_match.group('line')
                line_no = int(line_no) if line_no else None
                entries.append({'file': current_file, 'function': func_name, 'line': line_no})
    return entries

def filter_entries_by_backup(entries, backup_name):
    # backup_name like 'utils_20240101.py' => basename 'utils.py'
    m = re.match(r'(.*)_\d{8}\.py$', backup_name)
    if not m:
        return []
    base = m.group(1) + '.py'
    return [e for e in entries if os.path.basename(e['file']) == base]


def get_function_source(backup_path, func_name):
    try:
        with open(backup_path, 'r') as f:
            source = f.read()
    except OSError:
        print(f"Failed to read backup file '{backup_path}'.")
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        print(f"Backup file '{backup_path}' is corrupted.")
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            lines = source.splitlines()
            start = node.lineno - 1
            end = node.end_lineno
            func_lines = lines[start:end]
            if func_lines:
                func_lines[0] += "  # restored from backup"
            return "\n".join(func_lines) + "\n"
    print(f"Function '{func_name}' not found in backup.")
    return None


def insert_into_file(file_path, content, line_no=None):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except OSError:
        print(f"Failed to open target file '{file_path}'.")
        return False
    if line_no is None or line_no > len(lines):
        line_no = len(lines)
    else:
        line_no = max(0, line_no - 1)
    lines[line_no:line_no] = [content]
    try:
        with open(file_path, 'w') as f:
            f.writelines(lines)
    except OSError:
        print(f"Failed to write to target file '{file_path}'.")
        return False
    return True


def log_restoration(file_path, func_names):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"{timestamp} | {file_path} | {', '.join(func_names)}\n"
    with open(RESTORE_LOG, 'a') as f:
        f.write(entry)


def main():
    backups = list_backups()
    if not backups:
        return
    backup = select_from_list(backups, "Select backup file: ")
    if not backup:
        return
    entries = parse_removed_log()
    relevant = filter_entries_by_backup(entries, backup)
    if not relevant:
        print("No functions found in log for this backup.")
        return
    print("Functions available for restoration:")
    for idx, e in enumerate(relevant, 1):
        line_info = f" at line {e['line']}" if e['line'] else ''
        print(f"{idx}. {e['function']} (file: {e['file']}{line_info})")
    choice = input("Select functions by number (comma separated) or 'all': ")
    if choice.strip().lower() == 'all':
        selected = relevant
    else:
        numbers = [int(x)-1 for x in re.split(r'[ ,]+', choice.strip()) if x.isdigit()]
        selected = [relevant[i] for i in numbers if 0 <= i < len(relevant)]
    if not selected:
        print("No valid functions selected.")
        return
    backup_path = os.path.join(BACKUP_DIR, backup)
    restored = []
    for e in selected:
        code = get_function_source(backup_path, e['function'])
        if code is None:
            continue
        success = insert_into_file(e['file'], code, e['line'])
        if success:
            restored.append(e['function'])
    if restored:
        log_restoration(selected[0]['file'], restored)
        print(f"Restored functions: {', '.join(restored)}")
    else:
        print("No functions were restored.")

if __name__ == '__main__':
    main()
