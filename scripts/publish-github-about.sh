#!/usr/bin/env bash
# Apply docs/DISCOVERY.md to GitHub About. Requires gh, authenticated to
# ryanduguid/MaryAddisonHamilton with repo metadata write access.
set -euo pipefail

REPO="ryanduguid/MaryAddisonHamilton"
DESCRIPTION="Claude Code, Codex, and portable agent skills for Australian public-practice workflows: BAS tie-out, FBT, Division 7A, STP finalisation, and workpapers. Prep-only. Not lodgment. Not tax advice."
HOMEPAGE="https://github.com/ryanduguid/MaryAddisonHamilton#install"
TOPICS=(
  accounting
  accounting-automation
  agent-skills
  ai-agents
  ato
  australia
  australian-tax
  bas
  bas-agent
  claude-code
  claude-code-skills
  codex
  division-7a
  fbt
  mcp
  stp
  tax-prep
  xero
)

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required" >&2
  exit 1
fi

gh repo edit "$REPO" --description "$DESCRIPTION" --homepage "$HOMEPAGE"
topic_flags=()
for topic in "${TOPICS[@]}"; do
  topic_flags+=(--add-topic "$topic")
done
gh repo edit "$REPO" "${topic_flags[@]}"
echo "Updated $REPO About. Pin this repository from github.com/ryanduguid (Customize your pins)."
