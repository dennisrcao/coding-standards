#!/usr/bin/env bash
# Point this machine's Claude Code and Cursor at the slash commands tracked in this repo.
#
# The files under projects/coding-standards/commands/ are the source of truth. This script
# replaces ~/.claude/commands/* and ~/.cursor/{commands,skills}/* with symlinks into them,
# so editing a command in either agent edits the tracked file and `git pull` syncs every Mac.
#
# Safe to re-run. A pre-existing real file is backed up next to itself before being replaced,
# unless it is already byte-identical to the repo copy.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO/commands"
STAMP="$(date +%Y%m%d-%H%M%S)"
linked=0 backed_up=0 skipped=0

link() {           # link <repo-relative source> <absolute destination>
  local src="$SRC/$1" dst="$2"
  if [ ! -f "$src" ]; then
    echo "  MISSING in repo: $1" >&2
    return 1
  fi
  mkdir -p "$(dirname "$dst")"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    skipped=$((skipped + 1))
    return 0
  fi
  if [ -f "$dst" ] && [ ! -L "$dst" ]; then
    if cmp -s "$dst" "$src"; then
      rm -f "$dst"                       # identical — nothing to preserve
    else
      mv "$dst" "$dst.local-$STAMP"
      echo "  BACKED UP (differs from repo): $dst.local-$STAMP"
      backed_up=$((backed_up + 1))
    fi
  else
    rm -f "$dst"
  fi
  ln -s "$src" "$dst"
  linked=$((linked + 1))
}

echo "Source of truth: $SRC"

# Claude Code — ~/.claude/commands/<name>.md  ->  /<name>
for f in close-out ask CROSSCHECK ship docs-update pr-description update-markdown; do
  link "claude/$f.md" "$HOME/.claude/commands/$f.md"
done

# Cursor — commands, plus /ship shared with the Claude copy (one file, both agents)
link "cursor/ask.md"            "$HOME/.cursor/commands/ask.md"
link "cursor/CROSSCHECK.md"     "$HOME/.cursor/commands/CROSSCHECK.md"
link "claude/ship.md"           "$HOME/.cursor/commands/ship.md"

# Cursor — skills use a folder plus SKILL.md, and the name comes from the frontmatter
link "cursor/close-out/SKILL.md" "$HOME/.cursor/skills/close-out/SKILL.md"

echo "linked $linked, already correct $skipped, backed up $backed_up"
echo
echo "Verify:"
echo "  ls -l ~/.claude/commands/ ~/.cursor/commands/ ~/.cursor/skills/close-out/"
echo "  python3 $REPO/scripts/build-slash-command-doc.py   # regenerate the reference doc"
