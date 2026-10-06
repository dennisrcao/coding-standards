---
description: Put before/after screenshots in a PR description — shoots each surface on the base deploy and on the PR preview, hosts them, and rewrites the body
argument-hint: "[PR number, and/or which screens to capture — optional]"
allowed-tools: Bash(git:*), Bash(gh:*), Bash(aws:*), Bash(curl:*), Bash(mv:*), Bash(ls:*), Read, Write, Grep, Glob
---

## Context (auto-collected)

- Current branch: !`git rev-parse --abbrev-ref HEAD`
- Repo: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a gh repo"`
- PR for this branch: !`gh pr view --json number,title,headRefName,url -q '"#\(.number) \(.title) — \(.url)"' 2>/dev/null || echo "none"`
- Files changed: !`git diff --stat origin/HEAD...HEAD 2>/dev/null | tail -30`
- Preview slug for this branch: !`git rev-parse --abbrev-ref HEAD | tr '/' '-' | tr -cd 'a-zA-Z0-9-\n' | tr 'A-Z' 'a-z' | cut -c1-40`

Extra instruction from me: $ARGUMENTS

## Your task

Give the reviewer the two pictures instead of a paragraph: for each surface this PR
changes, capture the **same route** on the base deploy (before) and on this PR's preview
(after), host both, and rewrite the PR body with them embedded.

Unlike `/pr-description`, this one **does** edit the PR — that is the point. Say so before
you do it.

## Stop first if any of these hold

- **No deploy of the base branch to shoot the "before" on.** The "after" has a fallback
  (section 1); the "before" does not — a localhost "before" is a claim about the base that
  nothing backs.
- **The PR is backend-only.** Previews are frontend builds; an API or worker change has no
  visual diff. Say so and stop.
- **The change isn't visual.** Two identical screenshots imply a difference that isn't
  there — worse than none.
- **A screen would show real client work or PII and the host is public.** The S3 host in
  section 4 is world-readable; the orphan-branch host is gated by repo access. On a public
  host, use test fixtures or drop that surface. On a private repo, say in the body that the
  shots show live data, so nobody forwards them.

## 1. Resolve the two hosts

Resolve, don't assume. Three ladders, in order; the first rung that answers wins.

**The "after" host — this PR's deploy.**

1. **GitHub Deployments.** Vercel, Netlify, Railway and most CI previews record one:
   ```bash
   sha=$(gh pr view "$PR" --json headRefOid -q .headRefOid)
   for id in $(gh api "repos/{owner}/{repo}/deployments?sha=$sha&per_page=5" -q '.[].id'); do
     gh api "repos/{owner}/{repo}/deployments/$id/statuses" -q '.[0] | "\(.state) \(.environment) \(.environment_url)"'
   done
   ```
   Take the newest `success`. Vercel previews sit behind Vercel Authentication; an unauthed
   `curl` answers `302 → vercel.com/sso-api`. Get a bypass link (the Vercel MCP's
   `get_access_to_vercel_url`, or a `_vercel_share` link from the dashboard), open it once in
   the browser to set the cookie, then navigate normally.
2. **A workflow that builds its own preview path.** No deployment records → read the deploy
   workflow for the pattern: `grep -n "SLUG=\|deploy_url=\|preview" .github/workflows/*.yml`.
   app-monorepo: `https://client.staging.example.com/preview/<slug>`, slug = branch
   lower-cased, `/` → `-`, non-alphanumerics dropped, cut at 40.
3. **The local dev server on the PR branch — the fallback, and it must be labeled.** Some
   previews cannot be signed into (an OAuth client id that exists only in Production, a
   callback URL Google will not accept for a per-deployment hostname). When the "after" cannot
   be reached on a deploy, shoot it from a checkout on the PR branch and put three things in
   the body: that it is local, the port, and the commit (`git rev-parse --short HEAD`). Put
   *why* the preview could not be used in one sentence and link the preview anyway. Same
   code is not the same deploy; the body says which one the picture is.

**The "before" host — the base branch's deploy.** Same ladder, keyed on the base:

```bash
base=$(gh pr view "$PR" --json baseRefName -q .baseRefName)
```

- Base is the repo default → its production deploy. Deployments API with
  `environment=Production`, or the repo's homepage (`gh repo view --json homepageUrl`), or
  for app-monorepo the staging host. **No localhost "before", ever** — the body says the
  image is the base deploy, so it has to be.
- Base is another feature branch (a stacked PR) → **that branch's preview**, resolved the same
  way with its head sha. Shooting production instead attributes the parent PR's changes to
  this one. Label the sections **"Base branch (#N)"**, not "Production" or "Staging".

**Shoot every "before" from a deploy — never reuse a file from an earlier PR's folder.** If a
surface is genuinely untouched by this PR and you are showing it as context, put it in its
own section and say it is unchanged.

Confirm both hosts actually serve before capturing anything:

```bash
curl -s -o /dev/null -w "%{http_code}\n" "<host>/"
```

Not 200 (or a 302 to an SSO page you have not got past yet) → fix that first. Shooting a
stale or missing deploy produces a confidently wrong PR body.

## 2. Choose the surfaces

Per surface: a `label`, a `route`, and one sentence on what changed.

**Confirm gate — skip it when surfaces are already locked.** Infer from the diff, then:

| Who is running | What to do |
|---|---|
| Interactive `/pr-shots` with a human in the chat | Confirm the surface list **before** shooting |
| Mesh tester / Fabric `playwright` / `$ARGUMENTS` already lists `surfaces` or `prs[].surfaces` | **Do not wait.** Use the locked list. Say in the report which list you used |
| Stack job that names several PRs | Run each PR’s shot pass **to completion** (host + `gh pr edit`) before claiming done — parallel tabs OK; do not stop after resolving hosts |

Leaving “waiting for confirm” with no human in the loop is a failed run — the PR body stays
the old text and looks like the command never ran.

- **Same data both sides** — same ids, same fixture. Different data either side and the
  reader cannot separate your change from the content.
- **Pick a fixture that exposes the change.** A count bug needs a record where the counts
  differ; a one-item fixture hides it.
- **One outcome per section, not one surface.** The body is organised by what is now
  true for the user ("two dead messages now open the picker"), and each outcome carries
  whatever shots prove it — one surface can serve two outcomes, one outcome can need three
  shots. Three places changed for one reason is one section.
- **A surface can be a FLOW, not a moment.** When the difference only appears after a
  sequence — save, then reload; filter, then paginate — shoot the steps that carry it, on
  both hosts, and write the action between them. A single pair frozen at one moment cannot
  show a change that only exists after four clicks, and shooting the wrong moment produces
  two identical images of a real difference.

## 3. Capture

A deploy and a preview are different origins, so a sign-in on one does not carry to the
other. If you land on a sign-in screen, **stop and ask me to log in** — never drive an
OAuth flow. If the sign-in itself is broken on the preview (section 1, rung 3), that is the
moment to fall back to the local server, not to keep trying.

Navigate, perform whatever interaction the shot needs, then screenshot.

**Capture tool:** shared **headed** Playwright MCP (`/PLAYWRIGHT-start`, then
`mcp__playwright__*`). First call opens visible Chrome. Do not use headless Playwright CLI,
curl-only "captures", or Cursor `cursor-ide-browser` unless the user explicitly chose that.
When auth blocks, stop and ask the human to sign in in the Playwright Chrome window.

**Shared browser — one window, many tabs (mesh / dual-host pr-shots):** One headed Chrome on
`:8931` serves every MCP **client** on the machine — not one tab per tester unless each tester
claims one
([060-playwright-mcp-isolation.md](../../docs/workflow/060-playwright-mcp-isolation.md)). Each
client's **first** Playwright call must be `browser_tabs({ action: "new", url })`, never bare
`browser_navigate`. A second client that navigates first inherits the first client's tab and
invalidates before/after.

| Mode | When |
|---|---|
| **Parallel (preferred)** | Driver assigns **scope a → before host**, **scope b → after host** at the same time. Each tester opens **its own** tab (`browser_tabs` `new` with that host's URL) before any other Playwright call. Include `browser_tabs` `list` + final URL in `done`. |
| **Serial (always valid)** | One tester finishes before; driver sends after to the other scope (or the same tester with a **second** `browser_tabs` `new`). Use when unsure, when MCP reconnect failed, or when only one tester has Playwright tools. |

Never open a second HTTP MCP client to "share" the server while another agent is mid-flow on the
same tab. Do not close tabs another scope opened.

> **Playwright MCP writes screenshots to its own cwd** (the repo root), not the directory
> you name, and refuses absolute paths outside its allowed roots. Pass a bare filename,
> then `mv` it. Sweep the repo root afterwards — the files are gitignored there, but
> leaving them is still litter.

**Before shooting the "after", assert the change is actually on screen** — read the text
back and check it. A screenshot of a stale bundle is indistinguishable from a screenshot
of a working fix.

## 4. Host the images

GitHub has no API for uploading an image to a PR body — drag-and-drop is browser-only. So put
the files somewhere the reviewer's browser can fetch and reference them by URL. Which
somewhere is a per-repo decision, kept here:

| Repo | Host | Why |
|---|---|---|
| `your-org/app-monorepo` | S3, under the staging CDN (below) | Shared repo — no binaries in its git; the CDN already exists |
| everything else | an orphan `pr-shots` branch in the same repo (below) | Private repos; nothing external, no credentials, lives as long as the repo |

Add a row when a repo needs something else. Do not invent a host at run time.

### Orphan branch (the default)

One branch, `pr-shots`, no history in common with the default branch, one folder per PR.
Built with plumbing so nothing in the working tree is touched:

```bash
OUT=<dir with the PNGs>; IDX=$(mktemp); rm -f "$IDX"
git fetch -q origin pr-shots 2>/dev/null && parent=$(git rev-parse origin/pr-shots) || parent=""
[ -n "$parent" ] && GIT_INDEX_FILE=$IDX git read-tree "$parent"
for f in "$OUT"/*.png; do
  GIT_INDEX_FILE=$IDX git update-index --add --cacheinfo "100644,$(git hash-object -w "$f"),$PR/$(basename "$f")"
done
root=$(GIT_INDEX_FILE=$IDX git write-tree)
commit=$(echo "pr-shots: PR #$PR" | git commit-tree "$root" ${parent:+-p "$parent"})
git push -q origin "${commit}:refs/heads/pr-shots"   # braces matter: zsh reads $commit:r as a modifier
```

Reference each file as

```
https://github.com/<owner>/<repo>/blob/pr-shots/<PR>/<file>.png?raw=true
```

GitHub renders that inline for anyone who can see the repo and serves 404 to everyone else.
Verify with an authenticated fetch of the raw path, since the `blob` URL itself will not
answer a token:

```bash
curl -sL -o /dev/null -w "%{http_code} %{content_type}\n" \
  -H "Authorization: token $(gh auth token)" \
  "https://raw.githubusercontent.com/<owner>/<repo>/pr-shots/<PR>/<file>.png"
```

Expect `200 image/png`. **Before the first push to a repo, check no workflow triggers on
pushes to arbitrary branches** (`grep -A3 "^on:" .github/workflows/*.yml`); a bare `push:`
with no `branches:` filter would run CI on a branch of PNGs.

### S3 (app-monorepo)

```bash
aws --profile app-staging s3 cp "$f" \
  "s3://app-staging-products/client/preview/pr-shots/$PR/$f" \
  --content-type image/png --cache-control "max-age=31536000"
```

→ `https://client.staging.example.com/preview/pr-shots/$PR/$f`

**The `preview/` segment is load-bearing.** `deploy-frontend.yml` syncs the build over
`client/` with `--delete --exclude "preview/*"`. Anywhere else under `client/` and the next
staging deploy removes the images, leaving broken embeds in a PR nobody rechecks. Verify
that exclude still exists before relying on it. This host is **public**: a screen with real
client work or PII does not go here — use a fixture or drop the surface.

### Neither works

Emit the body with `[[PASTE <file>.png]]` placeholders and say so. Do not invent a host.

Curl every URL for 200 before writing the body.

## 5. Write the body

**Outcome-first.** A section heading says what is now true, not where you clicked. The
reader should get "what changed?" from the headings alone, and "how do you know?" from the
shots under them. Procedure ("Step 1: upload, Step 2: click the band") is how you *got* the
evidence — it is not the shape of the evidence.

**Stacked sections. Never a table.** GitHub inserts images as block elements; dropping one
into a pipe-delimited row collapses the table and spills the other cells into prose.

### Shape

```markdown
<One sentence naming the problem the PR removes. Bold the phrase the user actually sees.>

**Provenance:** <only when nobody asked for it — review finding, hub leftover, seen while
doing X. Say what makes it worth doing now. Omit for a ticketed request.>

**Fixture for every shot below:** <file / campaign / route. One line.>

**How to reach this screen:**

> `+ New session` → **<campaign>** → … → click **Retouch**

<The other door(s), and whether each was checked or assumed.>

---

## 1 · <What is now true — a sentence, e.g. "Two dead messages now open the source picker">

### Base

[<before-host><route>](<before-host><route>)

![<label> before](<cdn>/1a-<slug>-BEFORE.png)

<One to three sentences: what the reader is looking at and what is wrong with it. Point at
the thing in the picture — "the amber band, the empty state, and the pill; only the pill
does anything". If a click did nothing, say how you know (identical screenshot, md5).>

### This PR

[<after-host><route>](<after-host><route>)

![<label> after](<cdn>/2a-<slug>-AFTER.png)

<What changed, in the same terms. If proving it needs a second moment — the picker open,
the page after reload — put that shot here, under one line saying what action produced it.>

![band opens picker](<cdn>/2c-<slug>-AFTER.png)

---

## 2 · <Next outcome>

…

---

## How it is wired            ← rationale, after the evidence
## Deliberately not done      ← what stays as-is and why; invite the reviewer to disagree
## Verification               ← the commands, the counts, mutation checks
## Found while shooting these ← anything the shoot surfaced, and whether it is fixed here

*Images live at `<bucket path>`. <One line on why that path survives deploys.>*
```

**The preamble is four short items, then the rule.** Problem, provenance, fixture, entry
path. No summary of what changed above the first section — the `## N ·` headings are that
summary, and a paragraph of it pushes the first picture below the fold. Provenance earns
its line only when the PR is not answering a request: a reviewer who cannot see why this
exists will ask, and "nobody asked, here is why now" is the honest answer.

**Every image gets a caption below it, not a label above it.** The caption is where the
comparison actually happens — "three statements about the missing product, none of them a
way to set it" tells the reader what to look for in a screenshot they would otherwise
skim. One to three sentences, prose, pointing at things in the picture. A bare `**Before**`
over an image is not a caption.

**Link on its own line, above the image, as the full URL.** Write it as
`[https://host/path?query](https://host/path?query)` — text and target identical — never
`[open](…)` or `[here](…)`. A reviewer should see which host and which route a shot came
from without hovering, and be able to copy it as plain text. This applies to every link in
the body.

**The link must open the screen in the picture, not the front door.** `<route>` means the
route the shot was taken on — `/v2/session/retouch?project=…&candidate=…`, with the query —
read from the address bar at the moment you took it, per side (the two hosts usually have
different record ids). A reviewer who clicks and lands on a home screen has to redo your
navigation to find what you photographed.

**If the pictured state does not survive a cold load, say so and give the navigation.**
Some state only exists after a client-side transition — a suggestion computed on mount, an
unsaved edit. The deep link is still the right link; add one line naming what will be
missing on arrival and the click path that reproduces it. Silently linking a URL that
renders a different state than the image above it is worse than no link.

**Say how you reached the screen, and check the other doors.** The entry-path quote in the
preamble costs one line and prevents the most common review question. Then name the other
entry points and say whether you verified them or not. If a door behaves differently, that
is a finding and gets its own section, not a footnote.

**A flow is an outcome whose proof takes several moments.** Keep it in one section, and
put each moment under a bold step line with the action that reaches it:

```markdown
## 1 · The swap survives a reload

*Steps: upload → swap → Save → reload.*

**After Save**

### Base
…link, image, caption…
### This PR
…link, image, caption…

**Then reload the page**

### Base
…
### This PR
…
```

Number the files by outcome and moment (`1a-`, `1b-`, `2a-`) so the folder reads in order.
Shoot only the moments where something differs or where the reader would otherwise lose
the thread — not every click.

**A local "after" is labeled in the heading, not buried in a footnote.** `### This PR —
local `:3001` on `<branch>``, with the port and commit in the preamble and the unreachable
preview linked beside them. A reader must never mistake a dev-server shot for a deploy.

**Rationale goes after the comparisons.** "How it is wired", "deliberately not done",
verification, and anything found while shooting are for the reviewer who has already seen
the pictures and wants to argue with the approach. Keep them; keep them below.

Preserve any existing body sections worth keeping (test plan, scope notes); replace only
the comparison part. Close with a line saying where the images live and why that path
survives deploys, so nobody moves them.

**Before you post, reread the body against the current diff.** Copy quoted from the UI
("the band reads *…*") goes stale the moment a later commit changes the string, and a
leftover table row from an earlier draft reads as a bug. A body that quotes text the
preview no longer shows is the same failure as a stale screenshot.

Write to a file next to the screenshots, then:

```bash
gh pr edit "$PR" --body-file <file>
```

**Done-gate (mandatory before claiming finished).** The old Summary/Test-plan body still
showing on GitHub means the run failed, even if PNGs exist locally. After every `gh pr edit`:

```bash
gh pr view "$PR" --json body -q .body | grep -E 'pr-shots/|blob/pr-shots/' | head
```

Expect at least one hosted image URL per surface. Empty → re-edit; do not publish `done`.
For a stack of N PRs, every PR must pass this gate.

Re-running overwrites both the objects and the body, so this is idempotent.

## 6. Report

Name the surfaces captured, the URLs, which host each side came from (and if the "after"
was local, why the preview could not be used), and anything skipped and why. If a pair came out
identical, say so plainly — that is a finding about the change, not a failure of the
command. Quote the `gh pr view` grep that passed the done-gate for each PR.
