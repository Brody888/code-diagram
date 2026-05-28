#!/usr/bin/env python3
"""
One-command setup for code-diagram-mcp. Cross-platform (macOS/Linux/Windows).

Usage:
    python3 setup.py /path/to/your-codebase
    python3 setup.py /path/to/your-codebase --tool claude
    python3 setup.py /path/to/your-codebase --all-languages

Supports: Hermes Agent, Claude Code, Codex CLI, OpenClaw — all via MCP.

What it does:
    1. Installs tree-sitter + C/Python grammars
    2. Auto-detects project language/framework
    3. Builds AST index (functions, call graph, types)
    4. Prints MCP config for your AI coding tool
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=False, **kwargs)


def get_python() -> str:
    return sys.executable


def pip_install(packages: list[str]) -> bool:
    python = get_python()
    args = [python, "-m", "pip", "install", "--quiet"]
    result = run(args + ["--break-system-packages"] + packages)
    if result.returncode != 0:
        result = run(args + packages)
    return result.returncode == 0


def print_hermes_config(python: str, server_path: str, project: str):
    print("Add to ~/.hermes/config.yaml under mcp_servers:")
    print()
    print("  code-diagram:")
    print(f"    command: {python}")
    print("    args:")
    print(f"    - {server_path}")
    print("    - --project")
    print(f"    - {project}")
    print()
    print("Then /reload-mcp in Hermes.")


def print_claude_config(python: str, server_path: str, project: str):
    config = {
        "mcpServers": {
            "code-diagram": {
                "command": python,
                "args": [server_path, "--project", project],
            }
        }
    }
    print("Save as .mcp.json (project root) or ~/.claude/mcp.json:")
    print()
    print(json.dumps(config, indent=2))
    print()
    # Try auto-configure if claude CLI is available
    try:
        result = subprocess.run(
            ["claude", "mcp", "add", "code-diagram", "--",
             python, server_path, "--project", project],
            check=False, capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("✓ Auto-configured via `claude mcp add`. Restart Claude Code.")
            return
    except FileNotFoundError:
        pass
    print("Or if claude CLI is installed: claude mcp add code-diagram -- ...")


def print_codex_config(python: str, server_path: str, project: str):
    print("Add to ~/.codex/config.toml or ~/.config/codex/config.toml:")
    print()
    print("[[mcp_servers]]")
    print('name = "code-diagram"')
    print(f'command = "{python}"')
    print(f'args = ["{server_path}", "--project", "{project}"]')
    print()
    print("Then restart Codex.")


def print_openclaw_config(python: str, server_path: str, project: str):
    print("Add to your OpenClaw config.yaml under mcp_servers:")
    print()
    print("  code-diagram:")
    print(f"    command: {python}")
    print("    args:")
    print(f"    - {server_path}")
    print("    - --project")
    print(f"    - {project}")
    print()
    print("Then restart OpenClaw.")


CONFIGS = {
    "hermes":   ("Hermes Agent", print_hermes_config),
    "claude":   ("Claude Code",  print_claude_config),
    "codex":    ("Codex CLI",    print_codex_config),
    "openclaw": ("OpenClaw",     print_openclaw_config),
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--tool=")]
    tool = "hermes"
    for a in sys.argv[1:]:
        if a.startswith("--tool="):
            tool = a.split("=", 1)[1]
        elif a == "--tool":
            idx = sys.argv.index("--tool")
            if idx + 1 < len(sys.argv):
                tool = sys.argv[idx + 1]

    if len(args) < 1 or args[0] in ("-h", "--help"):
        print(__doc__)
        print("Tools:", ", ".join(CONFIGS))
        sys.exit(0)

    project_root = os.path.abspath(args[0])
    all_langs = "--all-languages" in sys.argv

    if not os.path.isdir(project_root):
        print(f"Error: '{project_root}' is not a directory.")
        sys.exit(1)

    if tool not in CONFIGS:
        print(f"Unknown tool '{tool}'. Options: {', '.join(CONFIGS)}")
        sys.exit(1)

    tool_name, print_config = CONFIGS[tool]
    script_dir = Path(__file__).resolve().parent

    print("═══ code-diagram-mcp setup ═══")
    print(f"  Platform: {platform.system()}")
    print(f"  Python:   {sys.version.split()[0]}")
    print(f"  Target:   {tool_name}")
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

    # 4. Print MCP config for target tool
    print(f"[4/4] MCP config for {tool_name}:")
    print()
    print_config(get_python(), str(script_dir / "mcp_server.py"), project_root)


if __name__ == "__main__":
    main()
