#!/usr/bin/env python3
"""
One-command setup for code-diagram-mcp. Cross-platform (macOS/Linux/Windows).

Usage:
    python3 setup.py /path/to/your-codebase
    python3 setup.py /path/to/your-codebase --all-languages

What it does:
    1. Installs tree-sitter + C/Python grammars
    2. Auto-detects project language/framework
    3. Builds AST index (functions, call graph, types)
    4. Prints MCP config snippet for ~/.hermes/config.yaml
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=False, **kwargs)


def get_python() -> str:
    """Return the python executable that's running this script."""
    return sys.executable


def pip_install(packages: list[str]) -> bool:
    """Install packages, handling PEP 668 on macOS Homebrew Python."""
    python = get_python()
    args = [python, "-m", "pip", "install", "--quiet"]

    # macOS Homebrew Python needs --break-system-packages (PEP 668)
    result = run(args + ["--break-system-packages"] + packages)
    if result.returncode != 0:
        # Try without the flag (Linux system Python, Windows, venv)
        result = run(args + packages)
    return result.returncode == 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    project_root = os.path.abspath(sys.argv[1])
    all_langs = "--all-languages" in sys.argv

    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory.")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent

    print("═══ code-diagram-mcp setup ═══")
    print(f"  Platform: {platform.system()}")
    print(f"  Python:   {sys.version.split()[0]}")
    print()

    # 1. Install dependencies
    print("[1/4] Installing dependencies...")
    packages = ["tree-sitter>=0.24", "tree-sitter-c>=0.23", "tree-sitter-python>=0.23"]
    if all_langs:
        packages += [
            "tree-sitter-go>=0.23", "tree-sitter-rust>=0.23",
            "tree-sitter-java>=0.23", "tree-sitter-javascript>=0.23",
            "tree-sitter-typescript>=0.23",
        ]
    if pip_install(packages):
        print("       ✓ done")
    else:
        print("       ⚠ pip install had issues — trying to continue...")
    print()

    # 2. Detect project
    print(f"[2/4] Scanning project: {project_root}")
    run([get_python(), str(script_dir / "scripts" / "init-project.py"), project_root])
    print()

    # 3. Build index
    print(f"[3/4] Building AST index...")
    run([get_python(), str(script_dir / "scripts" / "build-index-ts.py"),
         "--project", project_root])
    print()

    # 4. Print MCP config
    print("[4/4] MCP config — add to ~/.hermes/config.yaml under mcp_servers:")
    print()
    print("  code-diagram:")
    print(f"    command: {get_python()}")
    print("    args:")
    print(f"    - {script_dir / 'mcp_server.py'}")
    print("    - --project")
    print(f"    - {project_root}")
    print()
    print("Then /reload-mcp in Hermes. Done.")


if __name__ == "__main__":
    main()
