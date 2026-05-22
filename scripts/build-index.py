#!/usr/bin/env python3
"""Build project call graph index. Usage: python3 build-index.py [--project /path]"""
import os, re, json, sys
from datetime import datetime

EXCLUDE = re.compile(r'(?:lib/gcc/|include/c\+\+/|plugin/include/|mcu/.*/(?:lib|include)/)')
C_KW = {'if','while','for','switch','return','sizeof','goto','case','default','break','continue',
        'NULL','main','Copyright','INFO','ERR','WARN','DEBUG','VERBOSE','assert','printf','fprintf'}

def build(root):
    root = os.path.abspath(root)
    cfg_path = os.path.join(root, ".code-diagram.json")
    cfg = {}
    if os.path.exists(cfg_path):
        with open(cfg_path) as f: cfg = json.load(f)

    # ── Type discovery ──
    sig_types = set()
    for dirpath, _, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if EXCLUDE.search(rel_dir): continue
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as f: content = f.read()
            except: continue
            if fn.endswith('.h'):
                for m in re.finditer(r'typedef\s+.*\s+(\w+)\s*;', content): sig_types.add(m.group(1))
                for m in re.finditer(r'^\s*(?:extern\s+)?(\w[\w\s*]+?)\s+(\w+)\s*\([^)]*\)\s*;', content, re.MULTILINE):
                    ret = m.group(1).strip().replace('extern ','').split()[-1].replace('*','')
                    if m.group(2) not in C_KW and len(m.group(2)) > 2: sig_types.add(ret)
            if fn.endswith('.c'):
                for m in re.finditer(r'^\s*(?:static\s+)?(?:inline\s+)?(\w[\w\s*]+?)\s+(\w+)\s*\([^)]*\)\s*(\{?)', content, re.MULTILINE):
                    ret = m.group(1).strip().replace('static ','').replace('inline ','').split()[-1].replace('*','')
                    if m.group(2) not in C_KW and len(m.group(2)) > 2: sig_types.add(ret)

    BASE = {'void','int','char','float','double','bool','size_t','unsigned','long','short',
            'int32_t','uint32_t','int8_t','uint8_t','int16_t','uint16_t','int64_t','uint64_t'}
    VALID = BASE | sig_types

    # ── Function discovery ──
    func_files = {}
    for dirpath, _, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if EXCLUDE.search(rel_dir): continue
        for fn in filenames:
            if not fn.endswith(('.c','.h')): continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root)
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as f: lines = f.readlines()
            except: continue
            for i, line in enumerate(lines):
                m = re.match(r'^\s*(static\s+)?(inline\s+)?(const\s+)?(volatile\s+)?'
                             r'(struct\s+\w+\s*\*?\s*)?(enum\s+\w+\s*)?'
                             r'([\w]+(?:\s*\*)?)\s+(\w+)\s*\([^)]*\)\s*(\{?)', line)
                if not m: continue
                ret = m.group(7).replace('*','').strip()
                name = m.group(8)
                if name in C_KW or len(name) <= 2: continue
                if ret not in VALID: continue
                is_static = bool(m.group(1))
                mod = rel.split('/')[0]
                key = (name, fn.endswith('.c'))
                if name in func_files and func_files[name]["is_c"] and fn.endswith('.h'): continue
                func_files[name] = {"file":rel,"line":i+1,"module":mod,"static":is_static,"is_c":fn.endswith('.c')}

    # ── CLI commands ──
    CLI_PATS = [r'add_command\("(\w+)",\s*(\w+)', r'REGISTER_CMD\("(\w+)",\s*(\w+)',
                r'CLI_COMMAND\("(\w+)",\s*(\w+)', r'\.AddCommand\("(\w+)",\s*(\w+)']
    cli = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(('.c','.h','.py')): continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                    for i, line in enumerate(f, 1):
                        for pat in CLI_PATS:
                            for m in re.finditer(pat, line):
                                desc = ""; dm = re.search(r'"([^"]*)"', line[m.end():])
                                if dm: desc = dm.group(1)[:80]
                                cli.append({"name":m.group(1),"handler":m.group(2),"desc":desc,"file":os.path.relpath(fp,root),"line":i})
            except: pass

    # ── Public APIs ──
    CORE = {'drv','lib','src','pkg','api','core','app'}
    apis = []
    for name, info in func_files.items():
        if info["static"]: continue
        mod = info["module"]
        score = 0
        if mod in CORE: score += 2
        if mod not in {'test','tests','demo','example','examples','out','build','doc','include'}: score += 1
        if score >= 2: apis.append({"name":name,"file":info["file"],"line":info["line"],"module":mod})

    # ── Switches ──
    switches = {}
    switch_kw = re.compile(r'SUPPORT|ENABLE|DISABLE|MODE|CONFIG|VERSION|USE_|WITH_|HAS_|FEATURE', re.I)
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(('.h','.c')): continue
            fp = os.path.join(dirpath, fn)
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                    for m in re.finditer(r'#define\s+(\w+)\s+(\S+)', f.read()):
                        k, v = m.group(1), m.group(2)
                        if switch_kw.search(k): switches[k] = v[:60]
            except: pass

    # ── Products ──
    products = []
    for sub in ['product','variants','flavors','targets']:
        pd = os.path.join(root, sub)
        if not os.path.isdir(pd): continue
        for d in sorted(os.listdir(pd)):
            dp = os.path.join(pd, d)
            if os.path.isdir(dp):
                name = d
                for cf in ['config.h','config.mk']:
                    cp = os.path.join(dp, cf)
                    if os.path.exists(cp):
                        with open(cp, errors='replace') as f:
                            m = re.search(r'(?:PRODUCT_)?NAME\s+"?(\w+)"?', f.read())
                            if m: name = m.group(1)
                        break
                products.append({"dir":d,"name":name})
        if products: break

    # ── Modules ──
    modules = {}
    for name, info in func_files.items():
        mod = info["module"]
        if mod not in modules: modules[mod] = {"functions":0,"static":0,"public":0,"apis":0}
        modules[mod]["functions"] += 1
        if info["static"]: modules[mod]["static"] += 1
        else: modules[mod]["public"] += 1
    for a in apis: modules[a["module"]]["apis"] += 1

    # ── Write ──
    prj_name = cfg.get("project", os.path.basename(root))
    out_dir = os.path.join(root, "code-diagram")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{prj_name}.json")
    index = {
        "project":prj_name,"built_at":datetime.now().isoformat(),
        "source_root":root,"language":cfg.get("language","?"),"framework":cfg.get("framework","?"),
        "preset":cfg.get("preset","general"),
        "modules":modules,"cli_commands":cli,"public_apis":apis,
        "call_graph":{},"feature_switches":switches,"products":products,
        "stats":{"functions":len(func_files),"cli_commands":len(cli),"public_apis":len(apis),
                 "switches":len(switches),"products":len(products),"modules":len(modules)}
    }
    with open(out, 'w') as f: json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"✓ {out}")
    for k,v in index["stats"].items(): print(f"  {k}: {v}")

if __name__ == '__main__':
    root = '.'
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--project' and i+1 < len(args): root = args[i+1]
    build(root)
