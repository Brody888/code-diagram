#!/usr/bin/env python3
"""Show annotated project file structure tree. Usage: python3 filetree.py [--project /path]"""
import os, re, sys, json

C_KW = {'if','while','for','switch','return','sizeof','goto','case','default','break','continue',
        'NULL','main','Copyright','INFO','ERR','WARN','DEBUG','VERBOSE','assert','printf','fprintf'}
EXCLUDE = re.compile(r'(?:lib/gcc/|include/c\+\+/|plugin/include/|mcu/.*/(?:lib|include)/|code-diagram/|\.git/)')

def role_of(rel, fn):
    mod = rel.split('/')[0]
    if 'config' in fn.lower() or fn == 'config.h': return '配置/Feature Flags'
    if fn in ('main.c','main.go','app.c'): return '程序入口'
    if 'test' in fn.lower() or 'spec' in fn.lower(): return '测试用例'
    if mod == 'cmd' or 'cmd' in rel.lower(): return 'CLI 命令注册'
    if 'mailbox' in fn.lower(): return '消息通信 ← GOD NODE'
    if 'tiny' in fn.lower(): return '产品/服务分发 (适配层)'
    if 'handler' in fn.lower() or 'api' in rel.lower(): return 'API Handler'
    if mod in ('drv','lib','src','pkg','internal'): return '核心逻辑'
    if mod in ('product','variants'): return '产品/变体适配'
    if mod in ('platform','driver'): return '硬件/平台适配层'
    if mod in ('app','demo'): return '应用/示例入口'
    if mod == 'include' or fn.endswith('.h'): return '公共头文件'
    return '源码'

def filetree(root):
    root = os.path.abspath(root)

    # Load index for API/CLI annotations
    prj = os.path.basename(root)
    idx_path = os.path.join(root, 'code-diagram', f'{prj}.json')
    apis = {}; cli_files = {}; god_nodes = set()
    if os.path.exists(idx_path):
        with open(idx_path) as f: idx = json.load(f)
        for a in idx.get('public_apis', []):
            apis[a['name']] = a['file']
        for c in idx.get('cli_commands', []):
            f = c['file']
            if f not in cli_files: cli_files[f] = []
            cli_files[f].append(c['name'])

    # Count functions per file
    file_info = {}
    for dirpath, _, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if EXCLUDE.search(rel_dir): continue
        for fn in filenames:
            if not fn.endswith(('.c','.h','.py','.go','.rs','.java')): continue
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, root)
            try:
                with open(fp, 'r', encoding='utf-8', errors='replace') as f: content = f.read()
            except: continue
            count = 0; entries = []
            for m in re.finditer(r'^\s*(?:pub\s+)?(?:static\s+)?(?:inline\s+)?[\w\s*]+\s+(\w+)\s*\([^)]*\)\s*\{', content, re.MULTILINE):
                name = m.group(1)
                if name not in C_KW and len(name) > 2:
                    count += 1
                    if name in apis: entries.append(name)
            if count > 0:
                file_info[rel] = {"count": count, "entries": entries, "role": role_of(rel, fn), "fn": fn}

    total_files = len(file_info)
    total_funcs = sum(v['count'] for v in file_info.values())

    # Print tree
    print(f"\n{os.path.basename(root)}/")

    # Get top-level items
    items = sorted(os.listdir(root))
    # Filter: skip hidden, skip excluded, only show dirs with content or files with funcs
    visible = []
    for item in items:
        if item.startswith('.'): continue
        child = os.path.join(root, item)
        rel = os.path.relpath(child, root)
        if os.path.isdir(child):
            if EXCLUDE.search(rel + '/'): continue
            # Check if directory has any files with functions
            has_content = any(f.startswith(rel + '/') for f in file_info)
            if has_content:
                visible.append(item)
        elif os.path.isfile(child):
            if rel in file_info:
                visible.append(item)

    for i, item in enumerate(sorted(visible)):
        child = os.path.join(root, item)
        is_last = (i == len(visible) - 1)
        print_subtree(child, root, is_last, "", file_info, cli_files, EXCLUDE)

def print_subtree(path, base_root, is_last, prefix, file_info, cli_files, EXCLUDE):
    name = os.path.basename(path)
    conn = "└── " if is_last else "├── "

    if os.path.isfile(path):
        rel = os.path.relpath(path, base_root)
        info = file_info.get(rel)
        if not info:
            print(f"{prefix}{conn}{name}")
            return
        count = info['count']; entries = info['entries']
        marker = " ★" if count >= 10 else ""
        role_str = f" — {info['role']}" if info['role'] else ""
        extras = ""
        if entries: extras += f"  ← {', '.join(entries[:3])}"
        cli = cli_files.get(rel, [])
        if cli: extras += f"  📎 {', '.join('/' + c for c in cli[:4])}"
        print(f"{prefix}{conn}{name}  ({count} funcs{marker}){role_str}{extras}")
        return

    print(f"{prefix}{conn}{name}/")

    try: items = sorted(os.listdir(path))
    except: return
    visible = []
    for item in items:
        if item.startswith('.'): continue
        child = os.path.join(path, item)
        rel = os.path.relpath(child, base_root)
        if os.path.isdir(child):
            if EXCLUDE.search(rel + '/'): continue
            has = any(f.startswith(rel + '/') for f in file_info)
            if has: visible.append(item)
        elif os.path.isfile(child):
            if rel in file_info: visible.append(item)

    for i, item in enumerate(visible):
        child = os.path.join(path, item)
        print_subtree(child, base_root, i == len(visible) - 1,
                      prefix + ("    " if is_last else "│   "), file_info, cli_files, EXCLUDE)

if __name__ == '__main__':
    root = '.'
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--project' and i+1 < len(args): root = args[i+1]
    filetree(root)
