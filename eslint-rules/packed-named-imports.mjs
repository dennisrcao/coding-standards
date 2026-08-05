/**
 * Disallow Prettier-style named imports where every specifier sits on its own
 * line. Wrapped imports use the brace-newline form — `{` ends the `import`
 * line, names follow packed on 2-space-indented lines, `} from "…";` closes on
 * its own line — per `docs/030-lint-format-quality.md`.
 *
 * CANONICAL. This file is the source of truth; consuming repos copy it into
 * their own `eslint-rules/`. Edit it here, then re-copy downstream.
 *
 * @type {import('eslint').Rule.RuleModule}
 */
export const packedNamedImportsRule = {
  meta: {
    type: "layout",
    docs: {
      description:
        "Require packed named imports — multiple specifiers per line when wrapped",
    },
    messages: {
      onePerLine:
        "Pack named imports on fewer lines — do not put one import name per line (see 030-lint-format-quality).",
    },
    fixable: "code",
    schema: [
      {
        type: "object",
        properties: {
          minSpecifiers: { type: "number", minimum: 2 },
          maxLineLength: { type: "number", minimum: 40 },
        },
        additionalProperties: false,
      },
    ],
  },
  create(context) {
    const minSpecifiers = context.options[0]?.minSpecifiers ?? 2;
    const maxLineLength = context.options[0]?.maxLineLength ?? 150;

    return {
      ImportDeclaration(node) {
        const named = node.specifiers.filter(
          (s) => s.type === "ImportSpecifier",
        );
        if (named.length < minSpecifiers) return;

        if (node.loc.start.line === node.loc.end.line) return;

        const byLine = new Map();
        for (const spec of named) {
          const line = spec.loc.start.line;
          const row = byLine.get(line);
          if (row) row.push(spec);
          else byLine.set(line, [spec]);
        }

        // Any line carrying two or more names is already packed — that covers
        // both the brace-newline house form and the hanging form, so neither
        // is reported and hand-authored grouping is never destroyed.
        if (byLine.size < named.length) return;

        context.report({
          node,
          messageId: "onePerLine",
          fix(fixer) {
            const sourceCode = context.sourceCode;
            const specs = named.map((s) => sourceCode.getText(s).trim());
            const moduleSource = sourceCode.getText(node.source);
            const kind = node.importKind === "type" ? "type " : "";
            const packed = formatPackedImport(
              specs,
              moduleSource,
              kind,
              maxLineLength,
            );
            return fixer.replaceText(node, packed);
          },
        });
      },
    };
  },
};

/**
 * Collapse to one line when it fits; otherwise emit the brace-newline form:
 *
 *   import {
 *     Alpha, Bravo, Charlie,
 *     Delta,
 *   } from "mod";
 *
 * Every wrapped line is 2-space indent + names + a trailing comma, measured
 * against one flat budget — the opening `import {` and closing `} from "…";`
 * each stand alone, so no line has to reserve room for them. A single specifier
 * wider than the budget simply overflows; an identifier cannot be split.
 *
 * The packing is greedy, so it does not preserve any grouping the author had.
 * That is safe: the rule only fires on one-name-per-line imports, which carry
 * no grouping to lose.
 *
 * @param {string[]} specs
 * @param {string} moduleSource
 * @param {string} kind
 * @param {number} maxLineLength
 */
function formatPackedImport(specs, moduleSource, kind, maxLineLength) {
  const single = `import ${kind}{ ${specs.join(", ")} } from ${moduleSource};`;
  if (single.length <= maxLineLength) return single;

  const lines = [];
  let current = "";

  for (const spec of specs) {
    const candidate = current ? `${current} ${spec},` : `  ${spec},`;
    if (current && candidate.length > maxLineLength) {
      lines.push(current);
      current = `  ${spec},`;
    } else {
      current = candidate;
    }
  }
  lines.push(current);

  return `import ${kind}{\n${lines.join("\n")}\n} from ${moduleSource};`;
}
