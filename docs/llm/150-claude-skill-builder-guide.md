# Skill builder guide (notes)

**Reference only — not adoptable.** The `150` band holds guides, not rules. Do not copy this to
`.cursor/rules/`; point an agent at it when it is writing a skill.

These are my working notes on writing Claude skills. The source is Anthropic's
[*The Complete Guide to Building Skills for Claude*](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf?hsLang=en)
together with the [Agent Skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
and [best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).
Read those for the full treatment; this page is the part I check every time.

## Shape

```
kebab-case-name/
├── SKILL.md        # required, exactly this filename
├── scripts/        # optional — deterministic work the model should run, not reimplement
├── references/     # optional — long docs, loaded only when SKILL.md points at them
└── assets/         # optional — templates and files used in the output
```

No `README.md` inside the skill folder; humans get a README at the repo level.

## Loading is three levels, so write for each

1. **Frontmatter** — always in the system prompt, for every installed skill. It decides whether
   the skill loads at all.
2. **`SKILL.md` body** — loaded when the skill looks relevant. The working instructions.
3. **Linked files** — read only when the body sends the agent there.

Push detail down a level whenever it is not needed on every run. A long `SKILL.md` costs context
on every invocation and degrades the instructions around it.

## Frontmatter

```yaml
---
name: invoice-reconcile          # kebab-case, matches the folder
description: Reconciles exported bank CSVs against open invoices. Use when the user uploads a
  bank statement CSV, asks to "match payments", or mentions unpaid invoices.
---
```

- **`description` carries both what and when** — the task, then the phrases and file types that
  should trigger it. Vague descriptions ("helps with projects") never fire; broad ones fire on
  everything.
- No `<` or `>` in frontmatter (it lands in the system prompt), and `claude` / `anthropic` are
  reserved in names.
- Optional: `license`, `compatibility` (environment needs), `metadata` (author, version, …).

## Writing the body

- Numbered steps for workflows; say what "done" looks like for each step.
- Put a check that must be right into a script. Code is deterministic; prose instructions are not.
- Name the failure modes you have seen and what to do about them, not generic best practice.
- Assume other skills are loaded too. Don't write as if this is the only capability present.

## Testing

- **Triggering:** a short list of requests that should load it (including paraphrases) and some
  that should not. When it misfires, ask the agent when it would use the skill — it quotes the
  description back, and the gap is usually obvious.
- **Function:** run the real task end to end and check the output, not just that it ran.
- **Baseline:** compare against the same task without the skill — turns, failed calls, tokens.
  A skill that doesn't beat the baseline isn't earning its context.
- Iterate on one hard task until it succeeds, then generalize. Broad test sets come after.
