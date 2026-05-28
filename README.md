# code-diagram-mcp

Tree-sitter based code indexer with MCP server for Hermes Agent.
Query function call graphs, module stats, and code structure directly from Hermes.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Brody888/code-diagram.git ~/code-diagram-mcp

# 2. Install tree-sitter + language grammars (Python 3.12+)
pip3 install tree-sitter tree-sitter-c tree-sitter-python

# Optional: other languages
pip3 install tree-sitter-go tree-sitter-rust tree-sitter-java \
            tree-sitter-javascript tree-sitter-typescript

# 3. Init + index your project
python3 scripts/init-project.py /path/to/your-project
python3 scripts/build-index-ts.py --project /path/to/your-project

# 4. Add MCP server to ~/.hermes/config.yaml
#    (under mcp_servers:)
#  code-diagram:
#    command: python3.12
#    args:
#    - /Users/you/code-diagram-mcp/mcp_server.py
#    - --project
#    - /path/to/your-project

# 5. Reload in Hermes
/reload-mcp
```

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

## Requirements

- **Python 3.12+** — tree-sitter 0.24+ needs it
- **tree-sitter** (`pip install tree-sitter`)
- Language grammars as Python packages (e.g. `tree-sitter-c`, `tree-sitter-python`)
- Falls back to regex parsing if tree-sitter grammars are missing

## Supported Languages

| Language     | Package                    | AST parsing |
|-------------|----------------------------|-------------|
| C/C++       | `tree-sitter-c`            | ✅ full     |
| Python      | `tree-sitter-python`       | ✅ full     |
| Go          | `tree-sitter-go`           | ✅ full     |
| Rust        | `tree-sitter-rust`         | ✅ full     |
| Java        | `tree-sitter-java`         | ✅ full     |
| JS/TS       | `tree-sitter-javascript/typescript` | ✅ |
| Other       | (regex fallback)           | ⚠️ basic   |

## Tested On

- **clci-firmware** (C, embedded): 709 functions, 320 structs, 821 call edges, 84% coverage
- **Hermes Agent** (Python): function call graph, module stats
