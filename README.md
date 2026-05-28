# code-diagram-mcp

Tree-sitter AST code indexer → MCP server → query call graphs inside Hermes.

## Quick Start

```bash
git clone https://github.com/Brody888/code-diagram.git
cd code-diagram-mcp
python3 setup.py /path/to/your-codebase
```

One command. Works on macOS, Linux, and Windows.

`setup.py` handles everything:

1. Installs dependencies (`tree-sitter` + C/Python grammars)
2. Auto-detects language, framework, build system
3. Builds AST index (functions, call graph, types)
4. Prints the MCP config snippet → paste into `~/.hermes/config.yaml`

Then `/reload-mcp` in Hermes.

For all language grammars: `python3 setup.py /path --all-languages`

Re-index after code changes: `python3 scripts/build-index-ts.py --project /path`

## Hermes Tools

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
