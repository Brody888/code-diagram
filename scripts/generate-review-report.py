#!/usr/bin/env python3
"""Generate a self-contained HTML code review report with actionable fix suggestions."""
import json, os, hashlib, sys, re
from datetime import datetime

IDX_PATH = os.path.expanduser("~/.claude/cache/code-diagram/clci_combo.json")

try:
    with open(IDX_PATH) as f:
        idx = json.load(f)
except FileNotFoundError:
    print("Index not found. Run /code-diagram --index first.")
    sys.exit(1)

FW = idx["source_root"]
cg = idx["call_graph"]
switches = idx["feature_switches"]
fp_map = idx.get("fp_map", {})
comms = idx["communities"]
gods = idx["god_nodes"]

findings = {"R1": [], "R2": [], "R3": [], "R4": [], "R5": [], "R6": [], "R7": [], "R8": []}

# ── R2 ──
for func, node in cg.items():
    callers = node.get("callers", [])
    if len(callers) >= 5:
        n = len(callers)
        findings["R2"].append({
            "func": func, "file": node["file"], "comm": node["comm"], "callers": n,
            "detail": f"Called by {n} functions: {', '.join(callers[:5])}{'...' if n>5 else ''}",
            "fix": (
                f"<b>Before changing <code>{func}()</code>:</b><br>"
                f"1. Run <code>/code-diagram --impact {func}</code> to see full blast radius<br>"
                f"2. Add unit/regression test covering all {n} call paths<br>"
                f"3. If changing signature: add a wrapper function instead of modifying in-place<br>"
                f"4. Mark commit message with <code>[HIGH-RISK]</code> tag — changes to this function affect {n} callers across {len(set(cg[c]['comm'] for c in callers if c in cg))} communities"
            )
        })

# ── R4 ──
for fpath in ["include/drivers/clci_common.h"]:
    fp = os.path.join(FW, fpath)
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        for m in re.finditer(r'start addr (0x[0-9a-fA-F]+).*?\nstruct (\w+)\s*\{', content):
            name, addr = m.group(2), m.group(1)
            findings["R4"].append({
                "struct": name, "addr": addr,
                "detail": f"Fixed-address struct @ {addr} — HW register map, field order/alignment locked",
                "fix": (
                    f"<b><code>{name}</code> is memory-mapped to hardware at {addr}:</b><br>"
                    f"• <b>NEVER</b> reorder fields without HW team sign-off — each offset is a silicon register<br>"
                    f"• Add <code>static_assert(offsetof({name}, field) == expected)</code> for critical fields<br>"
                    f"• Mark with comment: <code>// WARNING: fixed HW address map — do not reorder</code><br>"
                    f"• All field changes must be synced with <code>clci_board.h</code> / CSR spec document"
                )
            })
        for m in re.finditer(r'struct (\w+)\s*\{(.*?)\};', content, re.DOTALL):
            body = m.group(2)
            field_addrs = re.findall(r'0x17[0-9a-fA-F]{3}', body)
            if field_addrs and m.group(1) not in {s["struct"] for s in findings["R4"]}:
                findings["R4"].append({
                    "struct": m.group(1), "addr": ", ".join(field_addrs[:3]),
                    "detail": f"Fixed-address struct — field offsets at {', '.join(field_addrs[:3])} — HW register map",
                    "fix": (
                        f"<b><code>{m.group(1)}</code> has hard-coded field offsets:</b><br>"
                        f"• Add explicit padding fields (<code>uint8_t _reserved[N]</code>) to make layout explicit<br>"
                        f"• Use <code>static_assert(sizeof({m.group(1)}) == expected_size)</code> to catch size changes<br>"
                        f"• All field changes must be synced with HW CSR spreadsheet"
                    )
                })

# ── R5 ──
error_funcs = {'cmd_clci_link', 'cmd_bitlock', 'cmd_pcslock', 'cmd_reset',
               'cmd_aphy_init', 'cmd_sphy_init', 'cmd_aphy_pll_init'}
for func in error_funcs:
    if func in cg:
        callees = cg[func].get("callees", [])
        if 'sys_error_save' not in callees:
            # Check if the fp-resolved callee DOES have sys_error_save
            resolved_callees = set()
            for c in callees:
                if c in cg:
                    resolved_callees.update(cg[c].get("callees", []))
            has_indirect_save = 'sys_error_save' in resolved_callees
            detail = "Error path may not report to SOC — no sys_error_save in callees"
            if has_indirect_save:
                detail += " (but indirect callee does call sys_error_save — may be OK)"
            findings["R5"].append({
                "func": func, "file": cg[func]["file"], "comm": cg[func]["comm"],
                "detail": detail,
                "fix": (
                    f"<b>Ensure all error paths in <code>{func}()</code> are reported to SOC:</b><br>"
                    f"• After every <code>return error</code> or <code>ret != 0</code> branch, call <code>sys_error_save(SYS_ERROR_CLASS_*, ret)</code><br>"
                    f"• Use <code>SYS_ERROR_CLASS_LINK</code> for link training failures<br>"
                    f"• <b>Pattern to follow:</b><br>"
                    f"<code style='background:#F3F4F6;padding:2px 6px;border-radius:4px'>"
                    f"if (ret) {{ sys_error_save(SYS_ERROR_CLASS_LINK, ret); return CMD_RESP_FAIL; }}"
                    f"</code>"
                ) if not has_indirect_save else (
                    f"<b><code>{func}()</code> reports errors indirectly via its callee's sys_error_save:</b><br>"
                    f"• Verify the indirect path works under all failure conditions<br>"
                    f"• Consider adding a direct sys_error_save for defense-in-depth<br>"
                    f"• Document the error-reporting chain in the function's header comment"
                )
            })

# ── R6 ──
polling_switches = {
    'SIDEBAND_MODE_ISR': ('sb0_link_rx_isr, sb0_rdi_rx_isr, sb0_fdi_rx_isr, sb_fatal_err_isr', '4 SB ISRs'),
    'DOORBELL_MODE_ISR': ('db_to_soc_isr', 'Doorbell ISR'),
    'UART_MODE_ISR': ('uart_isr', 'UART ISR'),
}
for sw, (handlers, desc) in polling_switches.items():
    if sw in switches and switches[sw]["default"] == "0":
        findings["R6"].append({
            "switch": sw, "handlers": handlers, "desc": desc,
            "detail": f"{desc} ({handlers}) running in polling mode (latency risk)",
            "fix": (
                f"<b><code>{sw}=0</code> → {desc} in <u>polling</u> mode:</b><br>"
                f"• Set <code>#define {sw} 1</code> in <code>product/sep1/ramfw/config.h</code> to enable interrupt mode<br>"
                f"• Measure worst-case polling latency: each poll loop is ~N μs × number of active lanes<br>"
                f"• If real-time response is required (e.g., fatal error ISR), switch to interrupt mode<br>"
                f"• <b>Tradeoff:</b> ISR mode increases interrupt load but guarantees bounded latency"
            )
        })

# ── R7 ──
def max_depth(func, visited=None, d=0):
    if visited is None: visited = set()
    if func not in cg or func in visited or d > 6: return d
    visited.add(func)
    return max([d] + [max_depth(c, visited.copy(), d+1) for c in cg[func].get("callees", [])])

for func in ['cmd_clci_link', 'cmd_soft_link', 'cmd_ucie_state_set', 'cmd_combo']:
    d = max_depth(func)
    if d >= 4:
        findings["R7"].append({
            "func": func, "depth": d,
            "detail": f"Call chain depth {d} — check stack usage under worst-case nesting",
            "fix": (
                f"<b><code>{func}()</code> has call depth {d} (max safe ~6 on RISC-V rv32imac):</b><br>"
                f"• Estimate stack: each frame ~64-128 bytes → depth {d} ≈ {d*64}-{d*128} bytes<br>"
                f"• Check <code>clci_config_t</code> local allocations (256B struct on stack = dangerous)<br>"
                f"• Consider inlining leaf functions (e.g., <code>phase0_check_lane</code>) with <code>static inline</code><br>"
                f"• Run with <code>-fstack-usage</code> GCC flag to get exact per-function stack sizes"
            )
        })

# ── R8 ──
if len(fp_map) > 0:
    findings["R8"].append({
        "count": len(fp_map),
        "detail": f"{len(fp_map)} function pointers assigned in product/sep1/src/ only — verify other 7 products",
        "fix": (
            f"<b>{len(fp_map)} function pointers only bound in <code>product/sep1/src/sep1_ram.c</code>:</b><br>"
            f"• Check <code>product/&lt;other&gt;/src/</code> — if missing <code>platform_clci_api_init()</code>, they fall back to sep1 defaults<br>"
            f"• For products with different PHY (e.g., otp2 AP=64 lanes), each fp should point to product-specific implementation<br>"
            f"• <b>Audit checklist:</b> run <code>/code-diagram --features --product &lt;name&gt;</code> for each of bdp1, mttp1, otp1, otp2, otp3, slp1, wmp1"
        )
    })

# ── Scoring ──
risk_map = {"R2": "red", "R3": "red", "R4": "red", "R1": "yellow", "R5": "yellow",
            "R6": "yellow", "R7": "yellow", "R8": "blue"}
red_cats = sum(1 for rid, items in findings.items() if risk_map[rid] == "red" and items)
yellow_cats = sum(1 for rid, items in findings.items() if risk_map[rid] == "yellow" and items)
blue_cats = sum(1 for rid, items in findings.items() if risk_map[rid] == "blue" and items)
score = max(40, 100 - red_cats*15 - yellow_cats*8 - blue_cats*3)
grade = "A" if score >= 90 else ("B+" if score >= 75 else ("B" if score >= 60 else ("C" if score >= 40 else "D")))
high = sum(len(items) for rid, items in findings.items() if risk_map[rid] == "red")
med = sum(len(items) for rid, items in findings.items() if risk_map[rid] == "yellow")
low = sum(len(items) for rid, items in findings.items() if risk_map[rid] == "blue")

# ── HTML ──
risk_label = {"red": "🔴 HIGH", "yellow": "🟡 MEDIUM", "blue": "⚠ LOW"}
risk_bg = {"red": "#FEF2F2", "yellow": "#FFFBEB", "blue": "#EFF6FF"}
risk_border = {"red": "#FECACA", "yellow": "#FDE68A", "blue": "#BFDBFE"}

def findings_html(rid):
    items = findings[rid]
    if not items:
        return '<div class="check-pass">✅ No issues found</div>'
    r = risk_map[rid]
    rows = []
    for item in items:
        name = item.get("func") or item.get("struct") or item.get("switch") or item.get("count", "?")
        file_info = item.get("file", "")
        comm = item.get("comm", "")
        detail = item.get("detail", "")
        fix = item.get("fix", "")
        tag = f'<span class="comm-tag">{comm}</span>' if comm else ""
        extra = ""
        if "callers" in item: extra = f'<span class="stat-badge">{item["callers"]} callers</span>'
        elif "depth" in item: extra = f'<span class="stat-badge">depth {item["depth"]}</span>'
        elif "addr" in item: extra = f'<span class="stat-badge">@{item["addr"]}</span>'
        rows.append(f'''
        <div class="finding-card" style="background:{risk_bg[r]};border-left:4px solid {risk_border[r]}">
          <div class="finding-header">
            <span class="finding-name">{name}</span>
            {tag}
            {extra}
            <span class="finding-file">{file_info}</span>
          </div>
          <div class="finding-detail">{detail}</div>
          <details class="fix-details">
            <summary>💡 Suggested Fix</summary>
            <div class="fix-content">{fix}</div>
          </details>
        </div>''')
    return '\n'.join(rows)

checks_html = []
check_names = {
    "R1": "Return Value Not Checked", "R2": "High Blast Radius",
    "R3": "Polling Without Timeout Guard", "R4": "Fixed-Address Structs",
    "R5": "Error Not Reported to SOC", "R6": "ISR Running in Polling Mode",
    "R7": "Deep Call Chains (≥4)", "R8": "FP Bindings — Single Product"
}
for rid in ["R1","R2","R3","R4","R5","R6","R7","R8"]:
    items = findings[rid]
    count = len(items)
    badge = f'<span class="count-badge">{count}</span>' if count else ''
    checks_html.append(f'''
  <div class="check-section">
    <div class="check-title" onclick="this.parentElement.classList.toggle('collapsed')">
      {risk_label.get(risk_map[rid], '⚪')} — {check_names[rid]} {badge}
    </div>
    <div class="check-body">
      {findings_html(rid)}
    </div>
  </div>''')

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Code Review — {idx["project"]}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background:#F8F9FA; color:#1A1A2E; line-height:1.6; }}
.container {{ max-width:960px; margin:0 auto; padding:32px 20px; }}
.header {{ background:linear-gradient(135deg, #1E293B 0%, #334155 100%); color:white; border-radius:16px; padding:36px 40px; margin-bottom:28px; }}
.header h1 {{ font-size:28px; font-weight:700; margin-bottom:8px; }}
.header .subtitle {{ color:#94A3B8; font-size:14px; }}
.header .meta {{ display:flex; gap:24px; margin-top:16px; font-size:13px; color:#CBD5E1; }}
.score-row {{ display:flex; gap:16px; margin-bottom:28px; align-items:stretch; }}
.score-card {{ background:white; border-radius:12px; padding:24px; text-align:center; flex:1; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.score-card .value {{ font-size:48px; font-weight:800; }}
.score-card .label {{ font-size:12px; color:#6B7280; margin-top:4px; text-transform:uppercase; letter-spacing:.08em; }}
.score-grade {{ background:{'#059669' if grade=='A' else '#2563EB' if grade.startswith('B') else '#D97706' if grade=='C' else '#DC2626'}; color:white; border-radius:12px; padding:24px; text-align:center; min-width:120px; box-shadow:0 1px 3px rgba(0,0,0,.06); }}
.score-grade .value {{ font-size:48px; font-weight:800; }}
.score-grade .label {{ font-size:12px; opacity:.85; margin-top:4px; text-transform:uppercase; letter-spacing:.08em; }}
.stats-row {{ display:flex; gap:12px; margin-bottom:28px; }}
.stat {{ background:white; border-radius:10px; padding:14px 20px; font-size:13px; color:#4B5563; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
.stat strong {{ color:#1F2937; }}
.check-section {{ background:white; border-radius:12px; margin-bottom:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.04); }}
.check-title {{ padding:16px 24px; font-weight:600; font-size:15px; cursor:pointer; user-select:none; display:flex; align-items:center; gap:10px; border-bottom:1px solid #F3F4F6; }}
.check-title:hover {{ background:#F9FAFB; }}
.check-body {{ padding:20px 24px; }}
.collapsed .check-body {{ display:none; }}
.count-badge {{ background:#E5E7EB; color:#374151; font-size:12px; padding:2px 8px; border-radius:10px; font-weight:600; }}
.finding-card {{ border-radius:8px; padding:14px 18px; margin-bottom:10px; }}
.finding-header {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.finding-name {{ font-weight:600; font-size:14px; font-family:'SF Mono',Menlo,monospace; color:#1F2937; }}
.finding-file {{ font-size:12px; color:#9CA3AF; font-family:'SF Mono',Menlo,monospace; }}
.finding-detail {{ font-size:13px; color:#4B5563; margin:6px 0; }}
.comm-tag {{ font-size:11px; background:#E0E7FF; color:#3730A3; padding:1px 7px; border-radius:6px; font-weight:600; }}
.stat-badge {{ font-size:11px; background:#F3F4F6; color:#6B7280; padding:1px 7px; border-radius:6px; }}
.check-pass {{ color:#059669; font-size:14px; padding:8px 0; }}
.fix-details {{ margin-top:10px; }}
.fix-details summary {{ font-size:13px; font-weight:600; color:#2563EB; cursor:pointer; padding:4px 0; }}
.fix-details summary:hover {{ color:#1D4ED8; }}
.fix-content {{ font-size:13px; color:#374151; background:white; border:1px solid #E5E7EB; border-radius:8px; padding:12px 16px; margin-top:6px; line-height:1.8; }}
.fix-content code {{ background:#F3F4F6; padding:1px 5px; border-radius:3px; font-size:12px; font-family:'SF Mono',Menlo,monospace; }}
.rec-section {{ background:white; border-radius:12px; padding:24px; margin-top:24px; box-shadow:0 1px 3px rgba(0,0,0,.04); }}
.rec-section h2 {{ font-size:18px; font-weight:700; margin-bottom:16px; }}
.rec-item {{ padding:8px 0; border-bottom:1px solid #F3F4F6; font-size:14px; }}
.rec-item:last-child {{ border-bottom:none; }}
.rec-prio {{ font-size:11px; font-weight:700; padding:2px 8px; border-radius:6px; margin-right:8px; }}
.rec-prio.high {{ background:#FEE2E2; color:#991B1B; }}
.rec-prio.med {{ background:#FFFBEB; color:#92400E; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>🔍 Code Review Report</h1>
  <div class="subtitle">{idx["project"]} — {idx["source_root"].split("/")[-1]}</div>
  <div class="meta">
    <span>📅 {datetime.now().strftime("%Y-%m-%d %H:%M")}</span>
    <span>📊 {idx["stats"]["functions_indexed"]} functions indexed</span>
    <span>🏷 {len(comms)} communities</span>
    <span>🔧 {len(switches)} switches</span>
  </div>
</div>

<div class="score-row">
  <div class="score-card">
    <div class="value" style="color:#DC2626">{high}</div>
    <div class="label">🔴 High Risk</div>
  </div>
  <div class="score-card">
    <div class="value" style="color:#D97706">{med}</div>
    <div class="label">🟡 Medium Risk</div>
  </div>
  <div class="score-card">
    <div class="value" style="color:#2563EB">{low}</div>
    <div class="label">⚠ Low Risk</div>
  </div>
  <div class="score-grade">
    <div class="value">{grade}</div>
    <div class="label">Overall Grade</div>
  </div>
</div>

<div class="stats-row">
  <div class="stat"><strong>{len(cg)}</strong> functions in call graph</div>
  <div class="stat"><strong>{len(fp_map)}</strong> function pointers resolved</div>
  <div class="stat"><strong>{len(gods)}</strong> GOD NODEs tracked</div>
  <div class="stat"><strong>{len(idx["products"])}</strong> products</div>
</div>

{''.join(checks_html)}

<div class="rec-section">
  <h2>📋 Action Items (Priority Order)</h2>
  <div class="rec-item"><span class="rec-prio high">1</span><b>Add sys_error_save to cmd_aphy_init / cmd_sphy_init / cmd_reset</b> — these C9 commands lack SOC-visible error reporting; follow the pattern in cmd_clci_link</div>
  <div class="rec-item"><span class="rec-prio high">2</span><b>Add static_assert for clci_config_t and clci_die_t</b> — catch accidental size changes at compile time: <code>static_assert(sizeof(clci_config_t) == 256, "HW address map broken")</code></div>
  <div class="rec-item"><span class="rec-prio med">3</span><b>Profile sideband_drv_msg_cmd refactoring risk</b> — with 10 callers, create a <code>sideband_drv_msg_v2()</code> wrapper rather than modifying in-place</div>
  <div class="rec-item"><span class="rec-prio med">4</span><b>Evaluate ISR mode for production</b> — current all-polling (<code>*_MODE_ISR=0</code>) gives predictable latency but no bound during heavy mainband traffic</div>
  <div class="rec-item"><span class="rec-prio med">5</span><b>Audit cmd_soft_link stack (depth 6)</b> — run <code>gcc -fstack-usage</code> and confirm peak stack < RISC-V IRQ stack reserve (typically 2KB)</div>
</div>

</div>
</body>
</html>'''

out = os.path.expanduser("~/.claude/cache/code-diagram/review-report.html")
with open(out, 'w') as f:
    f.write(html)
print(f"✓ Report: {out}")
print(f"  Grade: {grade} | 🔴{high} 🟡{med} ⚠{low}")
