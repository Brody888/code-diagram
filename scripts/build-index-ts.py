#!/usr/bin/env python3
"""
Tree-sitter based code indexer — replaces regex with AST parsing.
Builds: function list, call graph, type graph, module stats.

Usage: python3 build-index-ts.py [--project /path] [--languages c,python]

Fallback: if tree-sitter grammar for a language isn't available,
falls back to regex-based parsing (original build-index.py logic).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import tree_sitter
    from tree_sitter import Language, Parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False

# ── Language config ──────────────────────────────────────────────────

# Map file extensions to tree-sitter language name
EXT_TO_LANG = {
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".py": "python", ".pyi": "python",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
}

# Tree-sitter query patterns per language
QUERIES = {
    "c": {
        "functions": """
            (function_definition
                type: (_) @return_type
                declarator: (function_declarator
                    declarator: (identifier) @name
                    parameters: (parameter_list) @params
                )
                body: (_) @body
            )
            (declaration
                type: (_) @return_type
                declarator: (function_declarator
                    declarator: (identifier) @name
                    parameters: (parameter_list) @params
                )
            )
        """,
        "calls": """
            (call_expression
                function: (identifier) @callee
            )
        """,
        "structs": """
            (struct_specifier
                name: (type_identifier) @name
                body: (field_declaration_list) @body
            )
        """,
    },
    "python": {
        "functions": """
            (function_definition
                name: (identifier) @name
                parameters: (parameters) @params
                body: (block) @body
            )
            (class_definition
                name: (identifier) @name
                body: (block) @body
            )
        """,
        "calls": """
            (call
                function: (identifier) @callee
            )
            (call
                function: (attribute
                    attribute: (identifier) @callee
                )
            )
        """,
        "classes": """
            (class_definition
                name: (identifier) @name
                body: (block) @body
            )
        """,
    },
}

# ── Regex fallback patterns ──────────────────────────────────────────

C_KW = {'if','while','for','switch','return','sizeof','goto','case','default',
        'break','continue','NULL','main','Copyright','INFO','ERR','WARN','DEBUG',
        'VERBOSE','assert','printf','fprintf'}

EXCLUDE_DIR = re.compile(r'(lib/gcc/|include/c\+\+/|plugin/include/|mcu/.*/(?:lib|include)/|'
                         r'node_modules/|\.git/|__pycache__/|\.venv/|venv/)')


def infer_language(filepath: str) -> str | None:
    """Map file extension to tree-sitter language."""
    ext = Path(filepath).suffix.lower()
    # Check multi-extension first
    if filepath.endswith(('.test.js', '.test.ts', '.spec.js', '.spec.ts')):
        return None  # skip test files for indexing
    return EXT_TO_LANG.get(ext)


def fallback_index_c(content: str, filepath: str) -> list[dict]:
    """Regex-based C function discovery (fallback)."""
    functions = []
    for m in re.finditer(
        r'^\s*(static\s+)?(inline\s+)?(const\s+)?(volatile\s+)?'
        r'([\w]+(?:\s*\*)?)\s+(\w+)\s*\([^)]*\)\s*(\{?)',
        content, re.MULTILINE
    ):
        name = m.group(6)
        if name in C_KW or len(name) <= 2:
            continue
        functions.append({"name": name, "file": filepath})
    return functions


def fallback_index_python(content: str, filepath: str) -> list[dict]:
    """Regex-based Python function discovery (fallback)."""
    functions = []
    for m in re.finditer(r'^\s*def\s+(\w+)\s*\(([^)]*)\)', content, re.MULTILINE):
        name = m.group(1)
        params = m.group(2).strip()
        functions.append({"name": name, "file": filepath})
    return functions


FALLBACK_INDEXERS = {
    "c": fallback_index_c,
    "python": fallback_index_python,
}


# ── Tree-sitter indexer ──────────────────────────────────────────────

class TreeSitterIndexer:
    """Build call graph + type graph using tree-sitter AST parsing."""

    def __init__(self):
        self.parser = Parser()
        self.languages = {}
        self._load_languages()

    def _load_languages(self):
        """Try to load tree-sitter grammars for supported languages."""
        # tree-sitter 0.23+ uses Language(ptr, name) constructor
        # We'll try to import built-in languages
        try:
            import tree_sitter_c
            self.languages["c"] = Language(tree_sitter_c.language())
        except ImportError:
            pass

        try:
            import tree_sitter_python
            self.languages["python"] = Language(tree_sitter_python.language())
        except ImportError:
            pass

    def has_language(self, lang: str) -> bool:
        return lang in self.languages

    def parse_file(self, filepath: str, lang: str) -> dict | None:
        """Parse a single file and extract symbols."""
        language = self.languages.get(lang)
        if not language:
            return None

        self.parser.language = language

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return None

        tree = self.parser.parse(bytes(content, "utf-8"))
        root = tree.root_node

        result = {
            "file": filepath,
            "functions": [],
            "calls": [],
            "types": [],
            "classes": [],
        }

        queries = QUERIES.get(lang, {})
        query_lang = language

        # Extract functions with their bodies (for scoped call analysis)
        if "functions" in queries:
            q = query_lang.query(queries["functions"])
            captures = q.captures(root)

            if isinstance(captures, dict):
                func_names_set = set()
                # Collect function names and their body nodes
                name_nodes = captures.get("name", [])
                body_nodes = captures.get("body", [])
                # Build a map: body_node -> function name
                # In tree-sitter queries, captures from the same match share index
                # But since we have dict format, we pair by matching names to the
                # nearest enclosing body
                for name_node in name_nodes:
                    name = name_node.text.decode("utf-8")
                    if name.startswith("_") and len(name) <= 3:
                        continue
                    if name in func_names_set:
                        continue
                    func_names_set.add(name)
                    # Walk up to find the function_definition node
                    body = None
                    # Use the name's parent function_definition node to find body
                    parent = name_node.parent
                    while parent and parent.type != "function_definition":
                        parent = parent.parent
                    if parent:
                        # Search for block/body in children
                        for child in parent.named_children:
                            if child.type in ("block", "body"):
                                body = child
                                break
                    result["functions"].append({"name": name, "file": filepath, "body": body})

        # Extract calls — scope to function bodies
        if "calls" in queries:
            q = query_lang.query(queries["calls"])
            all_calls = q.captures(root)
            call_names = []
            if isinstance(all_calls, dict):
                call_names = [n.text.decode("utf-8") for n in all_calls.get("callee", [])]
            else:
                call_names = [n.text.decode("utf-8") for n, tag in all_calls if tag == "callee"]

            # Assign calls to functions by checking which function body contains each call node
            call_nodes = []
            if isinstance(all_calls, dict):
                call_nodes = all_calls.get("callee", [])
            else:
                call_nodes = [n for n, tag in all_calls if tag == "callee"]

            # Build function body ranges for quick containment check
            func_body_ranges = {}
            for func in result["functions"]:
                body = func.get("body")
                if body:
                    func_body_ranges[func["name"]] = (
                        body.start_point[0], body.end_point[0],
                        body.start_byte, body.end_byte
                    )

            # Assign each call to the functions whose body contains it
            for call_node in call_nodes:
                callee = call_node.text.decode("utf-8")
                cb = call_node.start_byte
                for fname, (sl, el, sb, eb) in func_body_ranges.items():
                    if sb <= cb <= eb:
                        result["calls"].append({"caller": fname, "callee": callee})
                        break
                # If no function body contains it (top-level call), skip

        # Extract types/structs
        for type_key in ["structs", "classes"]:
            if type_key in queries:
                q = query_lang.query(queries[type_key])
                captures = q.captures(root)
                if isinstance(captures, dict):
                    for node in captures.get("name", []):
                        result["types"].append({
                            "name": node.text.decode("utf-8"),
                            "kind": type_key.rstrip("s"),
                            "file": filepath
                        })
                else:
                    for node, tag in captures:
                        if tag == "name":
                            result["types"].append({
                                "name": node.text.decode("utf-8"),
                                "kind": type_key.rstrip("s"),
                                "file": filepath
                            })

        return result


# ── Build index ──────────────────────────────────────────────────────

def build_index(root: str, languages: list[str] | None = None) -> dict:
    """Build full project index using tree-sitter (with regex fallback)."""
    root = os.path.abspath(root)

    # Load project config
    cfg_path = os.path.join(root, ".code-diagram.json")
    cfg = {}
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)

    # Determine which languages to index
    if languages is None:
        languages = list(EXT_TO_LANG.values())
    languages = list(set(languages))

    indexer = TreeSitterIndexer() if HAS_TREE_SITTER else None

    all_functions = {}   # name -> {file, line}
    all_types = {}       # name -> {kind, file}
    call_graph = {}      # func_name -> {callers: [...], callees: [...]}
    modules = {}         # module_name -> {functions, ...}

    # Walk project files
    source_exts = set()
    for ext, lang in EXT_TO_LANG.items():
        if lang in languages:
            source_exts.add(ext)

    files_scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if EXCLUDE_DIR.search(rel_dir):
            continue

        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            ext = Path(fn).suffix.lower()
            if ext not in source_exts:
                continue

            lang = EXT_TO_LANG.get(ext)
            if not lang:
                continue

            rel = os.path.relpath(fp, root)
            module = rel.split("/")[0]

            # Try tree-sitter
            parsed = None
            if indexer and indexer.has_language(lang):
                parsed = indexer.parse_file(fp, lang)

            # Fallback to regex
            if parsed is None and lang in FALLBACK_INDEXERS:
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    functions = FALLBACK_INDEXERS[lang](content, rel)
                    parsed = {"file": rel, "functions": functions, "calls": [], "types": []}
                except Exception:
                    continue

            if parsed is None:
                continue

            files_scanned += 1

            # Index functions
            for func in parsed.get("functions", []):
                name = func["name"]
                if name not in all_functions:
                    all_functions[name] = {"file": rel, "module": module}
                if module not in modules:
                    modules[module] = {"functions": 0}
                modules[module]["functions"] += 1

            # Build call graph — use scoped caller→callee edges from AST
            for call in parsed.get("calls", []):
                if isinstance(call, dict):
                    caller = call["caller"]
                    callee = call["callee"]
                    if callee not in all_functions:
                        continue
                    if caller not in call_graph:
                        call_graph[caller] = {"callers": [], "callees": []}
                    if callee not in call_graph[caller]["callees"]:
                        call_graph[caller]["callees"].append(callee)
                    if callee not in call_graph:
                        call_graph[callee] = {"callers": [], "callees": []}
                    if caller not in call_graph[callee]["callers"]:
                        call_graph[callee]["callers"].append(caller)
                else:
                    # Legacy flat list — assign to all functions in file
                    callee = call
                    if callee not in all_functions:
                        continue
                    for caller_name in func_names_in_file:
                        if caller_name not in call_graph:
                            call_graph[caller_name] = {"callers": [], "callees": []}
                        if callee not in call_graph[caller_name]["callees"]:
                            call_graph[caller_name]["callees"].append(callee)
                        if callee not in call_graph:
                            call_graph[callee] = {"callers": [], "callees": []}
                        if caller_name not in call_graph[callee]["callers"]:
                            call_graph[callee]["callers"].append(caller_name)

            # Index types
            for t in parsed.get("types", []):
                all_types[t["name"]] = {"kind": t["kind"], "file": rel, "module": module}

    # ── Write index ──
    prj_name = cfg.get("project", os.path.basename(root))
    out_dir = os.path.join(root, "code-diagram")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{prj_name}.json")

    index = {
        "project": prj_name,
        "built_at": datetime.now().isoformat(),
        "method": "tree-sitter" if (indexer and any(indexer.has_language(l) for l in languages)) else "regex",
        "source_root": root,
        "language": cfg.get("language", "?"),
        "framework": cfg.get("framework", "?"),
        "preset": cfg.get("preset", "general"),
        "modules": modules,
        "public_apis": [
            {"name": name, "file": info["file"], "module": info["module"]}
            for name, info in all_functions.items()
        ],
        "call_graph": call_graph,
        "types": all_types,
        "stats": {
            "functions": len(all_functions),
            "types": len(all_types),
            "call_edges": sum(len(v["callees"]) for v in call_graph.values()),
            "modules": len(modules),
            "files_scanned": files_scanned,
        },
    }

    with open(out_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"✓ {out_path}")
    for k, v in index["stats"].items():
        print(f"  {k}: {v}")
    if call_graph:
        print(f"  call_graph coverage: {len(call_graph)}/{len(all_functions)} functions ({100*len(call_graph)//max(len(all_functions),1)}%)")

    return index


if __name__ == "__main__":
    root = "."
    languages = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--project" and i + 1 < len(args):
            root = args[i + 1]
        elif a == "--languages" and i + 1 < len(args):
            languages = args[i + 1].split(",")
    build_index(root, languages)
