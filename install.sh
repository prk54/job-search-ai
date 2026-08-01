#!/usr/bin/env bash
set -e

# ─── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC}  $1"; }
err()  { echo -e "${RED}✗${NC} $1"; }
info() { echo -e "${CYAN}→${NC} $1"; }

echo ""
echo "  job-search-ai installer"
echo "  ───────────────────────"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOB_SEARCH_DIR="$HOME/.job-search"
SKILLS_DIR="$HOME/.claude/skills"

# ─── Check prerequisites ────────────────────────────────────────────────────────

info "Checking prerequisites..."

# Claude Code
if command -v claude &>/dev/null; then
  ok "Claude Code found ($(claude --version 2>/dev/null | head -1))"
else
  err "Claude Code not found. Install from https://claude.ai/code"
  exit 1
fi

# tectonic
if command -v tectonic &>/dev/null; then
  ok "tectonic found ($(tectonic --version 2>/dev/null))"
else
  warn "tectonic not found. PDF compilation (/job-resume) won't work."
  echo "     Install with: brew install tectonic"
  echo "     (continuing setup — install tectonic before using /job-resume)"
fi

# pdftotext (needed by /job-profile and /job-audit)
if command -v pdftotext &>/dev/null; then
  ok "pdftotext found"
else
  warn "pdftotext not found. Resume PDF parsing (/job-profile) will fall back to Claude's native PDF reader."
  echo "     Install with: brew install poppler"
  echo "     (optional — Claude can still read PDFs without it)"
fi

# python3 (needed by /job-audit for PDF text extraction)
if command -v python3 &>/dev/null; then
  ok "python3 found ($(python3 --version 2>/dev/null))"
else
  warn "python3 not found. /job-audit won't be able to verify ATS parsability."
  echo "     Install with: brew install python3"
fi

echo ""

# ─── Create directories ────────────────────────────────────────────────────────

info "Creating ~/.job-search/ ..."
mkdir -p "$JOB_SEARCH_DIR/templates" "$JOB_SEARCH_DIR/output" "$JOB_SEARCH_DIR/intel"
ok "Directories ready"

# ─── Copy skills ───────────────────────────────────────────────────────────────

info "Installing skills to ~/.claude/skills/ ..."
mkdir -p "$SKILLS_DIR"

for skill in job job-build job-profile job-scan job-resume job-intel job-audit job-cover job-apply job-discover job-linkedin; do
  src="$SCRIPT_DIR/skills/${skill}.md"
  dst="$SKILLS_DIR/${skill}.md"
  if [ -f "$dst" ]; then
    warn "Skill $skill already exists — overwriting"
  fi
  cp "$src" "$dst"
  ok "Installed /${skill}"
done

info "Copying LaTeX templates and seed lists..."
cp "$SCRIPT_DIR/templates/jake-resume.tex" "$JOB_SEARCH_DIR/templates/jake.tex"
cp "$SCRIPT_DIR/templates/career-ops.tex" "$JOB_SEARCH_DIR/templates/career-ops.tex"
cp "$SCRIPT_DIR/templates/companies_seed.json" "$JOB_SEARCH_DIR/companies_seed.json"
ok "Templates and seeds ready"

info "Copying automation scripts..."
mkdir -p "$JOB_SEARCH_DIR/scripts"
cp "$SCRIPT_DIR/scripts/apply.py" "$JOB_SEARCH_DIR/scripts/apply.py"
chmod +x "$JOB_SEARCH_DIR/scripts/apply.py"
cp "$SCRIPT_DIR/scripts/discover.py" "$JOB_SEARCH_DIR/scripts/discover.py"
chmod +x "$JOB_SEARCH_DIR/scripts/discover.py"
ok "Scripts ready (apply.py, discover.py)"

# ─── Config files (only if they don't exist — never overwrite user data) ────────

if [ ! -f "$JOB_SEARCH_DIR/config.yml" ]; then
  cp "$SCRIPT_DIR/config/user.example.yml" "$JOB_SEARCH_DIR/config.yml"
  ok "Created ~/.job-search/config.yml"
else
  warn "~/.job-search/config.yml already exists — skipping (your settings preserved)"
fi

if [ ! -f "$JOB_SEARCH_DIR/companies.yml" ]; then
  cp "$SCRIPT_DIR/templates/companies.example.yml" "$JOB_SEARCH_DIR/companies.yml"
  ok "Created ~/.job-search/companies.yml (30+ companies pre-configured)"
else
  warn "~/.job-search/companies.yml already exists — skipping (your companies preserved)"
fi

if [ ! -f "$JOB_SEARCH_DIR/CLAUDE.md" ]; then
  cp "$SCRIPT_DIR/templates/CLAUDE.example.md" "$JOB_SEARCH_DIR/CLAUDE.md"
  ok "Created ~/.job-search/CLAUDE.md (workspace context for Claude Code)"
else
  warn "~/.job-search/CLAUDE.md already exists — skipping"
fi

# ─── Standalone Python CLI installation ────────────────────────────────────────

info "Installing job-search Python package locally..."
if python3 -m pip install --user -e "$SCRIPT_DIR" --break-system-packages &>/dev/null; then
  ok "Python package installed locally (job-search binary created)"
  PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  USER_BIN="$HOME/Library/Python/$PY_VER/bin"
  if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
    warn "The 'job-search' script is installed in $USER_BIN which is not on your PATH."
    warn "Add it to your PATH (e.g. export PATH=\"\$PATH:$USER_BIN\" in ~/.zshrc)"
  fi
else
  warn "Could not install python package system-wide. Run via: python3 -m job_search.cli"
fi


# ─── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo -e "  ${GREEN}Installation complete!${NC}"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Customise your setup:"
echo "     nano ~/.job-search/config.yml      # set your city, TC target, role level"
echo "     nano ~/.job-search/companies.yml   # add/remove target companies"
echo ""
echo "  2. Open Claude Code and use /job as the single entry point:"
echo "     claude"
echo "     /job                               # status dashboard"
echo "     /job build                         # build base resume (interview or paste)"
echo "     /job profile ~/Downloads/resume.pdf"
echo "     /job discover                      # discover target companies dynamically"
echo "     /job scan"
echo "     /job intel stripe"
echo "     /job resume https://careers.airbnb.com/..."
echo "     /job cover https://careers.airbnb.com/..."
echo "     /job apply https://careers.airbnb.com/..."
echo "     /job full stripe airbnb databricks # full pipeline for 3 companies"
echo ""
echo "  Or use individual skills directly:"
echo "     /job-build  /job-profile  /job-scan  /job-intel  /job-resume  /job-cover  /job-apply  /job-discover"
echo ""
