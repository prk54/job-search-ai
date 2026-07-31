#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC}  $1"; }

echo ""
echo "  job-search-ai uninstaller"
echo "  ─────────────────────────"
echo ""

read -r -p "  This will remove ~/.job-search/ and the 3 skill files. Continue? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "  Cancelled."
  exit 0
fi

echo ""

# Remove skills
for skill in job job-build job-profile job-scan job-resume job-intel job-audit job-cover job-apply job-discover; do
  dst="$HOME/.claude/skills/${skill}.md"
  if [ -f "$dst" ]; then
    rm "$dst"
    ok "Removed skill: $skill"
  fi
done

# Remove data directory (ask separately — contains user's generated PDFs)
if [ -d "$HOME/.job-search" ]; then
  read -r -p "  Also remove ~/.job-search/ (includes your generated PDFs and profile)? [y/N] " confirm2
  if [[ "$confirm2" =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/.job-search"
    ok "Removed ~/.job-search/"
  else
    warn "~/.job-search/ kept — your data is safe"
  fi
fi

echo ""
echo "  Done. Claude Code and tectonic are untouched."
echo ""
