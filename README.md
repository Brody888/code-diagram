# code-diagram-mcp

Tree-sitter AST code indexer → MCP server → query call graphs inside your AI coding tool.

Works with **Hermes Agent, Claude Code, Codex CLI, OpenClaw** — anything that speaks MCP.

## Quick Start

```bash
git clone https://github.com/Brody888/code-diagram.git
cd code-diagram-mcp

# Hermes Agent (default)
python3 setup.py /path/to/your-codebase

# Claude Code
python3 setup.py /path/to/your-codebase --tool claude

# Codex CLI
python3 setup.py /path/to/your-codebase --tool codex

# OpenClaw
python3 setup.py /path/to/your-codebase --tool openclaw

# TRAE IDE
python3 setup.py /path/to/your-codebase --tool trae
```

One command. Works on macOS, Linux, and Windows.

`setup.py` handles everything:

1. Installs dependencies (`tree-sitter` + C/Python grammars)
2. Auto-detects language, framework, build system
3. Builds AST index (functions, call graph, types)
4. Prints the MCP config — ready to paste

For all language grammars: add `--all-languages`.

Re-index after code changes: `python3 scripts/build-index-ts.py --project /path`

## How Each Tool Configures

| Tool          | Config file                        | Auto?                    |
|---------------|------------------------------------|--------------------------|
| Hermes Agent  | `~/.hermes/config.yaml`            | Paste + `/reload-mcp`    |
| Claude Code   | `.mcp.json` or `~/.claude/mcp.json`| `claude mcp add` if CLI  |
| Codex CLI     | `~/.codex/config.toml`             | Paste + restart          |
| OpenClaw      | `config.yaml`                      | Paste + restart          |
| TRAE IDE      | `.trae/mcp.json`                   | Paste + restart          |

## MCP Tools

| Tool           | Description                              |
|----------------|------------------------------------------|
| `cd_stats`     | Project overview: functions, types, edges|
| `cd_functions` | List/search functions by module or name  |
| `cd_modules`   | Module list with function counts         |
| `cd_callers`   | Who calls a given function               |
| `cd_callees`   | What a given function calls              |
| `cd_cli`       | CLI commands (Go/Cobra, Python/Click)    |
| `cd_switches`  | Feature flags / #define switches         |
| `cd_products`  | Product variants / build targets         |

## Supported Languages

C (full AST), Python (full AST), plus Go, Rust, Java, JS/TS with optional grammars.
Falls back to regex parsing for anything without a tree-sitter grammar installed.

## Tested On

| Project            | Language | Functions | Call Edges | Coverage |
|--------------------|----------|-----------|------------|----------|
| clci-firmware v1.6 | C        | 709       | 821        | 84%      |
