#!/usr/bin/env bash
# Point this machine's Claude Code and Cursor at the slash commands tracked in this repo.
#
# The files under projects/coding-standards/commands/ are the source of truth. This script
# replaces ~/.claude/commands/* and ~/.cursor/{commands,skills}/* with symlinks into them,
# so editing a command in either agent edits the tracked file and `git pull` syncs every Mac.
#
#   commands/shared/  -> BOTH agents. One file, cannot drift.
#   commands/claude/  -> Claude Code only.
#   commands/cursor/  -> Cursor only. /ask (must name the other agent's binary) and /debate (loops it).
#
# Safe to re-run. A pre-existing real file is backed up next to itself before being replaced,
# unless it is already byte-identical to the repo copy.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO/commands"
STAMP="$(date +%Y%m%d-%H%M%S)"
linked=0 backed_up=0 skipped=0 pruned=0

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

# ---------------------------------------------------------------------------
# Prune first. This script only ever CREATED links, so a command that moved or
# was renamed left its old symlink behind — still resolving, or dangling.
#
# The one that matters: ~/.cursor/skills/close-out/ was Cursor's merge-to-staging
# skill back when /close-out meant two different things in the two agents. It is
# now one shared command. Leaving the old skill in place puts a second, stale
# /close-out in Cursor beside the real one — the exact collision this layout
# exists to remove.
# ---------------------------------------------------------------------------
prune_dir() {
  [ -e "$1" ] || return 0
  rm -rf "$1"
  echo "  PRUNED (obsolete): $1"
  pruned=$((pruned + 1))
}
prune_dir "$HOME/.cursor/skills/close-out"

# Sweep dangling symlinks left by any earlier layout.
for d in "$HOME/.claude/commands" "$HOME/.cursor/commands" "$HOME/.claude/skills" "$HOME/.cursor/skills"; do
  [ -d "$d" ] || continue
  while IFS= read -r broken; do
    [ -n "$broken" ] || continue
    rm -f "$broken"
    echo "  PRUNED (dangling): $broken"
    pruned=$((pruned + 1))
  done < <(find "$d" -type l ! -exec test -e {} \; -print 2>/dev/null)
done

# ---------------------------------------------------------------------------
# Shared commands — one tracked file, both agents point at it.
# Claude honours the YAML frontmatter and the !`cmd` context lines; Cursor
# ignores both and renders them as text. That is the accepted cost of one file.
# ---------------------------------------------------------------------------
for f in argue close-out driver ship stack pr-description pr-shots tester; do
  link "shared/$f.md" "$HOME/.claude/commands/$f.md"
  link "shared/$f.md" "$HOME/.cursor/commands/$f.md"
done

# Claude Code only
for f in ask docs-update update-markdown explain tester-up; do
  link "claude/$f.md" "$HOME/.claude/commands/$f.md"
done

# Cursor only — /ask cannot be shared: each side must name the OTHER agent's
# binary. Merged into one file, an agent that misidentifies itself would shell
# out to itself and return its own reasoning as a second opinion, silently.
link "cursor/ask.md" "$HOME/.cursor/commands/ask.md"
link "cursor/debate.md" "$HOME/.cursor/commands/debate.md"

# Shared skills — these stay skills (they fire on intent), not commands.
SHARED_SKILLS=(
  app-staging-data app-staging-lambda-deploy
  # Spec-driven chain (adapted from mattpocock/skills → Acme #403; hub is source of truth)
  grilling grill-with-docs domain-modeling to-spec to-tickets implement tdd code-review
  diagnosing-bugs handoff sentry-to-ticket
)
for s in "${SHARED_SKILLS[@]}"; do
  # an older setup made ~/.claude/skills/<name> a symlink to the ~/.cursor copy; replace it with a real dir
  [ -L "$HOME/.claude/skills/$s" ] && rm -f "$HOME/.claude/skills/$s"
  link "shared/$s/SKILL.md" "$HOME/.claude/skills/$s/SKILL.md"
  link "shared/$s/SKILL.md" "$HOME/.cursor/skills/$s/SKILL.md"
done

# Per-core mesh Fabric rule (Cursor alwaysApply). Source of truth is the hub copy.
FABRIC_MDC_SRC="$(cd "$REPO/../agent-mesh/config/cursor" && pwd)/fabric.mdc"
FABRIC_MDC_DST="$HOME/.cursor/rules/fabric.mdc"
if [ -f "$FABRIC_MDC_SRC" ]; then
  mkdir -p "$(dirname "$FABRIC_MDC_DST")"
  if [ -L "$FABRIC_MDC_DST" ] && [ "$(readlink "$FABRIC_MDC_DST")" = "$FABRIC_MDC_SRC" ]; then
    skipped=$((skipped + 1))
  else
    if [ -f "$FABRIC_MDC_DST" ] && [ ! -L "$FABRIC_MDC_DST" ]; then
      if ! cmp -s "$FABRIC_MDC_DST" "$FABRIC_MDC_SRC"; then
        mv "$FABRIC_MDC_DST" "$FABRIC_MDC_DST.local-$STAMP"
        echo "  BACKED UP (differs from repo): $FABRIC_MDC_DST.local-$STAMP"
        backed_up=$((backed_up + 1))
      else
        rm -f "$FABRIC_MDC_DST"
      fi
    else
      rm -f "$FABRIC_MDC_DST"
    fi
    ln -s "$FABRIC_MDC_SRC" "$FABRIC_MDC_DST"
    linked=$((linked + 1))
  fi
fi

# gh stack wrapper — origin on github-work needs an https://github.com remote for submit/sync
GH_STACK_SRC="$(cd "$REPO/scripts" && pwd)/gh-stack-alias.sh"
GH_STACK_DST="$HOME/.local/bin/gh-stack-alias"
mkdir -p "$(dirname "$GH_STACK_DST")"
if [ -L "$GH_STACK_DST" ] && [ "$(readlink "$GH_STACK_DST")" = "$GH_STACK_SRC" ]; then
  skipped=$((skipped + 1))
elif [ -f "$GH_STACK_DST" ] && [ ! -L "$GH_STACK_DST" ]; then
  if cmp -s "$GH_STACK_DST" "$GH_STACK_SRC"; then
    rm -f "$GH_STACK_DST"
  else
    mv "$GH_STACK_DST" "$GH_STACK_DST.local-$STAMP"
    echo "  BACKED UP (differs from repo): $GH_STACK_DST.local-$STAMP"
    backed_up=$((backed_up + 1))
  fi
  ln -s "$GH_STACK_SRC" "$GH_STACK_DST"
  linked=$((linked + 1))
else
  rm -f "$GH_STACK_DST"
  ln -s "$GH_STACK_SRC" "$GH_STACK_DST"
  linked=$((linked + 1))
fi
chmod +x "$GH_STACK_SRC"

echo "linked $linked, already correct $skipped, backed up $backed_up, pruned $pruned"
echo
echo "Verify:"
echo "  ls -l ~/.claude/commands/ ~/.cursor/commands/"
echo "  command -v gh-stack-alias"
echo "  python3 $REPO/scripts/build-slash-command-doc.py   # regenerate the reference doc"
