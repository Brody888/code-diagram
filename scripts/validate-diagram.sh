#!/bin/bash
# ─────────────────────────────────────────────────────
# CLCI Diagram Validator
# 对生成的 .puml 和 .svg 执行 6 项自动检查
#
# Usage: ./validate-diagram.sh <file.puml> [file.svg]
#        若只提供 .puml，先自动调用 plantuml -tsvg 生成 SVG
# ─────────────────────────────────────────────────────
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

FAILURES=0
WARNINGS=0
CHECKS=0

pass()  { echo -e "  ${GREEN}✓${NC} $1"; ((CHECKS++)) || true; }
fail()  { echo -e "  ${RED}✗${NC} $1 — $2"; ((FAILURES++)); ((CHECKS++)) || true; }
warn()  { echo -e "  ${YELLOW}⚠${NC} $1 — $2"; ((WARNINGS++)); ((CHECKS++)) || true; }
header() { echo -e "\n${CYAN}── $1 ──${NC}"; }

# ── Arg parsing ─────────────────────────────────────
PUML="${1:-}"
SVG="${2:-}"

if [ -z "$PUML" ]; then
    echo "Usage: $0 <file.puml> [file.svg]"
    echo "  file.puml — PlantUML source to validate"
    echo "  file.svg  — (optional) pre-rendered SVG to check"
    exit 1
fi

if [ ! -f "$PUML" ]; then
    echo "Error: $PUML not found"
    exit 1
fi

echo "Validating: $PUML"

# Auto-render SVG if not provided
if [ -z "$SVG" ]; then
    SVG="${PUML%.puml}.svg"
    if [ ! -f "$SVG" ]; then
        echo "Rendering SVG..."
        plantuml -tsvg "$PUML" -o "$(dirname "$PUML")" 2>/dev/null || true
    fi
fi

# ═════════════════════════════════════════════════════
# Check 1: PlantUML Syntax
# ═════════════════════════════════════════════════════
header "1. PlantUML Syntax"
if [ -f "$SVG" ]; then
    # Error messages appear as XML comments in the SVG
    if grep -q '<\!--.*[Ee]rror' "$SVG" 2>/dev/null; then
        fail "PlantUML syntax" "error markers found in SVG output"
        grep '<\!--.*[Ee]rror' "$SVG" | head -3 | sed 's/^/    /'
    else
        pass "PlantUML syntax OK"
    fi
else
    fail "PlantUML syntax" "SVG not generated — syntax error suspected"
fi

# ═════════════════════════════════════════════════════
# Check 2: Source Link Completeness
# ═════════════════════════════════════════════════════
header "2. Source Link Completeness"

# Count :...; activity/step nodes — exclude error labels, goto, return, stop
step_count=$(grep -cE '^\s*:.*;$' "$PUML" 2>/dev/null) || step_count=0
step_count=${step_count:-0}
# Exclude steps that don't need source links: fail_* labels, goto/return/stop/detach
nolink_count=$(grep -cE '^\s*:(fail_|goto |return |stop|detach)' "$PUML" 2>/dev/null) || nolink_count=0
nolink_count=${nolink_count:-0}
linkable_steps=$(( step_count - nolink_count ))
# Count [[ links
link_count=$(grep -cE '\[\[/api/source' "$PUML" 2>/dev/null) || link_count=0
link_count=${link_count:-0}

# Activity diagrams: expect steps with source links
if [ "$linkable_steps" -gt 0 ]; then
    link_pct=$(( link_count * 100 / linkable_steps ))
    echo "  Steps: $step_count total, $nolink_count labels (excluded), $linkable_steps linkable"
    echo "  Source links: $link_count (${link_pct}%)"
    if [ "$link_pct" -ge 80 ]; then
        pass "Source link coverage ${link_pct}% (threshold: 80%)"
    elif [ "$link_pct" -ge 50 ]; then
        warn "Source link coverage ${link_pct}% (< 80%)" "consider adding links to remaining steps"
    else
        fail "Source link coverage ${link_pct}%" "most steps lack source links"
    fi
else
    # Sequence/state/component diagrams — different metric
    # Count participant declarations vs note links
    note_links=$(grep -cE '\[\[/api/source' "$PUML" 2>/dev/null) || note_links=0
note_links=${note_links:-0}
    echo "  Note links found: $note_links"
    pass "Sequence/state diagram — link check not applicable"
fi

# Check link format validity
bad_links=$(grep -cE '\[\[/api/source\?file=[^&]*( |%20)' "$PUML" 2>/dev/null) || bad_links=0
bad_links=${bad_links:-0}
if [ "$bad_links" -gt 0 ]; then
    warn "Source links with spaces" "$bad_links links contain unescaped spaces"
fi

# ═════════════════════════════════════════════════════
# Check 3: Register Name Convention
# ═════════════════════════════════════════════════════
header "3. Register Name Convention"

# Find register-like names (ALL_CAPS with at least one underscore)
reg_names=$(grep -oE '\b[A-Z]{2,}[_A-Z0-9]{2,}\b' "$PUML" 2>/dev/null | sort -u) || true
reg_count=$(echo "$reg_names" | grep -c .) || reg_count=0
reg_count=${reg_count:-0}

if [ "$reg_count" -gt 0 ]; then
    # Check for lowercase identifiers that look like register constants
    # (lowercase with _ctrl, _cfg, _lock, _lane, _addr, _data patterns — likely typos)
    bad_regs=$(grep -oE '\b[a-z][a-z0-9_]*_(ctrl|cfg|lock|lane|addr|data|stat|mask|en|int|csr)[0-9]*\b' "$PUML" 2>/dev/null | sort -u) || true
    bad_count=$(echo "$bad_regs" | grep -c .) || bad_count=0
    bad_count=${bad_count:-0}
    if [ "$bad_count" -gt 0 ]; then
        warn "Possible non-standard register names" "$bad_count lowercase register references"
        echo "$bad_regs" | sed 's/^/      /'
    else
        pass "Register naming convention OK ($reg_count UPPER_CASE registers found)"
    fi
else
    pass "No register references detected — check skipped"
fi

# ═════════════════════════════════════════════════════
# Check 4: Product Difference Annotations
# ═════════════════════════════════════════════════════
header "4. Product Difference Annotations"

prod_mentions=$(grep -ciE '(MTTP|SEP|BDP|OTP|SLP|WMP)[0-9]' "$PUML" 2>/dev/null) || prod_mentions=0
prod_mentions=${prod_mentions:-0}
only_notes=$(grep -ciE '\bonly\b' "$PUML" 2>/dev/null) || only_notes=0
only_notes=${only_notes:-0}
diff_notes=$(grep -ciE '(产品|product).*(差异|区别|diff)' "$PUML" 2>/dev/null) || diff_notes=0
diff_notes=${diff_notes:-0}

if [ "$prod_mentions" -gt 0 ]; then
    if [ "$only_notes" -gt 0 ] || [ "$diff_notes" -gt 0 ]; then
        pass "Product differences annotated ($only_notes 'only' markers)"
    else
        warn "Product names mentioned but no 'only' annotations" "verify product differences are labeled"
    fi
else
    pass "No product-specific references — check skipped"
fi

# ═════════════════════════════════════════════════════
# Check 5: Arrow-Legend Consistency
# ═════════════════════════════════════════════════════
header "5. Arrow-Legend Consistency"

# Check for explicit colored arrows OR semantic arrow macros
color_arrows=$(grep -cE '(-\[#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\])|(ARROW_(MMIO|MBOX|SDB|MAINBAND|IRQ|DMA|STATE))' "$PUML" 2>/dev/null) || color_arrows=0
color_arrows=${color_arrows:-0}
has_legend=$(grep -ci 'legend' "$PUML" 2>/dev/null) || has_legend=0
has_legend=${has_legend:-0}

if [ "$color_arrows" -ge 2 ] && [ "$has_legend" -eq 0 ]; then
    warn "Multiple colored arrows ($color_arrows) but no legend" "add legend for readability"
elif [ "$color_arrows" -ge 2 ]; then
    pass "Arrow-legend consistency OK ($color_arrows colored arrows, legend present)"
else
    pass "Single arrow style or no colored arrows — legend optional"
fi

# ═════════════════════════════════════════════════════
# Check 6: SVG XML Well-formedness (fireworks method)
# ═════════════════════════════════════════════════════
header "6. SVG XML Well-formedness"

if [ -f "$SVG" ]; then
    if python3 -c "
import xml.etree.ElementTree as ET
try:
    ET.parse('$SVG')
    print('OK')
except ET.ParseError as e:
    print(f'PARSE_ERROR: {e}')
    exit(1)
" 2>/dev/null; then
        pass "SVG XML well-formed"
    else
        fail "SVG XML parse error" "run 'xmllint --noout $SVG' for details"
    fi
else
    warn "SVG not found" "cannot validate XML — render first with plantuml -tsvg"
fi

# ═════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════
echo -e "\n──────────────────────────────────────────"
echo -e "Results: ${GREEN}$((CHECKS - FAILURES - WARNINGS)) passed${NC}, ${YELLOW}$WARNINGS warnings${NC}, ${RED}$FAILURES failures${NC} (total $CHECKS checks)"
echo "──────────────────────────────────────────"

if [ "$FAILURES" -gt 0 ]; then
    exit 1
fi
