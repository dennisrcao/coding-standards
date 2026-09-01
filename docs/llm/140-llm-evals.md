```yaml
description: Proving a pipeline change is an improvement — invariants and labeled gold sets, a structurally diverse corpus, deterministic scorers before judges, no change-detector tests, declaration files not source text, an offline CI gate and scheduled live evals
globs:
  - "**/eval/**/*.py"
  - "**/evals/**/*.py"
  - "**/*scorer*.{py,ts}"
  - "**/.github/workflows/*eval*.{yml,yaml}"
  - "**/test_*llm*.py"
  - "**/*.test.{ts,py}"
alwaysApply: false
```

# Evaluating an LLM pipeline

One question: **are we sure this change produces a better result?** — answered with a number rather
than a vibe. Without one, every prompt edit is a coin flip that looked good on the input you had
open.

| This file is… | Precedence |
|---|---|
| **derived from** eval harness shapes and two test antipatterns seen in production | those patterns win |
| **deliberately narrower** — the knob drift test, scheduled live evals | states its reason below |
| **downstream** — some pipelines ban hardcoded expected outputs outright; that is right for generation stages and wrong as a general law | this file wins, and says why |

## Do

- **Assert invariants for properties that must hold on every input.**
- **Use labeled gold sets for tasks that have a correct answer.**
- **Build a corpus that varies every axis your demo case fixes.**
- **Score deterministically first.** Reach for a judge only for what a pure function cannot check.
- **Gate the PR on the offline half**, path-filtered to the pipeline.
- **Assert against declaration files** — configs, templates, prompt fragments.

## Don't

- **Don't write change-detector tests.** If it reads like a snapshot of current data, delete it.
- **Don't read source code text in a test** as a proxy for behavior.
- **Don't let a judge gate a hard invariant.**
- **Don't refit the corpus to the case you have open.**
- **Don't leave live evals purely manual by default.** See below — this one is a spend decision, and
  it has to be made explicitly rather than inherited.

## Two eval types, not one law

They answer different questions and both are needed:

| | **Invariants** | **Labeled gold** |
|---|---|---|
| Question | does this property hold for *every* input? | did we get the *right* answer? |
| Examples | durations sum to the input; frame numbers contiguous; every id resolves; no banned vocabulary | this utterance is `calendar_add`; this field extracts to `"Tom Brady"`; this fact survives compaction |
| Expected output | none — the property *is* the assertion | yes, and hardcoding it is the point |
| Fails when | the pipeline breaks a contract | the pipeline gets it wrong |

Some generation pipelines assert only invariants: *"No expected outputs are hard-coded (that would
refit the judge to one run)."* **That is correct for generation**, where "the right output" is
not a single string — and wrong as a general law. A compaction eval scores **recall against gold
answers**, because "did this fact survive compaction" has a right answer.

Applied blanket, "no hardcoded expected outputs" bans classifier and extraction evals entirely and
leaves *"the JSON parsed"* as a passing score — which is exactly the class of failure this band
exists to prevent.

**Grade findings by severity, not pass/fail.** The reference harness types each as
`invariant | rule | heuristic`, so a broken contract and a stylistic miss are not the same event and
only the first can gate.

## The corpus varies what the demo fixes

The demo input fixes a dozen variables by accident: its length, its entity count, whether it has
explicit structure, whether it is sparse or dense. **A corpus that is the demo tests none of them.**

Build it to vary every one of those axes deliberately — and make it *not* the demo case. A change
that helps one shape and regresses another is exactly what this catches, and nothing else will.

**"Don't fit the example" is an eval rule, not a prompting rule.** Few-shot examples inside a prompt
are fine and mainstream — a classifier prompt may carry several, and they are why it works. What is
banned is *prose true only of your test case* ("there are three characters," the demo's genre baked
into an instruction) and *a corpus that is the demo*. Do not let this rule strip worked examples
out of prompts.

## Deterministic first, judges for what pure functions cannot check

**The rules are not invented — they are the prose contracts already in your prompts, made
executable.** "No color words," "durations must sum," "frame numbers are 1-based" are written in the
signatures; a scorer turns each into a function. Same rule, two consumers.

Deterministic scorers are reproducible, free, and unit-testable. They run in CI with no API key.
Start there and cover everything they can reach.

**A judge is for what a pure function genuinely cannot check** — semantic adherence, "did this
survive compaction," "does this image match the scene." When you need one:

- **Measure the thing that matters, not a proxy.** A compaction eval scores *recall* — it generates
  factual questions from the region compaction will summarize away, then asks a fresh model those
  questions against only the post-compaction context and grades against gold. Not "tokens retained."
  Tokens retained is the cost; recall is the thing you were buying.
- **A judge never gates a hard invariant.** It is noisy; invariants are not.

## Two antipatterns, and the line between them

**Change-detector tests** fail whenever data that is *expected to change* gets updated — model
catalogs, config version literals, enumeration counts. They add no behavioral coverage and guarantee
that routine updates break CI:

```python
# Don't — breaks on every model release / schema bump / new provider
assert "gemini-2.5-pro" in _PROVIDER_MODELS["gemini"]
assert DEFAULT_CONFIG["_config_version"] == 21
assert len(_PROVIDER_MODELS["huggingface"]) == 8

# Do — assert how two pieces of data must RELATE
assert "gemini" in _PROVIDER_MODELS and len(_PROVIDER_MODELS["gemini"]) >= 1
assert raw["_config_version"] == DEFAULT_CONFIG["_config_version"]
for m in _PROVIDER_MODELS["huggingface"]:
    assert m.lower() in DEFAULT_CONTEXT_LENGTHS_LOWER   # every model has a context length
```

**Source text as a proxy for behavior** — a test that regex-matches a `.py`/`.ts` file to prove a
call site exists. It passes when the wiring is subtly broken, fails when a correct refactor renames
a variable, and has never once executed the path it claims to guard.

**The line is the proxy, not the file read.** Asserting about a **declaration** — a config, a
template, a manifest, a prompt fragment — is asserting about a *file*, which is what that file *is*.
The allowed pattern: text assertions over **discovered** `template.yaml` files, with the reason stated
(some YAML loaders break on short tags) and a floor-not-exact-count assertion so discovery breaking
cannot leave every parametrized test vacuously passing.

A flat "never read files in tests" would forbid the prompt-fragment drift test that
[`120`](120-prompt-and-context-budget.md)'s composition rule depends on. Keep the proxy ban; keep
declaration assertions.

## The knob drift test

[`100`](100-llm-call-pathway.md) requires one source of truth per knob — model id, timeout, budget.
**The test that enforces it lives here**, because it is a test, and because this is the file that
says a test nothing runs is not coverage.

Assert the code constant and any config schema `default` agree, and assert the *relationships*
(`preflight_budget > measured_cold_p99`, `per_message_timeout < platform_ceiling`) rather than
freezing the numbers — a raw-value assertion is a change-detector. Production has seen this twice: a
model default that 404'd, and a timeout that was 5 s in the schema and 15 s in code.

## Where it runs

**The offline half gates the PR.** Path-filter to the pipeline package, run lint plus pure-function
tests, require no API key and spend nothing. `agents-eval.yml` is the reference:

```yaml
on:
  pull_request:
    paths: ["packages/agents/**", ".github/workflows/agents-eval.yml"]
# ruff check + ruff format --check, then pytest over scorers/validators.
# All offline; no ANTHROPIC_API_KEY required.
```

**Live evals run on a schedule when the calls are cheap.** "Live A/B stays manual" is a defensible
*spend* decision for an image pipeline and a bad default for a text classifier that costs cents. Make
the call explicitly per pipeline and write down which you chose — because the failure it prevents is
precisely the one that seeded this band: a provider quietly moves a model alias and nobody notices
for weeks.

**A test that no workflow runs is not coverage.** Verify the path filters still match after any
move — a refactor that relocates code silently relocates it out of CI's reach, and nothing goes red
to tell you. **Land the workflow change in the same commit as the move**, not after it: a branch that
relocates packages while the workflow still triggers on the old paths can report green while the
eval suite runs nowhere.

## Canonical shape

One deterministic scorer, from `eval/scorers.py`:

```python
@dataclass(frozen=True)
class Finding:
    rule: str
    stage: str                    # which pipeline stage produced the output
    severity: str                 # "invariant" | "rule" | "heuristic" — only the first gates
    ok: bool
    detail: str
    frame_number: int | None = None


def score_durations_sum(frames: list[Frame], inp: Input) -> list[Finding]:
    """sum(frame.duration_seconds) must equal input.duration_seconds.
    An INVARIANT: it holds for every input, so no expected output is needed."""
    total = sum(f.duration_seconds for f in frames)
    return [Finding(
        "durations_sum_to_input", "frames", "invariant",
        ok=abs(total - inp.duration_seconds) <= 0.5,       # stated tolerance
        detail=f"sum={total:.2f} vs input={inp.duration_seconds}",
    )]
```

Pure, typed, offline, and named after the contract it enforces — so a failure reads as *which rule
broke*, not "assertion failed." The scorers are unit-tested themselves, which is what stops a broken
scorer from silently passing every run.
