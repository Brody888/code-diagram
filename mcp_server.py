#!/usr/bin/env python3
"""MCP server for code-diagram — query code indexes via Hermes Agent tools.

Usage:
  python3 mcp_server.py --project /path/to/project

Connect from Hermes:
  hermes mcp add code-diagram --command python3 --args /path/to/mcp_server.py --args --project --args /path/to/project

Protocol: MCP JSON-RPC 2.0 over stdin/stdout, zero external dependencies.
"""

from __future__ import annotations

import json
import os
import sys

# ── Protocol constants ──────────────────────────────────────────────
JSONRPC = "2.0"
SERVER_NAME = "code-diagram"
SERVER_VERSION = "1.0.0"


def log(msg: str) -> None:
    """Log to stderr so it doesn't interfere with stdout JSON-RPC."""
    print(f"[code-diagram-mcp] {msg}", file=sys.stderr, flush=True)


def send_response(request_id, result):
    """Send a JSON-RPC success response."""
    msg = json.dumps({"jsonrpc": JSONRPC, "id": request_id, "result": result})
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def send_error(request_id, code: int, message: str):
    """Send a JSON-RPC error response."""
    msg = json.dumps({"jsonrpc": JSONRPC, "id": request_id, "error": {"code": code, "message": message}})
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def load_index(project_root: str) -> dict | None:
    """Load the code-diagram index JSON, or return None if not found."""
    cfg_path = os.path.join(project_root, ".code-diagram.json")
    if not os.path.exists(cfg_path):
        return None

    with open(cfg_path) as f:
        cfg = json.load(f)

    prj_name = cfg.get("project", os.path.basename(project_root))
    index_path = os.path.join(project_root, "code-diagram", f"{prj_name}.json")
    if not os.path.exists(index_path):
        return None

    with open(index_path) as f:
        return json.load(f)


def format_symbol(info: dict) -> str:
    """Format a function/symbol entry for display."""
    return f"{info['name']} ({info.get('module','?')}/{info['file']}:{info['line']})"


# ── Tool implementations ────────────────────────────────────────────


def tool_get_stats(project_root: str) -> str:
    idx = load_index(project_root)
    if not idx:
        return "No index found. Run `code-diagram --init && code-diagram --index` first."

    stats = idx.get("stats", {})
    lines = [
        f"Project: {idx['project']}  |  Language: {idx.get('language','?')}  |  Framework: {idx.get('framework','?')}",
        f"Preset: {idx.get('preset','general')}",
        f"---",
    ]
    for k, v in stats.items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def tool_list_functions(project_root: str, module: str = "", query: str = "", limit: int = 50) -> str:
    idx = load_index(project_root)
    if not idx:
        return "No index found."

    funcs = idx.get("public_apis", [])
    if module:
        funcs = [f for f in funcs if f.get("module", "") == module]
    if query:
        q = query.lower()
        funcs = [f for f in funcs if q in f["name"].lower() or q in f.get("module", "").lower()]

    if not funcs:
        return f"No functions found{' in module ' + module if module else ''}{' matching ' + query if query else ''}."

    lines = [f"Functions ({len(funcs)} total, showing {min(len(funcs), limit)}):"]
    for f in funcs[:limit]:
        lines.append(f"  {f['name']:40s}  module={f.get('module','?'):20s}  {f.get('file','?')}:{f.get('line','?')}")
    return "\n".join(lines)


def tool_list_modules(project_root: str) -> str:
    idx = load_index(project_root)
    if not idx:
        return "No index found."

    modules = idx.get("modules", {})
    if not modules:
        return "No modules found."

    lines = ["Modules:"]
    for name, info in sorted(modules.items()):
        lines.append(f"  {name:25s}  functions={info.get('functions',0):4d}  public={info.get('public',0):4d}  static={info.get('static',0):4d}  apis={info.get('apis',0):4d}")
    return "\n".join(lines)


def tool_list_cli_commands(project_root: str) -> str:
    idx = load_index(project_root)
    if not idx:
        return "No index found."

    cmds = idx.get("cli_commands", [])
    if not cmds:
        return "No CLI commands found."

    lines = ["CLI Commands:"]
    for c in cmds:
        lines.append(f"  {c['name']:20s}  → {c['handler']:25s}  {c.get('desc','')}")
    return "\n".join(lines)


def tool_list_switches(project_root: str) -> str:
    idx = load_index(project_root)
    if not idx:
        return "No index found."

    switches = idx.get("feature_switches", {})
    if not switches:
        return "No feature switches found."

    lines = [f"Feature Switches ({len(switches)} total):"]
    for k, v in switches.items():
        lines.append(f"  {k:40s} = {v}")
    return "\n".join(lines)


def tool_list_products(project_root: str) -> str:
    idx = load_index(project_root)
    if not idx:
        return "No index found."

    products = idx.get("products", [])
    if not products:
        return "No products/variants found."

    lines = ["Products:"]
    for p in products:
        lines.append(f"  {p['name']:20s}  ({p['dir']})")
    return "\n".join(lines)


def tool_get_callers(project_root: str, function: str) -> str:
    idx = load_index(project_root)
    if not idx:
        return "No index found."

    # Search public_apis first
    apis = {a["name"]: a for a in idx.get("public_apis", [])}
    cg = idx.get("call_graph", {})

    if function not in apis and function not in cg:
        return f"Symbol '{function}' not found in index."

    entry = cg.get(function, {})
    callers = entry.get("callers", [])

    if not callers:
        return f"No callers found for '{function}'."

    lines = [f"Callers of '{function}':"]
    for c in callers:
        info = apis.get(c)
        if info:
            lines.append(f"  {c:30s}  {info.get('file','?')}:{info.get('line','?')}")
        else:
            lines.append(f"  {c}")
    return "\n".join(lines)


def tool_get_callees(project_root: str, function: str) -> str:
    idx = load_index(project_root)
    if not idx:
        return "No index found."

    apis = {a["name"]: a for a in idx.get("public_apis", [])}
    cg = idx.get("call_graph", {})

    if function not in apis and function not in cg:
        return f"Symbol '{function}' not found in index."

    entry = cg.get(function, {})
    callees = entry.get("callees", [])

    if not callees:
        return f"No callees found for '{function}'."

    lines = [f"Callees of '{function}':"]
    for c in callees:
        info = apis.get(c)
        if info:
            lines.append(f"  {c:30s}  {info.get('file','?')}:{info.get('line','?')}")
        else:
            lines.append(f"  {c}")
    return "\n".join(lines)


# ── Tool registry ───────────────────────────────────────────────────

TOOLS = [
    {
        "name": "cd_stats",
        "description": "Get project overview: language, framework, function count, module count, CLI commands, API count, switches. Uses the project set at server start, or specify 'project' to query a different indexed project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Optional: path to project root with a built code-diagram index"},
            },
            "required": [],
        },
    },
    {
        "name": "cd_functions",
        "description": "List public functions/APIs. Filter by module name or search by function name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "module": {"type": "string", "description": "Filter by module name (directory)"},
                "query": {"type": "string", "description": "Search by function name (case-insensitive substring)"},
                "limit": {"type": "integer", "description": "Max results (default 50)", "default": 50},
                "project": {"type": "string", "description": "Optional: project root path"},
            },
            "required": [],
        },
    },
    {
        "name": "cd_modules",
        "description": "List all modules with function counts (total, public, static, APIs).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Optional: project root path"},
            },
            "required": [],
        },
    },
    {
        "name": "cd_cli",
        "description": "List CLI commands registered in the project with their handlers and descriptions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Optional: project root path"},
            },
            "required": [],
        },
    },
    {
        "name": "cd_switches",
        "description": "List feature flags / #define switches in the project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Optional: project root path"},
            },
            "required": [],
        },
    },
    {
        "name": "cd_products",
        "description": "List product variants / build targets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Optional: project root path"},
            },
            "required": [],
        },
    },
    {
        "name": "cd_callers",
        "description": "Find all functions that call the given function.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "function": {"type": "string", "description": "Function name to find callers of"},
                "project": {"type": "string", "description": "Optional: project root path"},
            },
            "required": ["function"],
        },
    },
    {
        "name": "cd_callees",
        "description": "Find all functions called by the given function.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "function": {"type": "string", "description": "Function name to find callees of"},
                "project": {"type": "string", "description": "Optional: project root path"},
            },
            "required": ["function"],
        },
    },
]

TOOL_HANDLERS = {
    "cd_stats": tool_get_stats,
    "cd_functions": tool_list_functions,
    "cd_modules": tool_list_modules,
    "cd_cli": tool_list_cli_commands,
    "cd_switches": tool_list_switches,
    "cd_products": tool_list_products,
    "cd_callers": tool_get_callers,
    "cd_callees": tool_get_callees,
}


def get_project_root(explicit: str | None = None, cli_default: str | None = None) -> str:
    """Resolve project root: explicit arg > CLI --project > ~/.hermes/code-diagram-project > cwd."""
    if explicit:
        return explicit
    if cli_default and cli_default != os.getcwd():
        return cli_default
    # Check the active-project pointer file
    ptr = os.path.expanduser("~/.hermes/code-diagram-project")
    if os.path.exists(ptr):
        with open(ptr) as f:
            candidate = f.read().strip()
            if os.path.isdir(candidate):
                return candidate
    return cli_default or os.getcwd()

def main():
    args = sys.argv[1:]
    project_root = os.getcwd()

    for i, a in enumerate(args):
        if a == "--project" and i + 1 < len(args):
            project_root = os.path.abspath(args[i + 1])

    log(f"Starting MCP server for project: {project_root}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            log(f"Invalid JSON: {e}")
            continue

        req_id = request.get("id")
        method = request.get("method", "")

        if method == "initialize":
            send_response(req_id, {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "capabilities": {"tools": {}},
            })

        elif method == "notifications/initialized":
            # No response needed for notifications
            pass

        elif method == "tools/list":
            send_response(req_id, {"tools": TOOLS})

        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            # Resolve project: per-call > pointer-file > CLI --project > cwd
            explicit = arguments.pop("project", None)
            call_project = get_project_root(explicit, project_root)

            handler = TOOL_HANDLERS.get(tool_name)
            if not handler:
                send_error(req_id, -32601, f"Unknown tool: {tool_name}")
                continue

            try:
                result = handler(call_project, **arguments)
                send_response(req_id, {
                    "content": [{"type": "text", "text": result}],
                })
            except Exception as e:
                log(f"Tool error [{tool_name}]: {e}")
                send_error(req_id, -32000, str(e))

        else:
            send_error(req_id, -32601, f"Unknown method: {method}")


if __name__ == "__main__":
    main()
