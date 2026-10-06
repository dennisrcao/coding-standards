#!/usr/bin/env bash
# gh-stack-alias — gh stack wrapper when origin uses a github.com SSH alias (e.g. github-work).
# gh stack submit/sync/push do not resolve SSH host aliases; they need an https://github.com remote.
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "gh-stack-alias: not inside a git repo" >&2
  exit 1
}

origin_url="$(git remote get-url origin 2>/dev/null || true)"
remote="origin"

case "$origin_url" in
  https://github.com/*)
    remote="origin"
    ;;
  git@github.com:*/* | ssh://git@github.com/*/*)
    remote="origin"
    ;;
  git@github-work:*/* | git@github-personal:*/* | git@*:*/*)
    owner_repo="${origin_url#git@*:}"
    owner_repo="${owner_repo%.git}"
    ghstack_url="https://github.com/${owner_repo}.git"
    if ! git remote get-url ghstack &>/dev/null; then
      git remote add ghstack "$ghstack_url"
      echo "gh-stack-alias: added ghstack remote → $ghstack_url"
    fi
    remote="ghstack"
    ;;
  *)
    echo "gh-stack-alias: unrecognized origin remote: ${origin_url:-<none>}" >&2
    echo "Add an https://github.com/<org>/<repo>.git remote named ghstack, then retry." >&2
    exit 1
    ;;
esac

cmd="${1:-}"
shift || true

case "$cmd" in
  submit)
    if [[ "${1:-}" != "--auto" && "${1:-}" != "--open" ]]; then
      set -- --auto "$@"
    fi
    exec gh stack submit --remote "$remote" "$@"
    ;;
  sync | push)
    exec gh stack "$cmd" --remote "$remote" "$@"
    ;;
  "" | help | -h | --help)
    exec gh stack --help
    ;;
  *)
    exec gh stack "$cmd" "$@"
    ;;
esac
