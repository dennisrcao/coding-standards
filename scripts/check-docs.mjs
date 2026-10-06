#!/usr/bin/env node
// Checks every standard opens with the fenced yaml frontmatter its .mdc copy needs,
// and that every relative markdown link in the repo points at a file that exists.
import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const FRONTMATTER_KEYS = ["description", "globs", "alwaysApply"];
// Guides, surveys and indexes are read in place, never copied into a repo as an .mdc.
const NOT_A_STANDARD = [/^docs\/README\.md$/, /^docs\/research\//, /^docs\/archive\//, /^docs\/llm\/1[5-9]\d-/];

const walk = (dir) =>
  readdirSync(dir).flatMap((name) => {
    if (name === ".git" || name === "node_modules") return [];
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });

const errors = [];
const markdown = walk(ROOT).filter((p) => p.endsWith(".md"));

for (const file of markdown) {
  const rel = relative(ROOT, file);
  const text = readFileSync(file, "utf8");

  if (rel.startsWith("docs/") && !NOT_A_STANDARD.some((re) => re.test(rel))) {
    const block = text.match(/^```yaml\n([\s\S]*?)\n```/);
    if (!block) errors.push(`${rel}: must open with a fenced \`\`\`yaml frontmatter block`);
    else
      for (const key of FRONTMATTER_KEYS)
        if (!new RegExp(`^${key}:`, "m").test(block[1])) errors.push(`${rel}: frontmatter is missing \`${key}\``);
  }

  // Code spans and fences hold example links for other repos; only prose links must resolve.
  let fence = null;
  const prose = text
    .split("\n")
    .filter((line) => {
      const marker = line.match(/^\s*(`{3,}|~{3,})/)?.[1];
      if (marker && (!fence || marker.startsWith(fence))) {
        fence = fence ? null : marker;
        return false;
      }
      return !fence;
    })
    .join("\n")
    .replace(/`[^`\n]*`/g, "");
  for (const [, target] of prose.matchAll(/\]\(([^)\s]+)\)/g)) {
    if (/^(https?:|mailto:|#)/.test(target)) continue;
    const path = decodeURIComponent(target.split("#")[0]);
    if (path && !existsSync(resolve(dirname(file), path))) errors.push(`${rel}: broken link → ${target}`);
  }
}

if (errors.length) {
  console.error(errors.join("\n"));
  console.error(`\n${errors.length} problem(s) in ${markdown.length} markdown files`);
  process.exit(1);
}
console.log(`ok — ${markdown.length} markdown files, frontmatter and relative links intact`);
