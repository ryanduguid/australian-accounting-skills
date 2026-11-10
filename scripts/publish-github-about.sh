#!/usr/bin/env bash
# Copyright 2026 Ryan Duguid
# SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0

# Apply docs/DISCOVERY.md to GitHub About. Requires gh, authenticated to
# ryanduguid/australian-accounting-skills with repo metadata write access.
set -euo pipefail

REPO="ryanduguid/australian-accounting-skills"
DESCRIPTION="Australian tax and accounting agent skills for Claude Code and Codex: review-ready workpapers for BAS, FBT, Division 7A, trusts, payroll and practice compliance."
HOMEPAGE="https://duguid.com.au/tools/australian-tax-ai-agents/"
TOPICS=(
  accounting
  accounting-automation
  agent-skills
  ai-agents
  ato
  australia
  australian-accounting
  australian-tax
  bas
  claude-code
  claude-skills
  codex
  division-7a
  fbt
  public-practice
  python
  stp
  tax
  tax-prep
  xero
)

if ! command -v gh >/dev/null 2>&1; then
  echo "gh is required" >&2
  exit 1
fi

gh repo edit "$REPO" --description "$DESCRIPTION" --homepage "$HOMEPAGE"
topic_args=()
for topic in "${TOPICS[@]}"; do
  topic_args+=(-f "names[]=$topic")
done
# Set the whole topic list so removals apply too and drift cannot accumulate.
gh api -X PUT "repos/$REPO/topics" "${topic_args[@]}" --jq '.names | length'
echo "Updated $REPO About. Pin this repository from github.com/ryanduguid (Customize your pins)."
