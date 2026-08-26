# /CROSSCHECK — a critique is a claim, not a verdict

Another model critiqued a plan of ours — via `/ask`, a Claude Code window, a pasted screenshot,
whatever. **Verify every claim against the real code before changing a single line of the plan.**
A second model is confidently wrong often enough that adopting its critique unverified is worse
than ignoring it: it launders a hallucinated file path into a plan the next session acts on.

The mirror-image `/CROSSCHECK` in Claude Code does the same job on critiques that came from you.

## Step 0 — Pin the clone

These repos are cloned many times over (`app-monorepo-1`..`-7`, `studio`/`studio-2`,
`claw-calendar`/`-2`/`-3`), each on its own branch. Verifying a claim against the wrong checkout
produces a confident REFUTED that is simply false. State the clone and branch in one line before
you check anything, and run every command from there.

## Step 1 — Find the critique, and the plan it attacks

The critique: a file the user pointed at, an image attached to the message (transcribe every
distinct claim, including ones inside code blocks and diffs), or text they pasted. If you cannot
find one, **stop and ask** — do not invent one.

The plan: match on the critique's subject matter — ticket number, file names, function names it
mentions. Look at what the user named, then recently-touched markdown, then `~/Desktop/*.md`
(drafts start there), then `~/Desktop/docs-hub/projects/*/docs/`.

State which plan file you settled on and why, in one line. If two are plausible, ask.

## Step 2 — Decompose into atomic claims

A numbered list, one row per **falsifiable** assertion. Split compound complaints apart — "this is
racy and also the store is keyed wrong" is two claims.

Discard what cannot be checked against the codebase: style preferences, "consider also…", vague
hedges. Note them in one line at the end as *unfalsifiable — ignored*.

## Step 3 — Verify each one against the actual code

This is the whole point of the command.

- **Open the real file and function it names.** If it names none, find the code yourself.
- **Check the thing it describes exists at all.** Other models hallucinate file paths, prop names,
  hook names and signatures constantly. A claim about `useSessionStore` is dead on arrival if that
  hook does not exist.
- **Run something.** Tests, a type check, `git log -S` for when a line arrived, `gh pr view` for
  prior review context. Evidence beats reasoning.
- **Check the plan actually says what the critique says it says.** A large fraction of cross-model
  critiques attack a misreading of the plan.

One verdict per claim:

| Verdict | Meaning |
| --- | --- |
| **CONFIRMED** | Verified true against the code. The plan is wrong or incomplete here. |
| **REFUTED** | Verified false. Name the specific evidence that kills it. |
| **MISREAD** | True of some other code, or of a plan that isn't this one. |
| **UNVERIFIABLE** | Cannot be settled from the codebase — a product or design call. Say whose. |

Never write a verdict you did not verify. "Probably fine" is not a verdict — go look.

## Step 4 — Report before touching the plan

```
## Cross-check verdict

| # | Claim (one line) | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | ... | REFUTED | `shotlist-store.ts:88` keys by projectId — the critique's `bySession` map does not exist |
```

Evidence is `file.ts:line`, real command output, or a commit SHA. Not prose.

Then: **where we disagree** (one short paragraph per REFUTED/MISREAD — state plainly what the other
model got wrong and what is actually true; do not soften it into "both perspectives have merit"),
**where it is right** (what each CONFIRMED claim changes in the plan), and **open questions**
(UNVERIFIABLE claims, phrased as a question to the user).

## Step 5 — Update the plan, for CONFIRMED claims only

Edit the plan markdown in place, surgically — fix the wrong step, add the missing one, correct the
wrong path. Preserve its structure and voice. Append a dated entry under `## Cross-check revisions`
at the bottom, one line per adopted claim.

Do **not** silently drop or reword anything the critique got wrong; the plan keeps its original
position there. If **zero** claims were confirmed, do not touch the file — say so plainly: the plan
stands, and here is why each objection failed.

Findings go in the plan, not the code. Do not commit or push unless asked.

## Style

- Verify before you agree. Deference to another model is not rigor.
- Verify before you disagree too — an unchecked refutation is the same failure in the other direction.
- No "great catch", no "you're absolutely right", no apologising for the original plan.
