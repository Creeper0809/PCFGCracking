#!/usr/bin/env python3
"""
Script to auto-generate __init__.py files that import all submodules and functions.
Usage: python generate_init_imports.py path/to/pcfg_lib
"""
import os
import re

INIT_FILENAME = '__init__.py'
PY_SUFFIX = '.py'

MODULE_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*\.py$')

def generate_init(dirpath):
    items = []
    for name in sorted(os.listdir(dirpath)):
        full = os.path.join(dirpath, name)
        if os.path.isdir(full) and os.path.exists(os.path.join(full, INIT_FILENAME)):
            items.append((name, None))
        elif MODULE_RE.match(name) and name != INIT_FILENAME:
            mod = name[:-3]
            items.append((mod, None))
    if not items:
        return
    lines = ["# Auto-generated __init__.py", ""]
    for mod, _ in items:
        lines.append(f"from .{mod} import *")
    content = "\n".join(lines) + "\n"
    # write __init__.py
    init_path = os.path.join(dirpath, INIT_FILENAME)
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Generated imports in {init_path}")


def main(root):
    for dirpath, dirnames, filenames in os.walk(root):
        # skip hidden dirs
        if any(part.startswith('.') for part in dirpath.split(os.sep)):
            continue
        # Only process package dirs (containing __init__.py)
        if INIT_FILENAME in filenames:
            generate_init(dirpath)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    root_dir = sys.argv[1]
    main(root_dir)
