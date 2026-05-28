.PHONY: setup index clean

PROJECT ?=
PYTHON ?= python3

# ── One-command setup ────────────────────────────────────────────────
#   make setup PROJECT=/path/to/your-codebase
#
# Installs deps, detects language, builds AST index, prints MCP config.

ifeq ($(PROJECT),)
  $(error USAGE: make setup PROJECT=/path/to/your-codebase)
endif

setup:
	@echo "═══ code-diagram-mcp setup ═══"
	@echo ""
	@echo "[1/4] Installing dependencies..."
	@$(PYTHON) -m pip install -e "." --break-system-packages --quiet 2>&1 | tail -1 || \
		$(PYTHON) -m pip install -e "." --quiet 2>&1 | tail -1
	@echo "       ✓ tree-sitter + C + Python grammars"
	@echo ""
	@echo "[2/4] Scanning project: $(PROJECT)"
	@$(PYTHON) scripts/init-project.py $(PROJECT)
	@echo ""
	@echo "[3/4] Building AST index..."
	@$(PYTHON) scripts/build-index-ts.py --project $(PROJECT)
	@echo ""
	@echo "[4/4] MCP config — add to ~/.hermes/config.yaml under mcp_servers:"
	@echo ""
	@echo "  code-diagram:"
	@echo "    command: $(PYTHON)"
	@echo "    args:"
	@echo "    - $(PWD)/mcp_server.py"
	@echo "    - --project"
	@echo "    - $(PROJECT)"
	@echo ""
	@echo "Then /reload-mcp in Hermes. Done."

# ── Re-index after code changes ──────────────────────────────────────
index:
	@$(PYTHON) scripts/build-index-ts.py --project $(PROJECT)
