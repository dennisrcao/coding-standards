/**
 * Fixtures for the canonical `packed-named-imports` rule.
 *
 * There is no test runner in this docs repo, and no node_modules — so `eslint`
 * and `@typescript-eslint/parser` are resolved from the CURRENT WORKING
 * DIRECTORY. Run it from any repo that has both installed:
 *
 *   cd ~/Desktop/studio
 *   node ~/coding-standards/eslint-rules/packed-named-imports.test.mjs
 *
 * Exits non-zero on failure.
 */
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(`${process.cwd()}/`);
const load = async (spec) => {
  try {
    return await import(pathToFileURL(require.resolve(spec)).href);
  } catch {
    console.error(`Cannot resolve "${spec}" from ${process.cwd()}.`);
    console.error("Run this from a repo with eslint + @typescript-eslint/parser installed.");
    process.exit(2);
  }
};

const { Linter } = await load("eslint");
const tsParser = (await load("@typescript-eslint/parser")).default;
const { packedNamedImportsRule } = await import("./packed-named-imports.mjs");

const linter = new Linter();
const config = {
  languageOptions: { ecmaVersion: "latest", sourceType: "module", parser: tsParser },
  plugins: { local: { rules: { "packed-named-imports": packedNamedImportsRule } } },
  rules: { "local/packed-named-imports": ["error", { maxLineLength: 60 }] },
};

let pass = 0;
let fail = 0;

/** @param {{ reports: number, expected?: string }} want */
function check(name, code, want) {
  const msgs = linter.verify(code, config);
  const fatal = msgs.filter((m) => m.fatal);
  if (fatal.length) {
    console.log(`FAIL  ${name}  -> PARSE ERROR: ${fatal[0].message}`);
    fail++;
    return;
  }
  const out = linter.verifyAndFix(code, config).output;
  let ok = msgs.length === want.reports;
  if (ok && want.expected !== undefined) ok = out.trim() === want.expected.trim();
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}   (reports ${msgs.length}, want ${want.reports})`);
  if (ok) pass++;
  else {
    fail++;
    console.log(`--- got ---\n${out}\n--- want ---\n${want.expected ?? "(unchanged)"}`);
  }
}

check(
  "one-per-line -> brace-newline, wrapping at the budget",
  `import {
  Aperture,
  Archive,
  Boxes,
  FileTextIcon,
  FolderIcon,
  Home,
  LayoutGrid,
  Settings,
  Clapperboard,
} from "lucide-react";`,
  {
    reports: 1,
    expected: `import {
  Aperture, Archive, Boxes, FileTextIcon, FolderIcon, Home,
  LayoutGrid, Settings, Clapperboard,
} from "lucide-react";`,
  },
);

check(
  "one-per-line -> collapses to a single line when it fits",
  `import {
  useMemo,
  useRef,
} from "react";`,
  { reports: 1, expected: `import { useMemo, useRef } from "react";` },
);

// The house form. Must never be reported, or adoption mass-reformats a repo.
check(
  "brace-newline packed passes untouched",
  `import {
  PAGE, STYLE, mm, COL_CX, COL_W,
  KNOB_ROW_CY, KNOB, FADER_CX,
} from "./geometry.ts";`,
  { reports: 0 },
);

check(
  "hanging form passes untouched",
  `import { Aperture, Archive, Boxes,
  FileTextIcon } from "lucide-react";`,
  { reports: 0 },
);

check(
  "type-only import keeps its `type` keyword",
  `import type {
  AlphaLongName,
  BravoLongName,
  CharlieLongName,
  DeltaLongName,
} from "./t.ts";`,
  {
    reports: 1,
    expected: `import type {
  AlphaLongName, BravoLongName, CharlieLongName,
  DeltaLongName,
} from "./t.ts";`,
  },
);

check(
  "inline `type` specifier survives the fix",
  `import {
  type Unit,
  deriveMidi,
} from "./m.ts";`,
  { reports: 1, expected: `import { type Unit, deriveMidi } from "./m.ts";` },
);

const wrapped = linter.verifyAndFix(
  `import {
  Aperture,
  Archive,
  Boxes,
  FileTextIcon,
  FolderIcon,
  Home,
  LayoutGrid,
  Settings,
  Clapperboard,
} from "lucide-react";`,
  config,
).output;

const over = wrapped.split("\n").filter((l) => l.length > 60);
console.log(`${over.length === 0 ? "PASS" : "FAIL"}  no emitted line exceeds the budget`);
if (over.length === 0) pass++;
else {
  fail++;
  console.log(over);
}

const trailing = /Clapperboard,\n\} from/.test(wrapped);
console.log(`${trailing ? "PASS" : "FAIL"}  trailing comma on the final wrapped line`);
trailing ? pass++ : fail++;

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
