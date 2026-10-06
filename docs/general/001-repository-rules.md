```yaml
description: General repository conventions that apply to every repo — pin the VS Code / Cursor Explorer to "mixed" sort order (files and folders interleaved alphabetically) via a committed .vscode/settings.json
globs:
  - "**/.vscode/settings.json"
alwaysApply: false
```

# General repository rules

Conventions that apply to **every** repo regardless of language or framework.

## Explorer sort order — `mixed`

Pin the VS Code / Cursor file Explorer to **`mixed`**: files and folders are sorted
**together** in one alphabetical list, not folders-first. This makes a file's position
predictable from its name alone, no matter whether it's a file or a folder.

**Commit it per-repo** (so it's identical for everyone and travels with the repo) in
`.vscode/settings.json`:

```json
{
  "explorer.sortOrder": "mixed"
}
```

### How to apply

- **Per repo (preferred):** create `.vscode/settings.json` with the snippet above and
  commit it. Workspace settings override user settings, so this wins for everyone.
- **Globally (your machine only):** Command Palette → *Preferences: Open Settings (UI)*
  → search **"explorer sort order"** → set to **Mixed**. This writes to your *user*
  settings (`~/Library/Application Support/Cursor/User/settings.json` /
  `…/Code/User/settings.json`) and applies to all repos, but is **not** shared — still
  commit the per-repo file for teammates.

### `explorer.sortOrder` options (for reference)

| value        | behavior                                                            |
| ------------ | ------------------------------------------------------------------- |
| `default`    | folders first, then files — each alphabetical (VS Code's default)   |
| **`mixed`**  | **files & folders interleaved, alphabetical ← our standard**        |
| `filesFirst` | files first, then folders                                           |
| `type`       | grouped by file extension                                           |
| `modified`   | most-recently-modified first                                        |
| `foldersNestsFiles` | like default, but related files nest under a primary file    |

> Add further universal repo rules (e.g. required root files, line endings, editorconfig)
> to this doc as they're agreed.
