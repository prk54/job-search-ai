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
  warn "tectonic not found. PDF compilation won't work."
  echo "     Install with: brew install tectonic"
  echo "     (continuing setup — you can install tectonic later)"
fi

echo ""

# ─── Create directories ────────────────────────────────────────────────────────

info "Creating ~/.job-search/ ..."
mkdir -p "$JOB_SEARCH_DIR/templates" "$JOB_SEARCH_DIR/output" "$JOB_SEARCH_DIR/intel"
ok "Directories ready"

# ─── Copy skills ───────────────────────────────────────────────────────────────

info "Installing skills to ~/.claude/skills/ ..."
mkdir -p "$SKILLS_DIR"

for skill in job-profile job-scan job-resume job-intel; do
  src="$SCRIPT_DIR/skills/${skill}.md"
  dst="$SKILLS_DIR/${skill}.md"
  if [ -f "$dst" ]; then
    warn "Skill $skill already exists — overwriting"
  fi
  cp "$src" "$dst"
  ok "Installed /job-${skill#job-} skill"
done

# ─── Copy templates ────────────────────────────────────────────────────────────

info "Copying LaTeX templates..."
cp "$SCRIPT_DIR/templates/jake-resume.tex" "$JOB_SEARCH_DIR/templates/jake.tex"
cp "$SCRIPT_DIR/templates/classic.tex" "$JOB_SEARCH_DIR/templates/classic.tex"
ok "Templates ready (jake, classic)"

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
echo "  2. Open Claude Code in any project:"
echo "     claude"
echo ""
echo "  3. Parse your resume:"
echo "     /job-profile ~/Downloads/resume.pdf"
echo ""
echo "  4. Find matching roles:"
echo "     /job-scan"
echo ""
echo "  5. Generate a tailored resume:"
echo "     /job-resume <JD URL>"
echo ""
