#!/usr/bin/env python3
"""Generate feature inventory report from index. Usage: python3 features-report.py [--html] [--project /path]"""
import os, sys, json
from datetime import datetime

def report(root):
    root = os.path.abspath(root)
    prj_name = os.path.basename(root)
    idx_path = os.path.join(root, "code-diagram", f"{prj_name}.json")
    if not os.path.exists(idx_path):
        print(f"Index not found: {idx_path}")
        print("Run: python3 build-index.py --project .")
        sys.exit(1)
    with open(idx_path) as f: idx = json.load(f)

    modules = idx["modules"]; cli = idx["cli_commands"]; apis = idx["public_apis"]
    switches = idx["feature_switches"]; products = idx["products"]; stats = idx["stats"]
    html = '--html' in sys.argv

    if html:
        t1 = ''.join(f'<tr><td><b>{m}</b></td><td>{v["functions"]}</td><td>public:{v["public"]} static:{v["static"]} apis:{v["apis"]}</td></tr>' for m,v in sorted(modules.items()))
        t2 = ''
        for c in cli: t2 += f'<tr><td><span style="background:#E0E7FF;color:#3730A3;font-size:11px;padding:1px 7px;border-radius:6px">CLI</span></td><td><b>/{c["name"]}</b></td><td><code>{c["handler"]}()</code></td><td>{c["desc"][:90]}</td><td><code>{c["file"]}:{c["line"]}</code></td></tr>'
        for a in apis[:50]: t2 += f'<tr><td><span style="background:#E0E7FF;color:#3730A3;font-size:11px;padding:1px 7px;border-radius:6px">{a["module"]}</span></td><td><code>{a["name"]}()</code></td><td>—</td><td>Public API</td><td><code>{a["file"]}:{a["line"]}</code></td></tr>'
        t3 = ''.join(f'<tr><td><code>{k}</code></td><td>{v}</td></tr>' for k,v in sorted(switches.items())[:40])
        t4 = ''.join(f'<tr><td><b>{p["name"]}</b></td><td>{p["dir"]}</td></tr>' for p in products)
        out = os.path.join(root, "code-diagram", "features-report.html")
        with open(out, 'w') as f:
            f.write(f'''<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><title>Features — {prj_name}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#F8F9FA;color:#1A1A2E;line-height:1.6}}.container{{max-width:1200px;margin:0 auto;padding:32px 20px}}
.header{{background:linear-gradient(135deg,#1E293B,#334155);color:white;border-radius:16px;padding:36px 40px;margin-bottom:28px}}.stats{{display:flex;gap:12px;margin-bottom:28px;flex-wrap:wrap}}
.stat{{background:white;border-radius:10px;padding:14px 20px;font-size:13px;color:#4B5563;box-shadow:0 1px 2px rgba(0,0,0,.04)}}.stat strong{{color:#1F2937}}
.section{{background:white;border-radius:12px;margin-bottom:16px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)}}.section h2{{padding:18px 24px;font-size:16px;font-weight:700;background:#FAFBFC;border-bottom:1px solid #F3F4F6}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th{{background:#F9FAFB;text-align:left;padding:10px 16px;font-weight:600;font-size:12px;color:#6B7280;text-transform:uppercase;border-bottom:2px solid #E5E7EB}}td{{padding:10px 16px;border-bottom:1px solid #F3F4F6}}code{{font-size:12px;background:#F3F4F6;padding:1px 5px;border-radius:3px;font-family:monospace}}</style></head><body><div class="container">
<div class="header"><h1>📊 Feature Inventory</h1><div style="color:#94A3B8;font-size:14px;margin-top:6px">{prj_name} — {idx.get("language","?")} | {idx.get("framework","?")}</div></div>
<div class="stats"><div class="stat"><strong>{stats["functions"]}</strong> functions</div><div class="stat"><strong>{stats["cli_commands"]}</strong> CLI</div><div class="stat"><strong>{stats["public_apis"]}</strong> APIs</div><div class="stat"><strong>{stats["modules"]}</strong> modules</div><div class="stat"><strong>{stats["switches"]}</strong> switches</div><div class="stat"><strong>{stats["products"]}</strong> products</div></div>
<div class="section"><h2>表 1 — Module Overview</h2><table><tr><th>Module</th><th>Functions</th><th>Visibility</th></tr>{t1}</table></div>
<div class="section"><h2>表 2 — Feature Detail ({len(cli)} CLI + {len(apis)} APIs)</h2><table><tr><th>Module</th><th>Command/API</th><th>Handler</th><th>Description</th><th>File</th></tr>{t2}</table></div>
<div class="section"><h2>表 3 — Feature Switches</h2><table><tr><th>Switch</th><th>Value</th></tr>{t3}</table></div>
<div class="section"><h2>表 4 — Products</h2><table><tr><th>Product</th><th>Directory</th></tr>{t4}</table></div>
</div></body></html>''')
        print(f"✓ {out}")
    else:
        out = os.path.join(root, "code-diagram", "features-report.md")
        with open(out, 'w') as f:
            f.write(f"# Feature Inventory — {prj_name}\n\n")
            f.write(f"**{stats['functions']}** functions | **{stats['cli_commands']}** CLI | **{stats['public_apis']}** APIs | **{stats['modules']}** modules | **{stats['switches']}** switches | **{stats['products']}** products\n\n")
            f.write(f"## Module Overview\n\n")
            for m, v in sorted(modules.items()):
                f.write(f"- **{m}**: {v['functions']} funcs (public:{v['public']} static:{v['static']} apis:{v['apis']})\n")
            f.write(f"\n## CLI Commands ({len(cli)})\n\n")
            for c in cli:
                f.write(f"- **/{c['name']}** → `{c['handler']}()` — {c['desc'][:80]}\n")
            f.write(f"\n## Public APIs ({len(apis)})\n\n")
            for a in apis[:50]:
                f.write(f"- `{a['name']}()` [{a['file']}:{a['line']}]\n")
            f.write(f"\n## Feature Switches ({len(switches)})\n\n")
            for k, v in sorted(switches.items())[:40]:
                f.write(f"- `{k}` = {v}\n")
        print(f"✓ {out}")

if __name__ == '__main__':
    root = '.'
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--project' and i+1 < len(args): root = args[i+1]
    report(root)
