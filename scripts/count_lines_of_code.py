"""
Count the number of lines of code in the project.
"""

# pylint: disable=redefined-outer-name, broad-exception-caught

import os

EXCLUDE_DIRS = {
    "venv",
    "env",
    "__pycache__",
    "build",
    "dist",
    ".git",
    ".idea",
    ".mypy_cache",
}
SKIP_HIDDEN_DIRS = True


def count_lines_of_code(path="."):
    """
    Count the number of lines of code in Python files within a directory and its subdirectories.
    """
    total_no_of_lines = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [
            d
            for d in dirs
            if d not in EXCLUDE_DIRS and not (SKIP_HIDDEN_DIRS and d.startswith("."))
        ]

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = [line for line in f if line.strip()]
                        count = len(lines)
                        total_no_of_lines += count
                        print(f"[+] {file_path}: {count} lines")
                except Exception as e:
                    print(f"[!] Skipped {file_path}: {e}")
    return total_no_of_lines


if __name__ == "__main__":
    total_no_of_lines = count_lines_of_code("./..")
    print("\n========================")
    print(f"total_no_of_lines lines of code: {total_no_of_lines}")
