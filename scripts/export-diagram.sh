#!/bin/bash
# ─────────────────────────────────────────────────────
# CLCI Diagram Exporter — SVG + PNG 双输出管线
#
# Usage: ./export-diagram.sh <file.puml> [-w width] [-o output_dir]
#   file.puml  — PlantUML source (必需)
#   -w width   — PNG 宽度像素 (默认 1920)
#   -o dir     — 输出目录 (默认: file.puml 所在目录)
#   --no-png   — 只生成 SVG，跳过 PNG 导出
# ─────────────────────────────────────────────────────
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Defaults ────────────────────────────────────────
WIDTH=1920
NO_PNG=false

# ── Arg parsing ─────────────────────────────────────
PUML=""
while [ $# -gt 0 ]; do
    case "$1" in
        -w) WIDTH="$2"; shift 2 ;;
        -o) OUT_DIR="$2"; shift 2 ;;
        --no-png) NO_PNG=true; shift ;;
        -h|--help)
            echo "Usage: $0 <file.puml> [-w width] [-o output_dir] [--no-png]"
            exit 0
            ;;
        *) PUML="$1"; shift ;;
    esac
done

if [ -z "$PUML" ] || [ ! -f "$PUML" ]; then
    echo "Usage: $0 <file.puml> [-w width] [-o output_dir]"
    echo "Error: .puml file required"
    exit 1
fi

OUT_DIR="${OUT_DIR:-$(dirname "$PUML")}"
BASENAME="$(basename "${PUML%.puml}")"
SVG_PATH="$OUT_DIR/$BASENAME.svg"
PNG_PATH="$OUT_DIR/$BASENAME.png"

echo -e "${CYAN}Exporting: $PUML${NC}"

# ═════════════════════════════════════════════════════
# Step 1: SVG render
# ═════════════════════════════════════════════════════
echo -e "\n${CYAN}[1/2] Rendering SVG...${NC}"

if plantuml -tsvg "$PUML" -o "$OUT_DIR" 2>&1; then
    if [ -f "$SVG_PATH" ]; then
        svg_size=$(du -h "$SVG_PATH" | cut -f1)
        echo -e "  ${GREEN}✓${NC} SVG generated: $SVG_PATH ($svg_size)"
    else
        echo -e "  ${YELLOW}⚠${NC} plantuml exited OK but SVG not found at $SVG_PATH"
    fi
else
    echo -e "  ${RED}✗${NC} plantuml render failed"
    exit 1
fi

# ═════════════════════════════════════════════════════
# Step 2: PNG export (cairosvg → rsvg-convert fallback)
# ═════════════════════════════════════════════════════
if $NO_PNG; then
    echo -e "\n${YELLOW}PNG export skipped (--no-png)${NC}"
    echo -e "\n${GREEN}Done: $SVG_PATH${NC}"
    exit 0
fi

echo -e "\n${CYAN}[2/2] Exporting PNG (target: ${WIDTH}px)...${NC}"

# Compute scale factor: width / SVG native viewBox width
# PlantUML default viewBox varies; use 960 as common base
scale=$(python3 -c "print(round(${WIDTH}/960, 2))")

png_ok=false

# Method 1: cairosvg (recommended — good CSS support)
if python3 -c "import cairosvg" 2>/dev/null; then
    echo "  Trying cairosvg (scale=${scale})..."
    if python3 -c "
import cairosvg
cairosvg.svg2png(url='$SVG_PATH', write_to='$PNG_PATH', scale=${scale})
" 2>/dev/null; then
        png_size=$(du -h "$PNG_PATH" | cut -f1)
        echo -e "  ${GREEN}✓${NC} PNG (cairosvg): $PNG_PATH ($png_size)"
        png_ok=true
    else
        echo -e "  ${YELLOW}⚠${NC} cairosvg failed, trying rsvg-convert..."
    fi
else
    echo "  cairosvg not available (pip install cairosvg)"
fi

# Method 2: rsvg-convert (fallback — may drop CSS filters)
if ! $png_ok; then
    if command -v rsvg-convert >/dev/null 2>&1; then
        echo "  Trying rsvg-convert (width=${WIDTH})..."
        if rsvg-convert -w "$WIDTH" "$SVG_PATH" -o "$PNG_PATH" 2>/dev/null; then
            png_size=$(du -h "$PNG_PATH" | cut -f1)
            echo -e "  ${YELLOW}⚠${NC} PNG (rsvg-convert): $PNG_PATH ($png_size)"
            echo -e "  ${YELLOW}   Note: may drop CSS styles — prefer cairosvg: pip install cairosvg${NC}"
            png_ok=true
        fi
    else
        echo "  rsvg-convert not available (brew install librsvg)"
    fi
fi

if ! $png_ok; then
    echo -e "  ${RED}✗${NC} PNG export failed — install one of:"
    echo "      pip install cairosvg     (recommended)"
    echo "      brew install librsvg     (rsvg-convert)"
    echo "      npm install puppeteer    (highest fidelity)"
fi

# ═════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════
echo -e "\n──────────────────────────────────────────"
echo -e "Output files:"
echo -e "  SVG: $SVG_PATH"
if $png_ok; then
    echo -e "  PNG: $PNG_PATH"
else
    echo -e "  PNG: ${RED}not generated${NC}"
fi
echo "──────────────────────────────────────────"
