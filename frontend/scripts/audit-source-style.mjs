import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const sourceRoots = ["app", "features", "shared"];
const extensions = new Set([".js", ".jsx", ".mjs"]);
const forbiddenPatterns = [
  ["transpiled_object_assign", /Object\.assign\s*\(/],
  ["transpiled_optional_chain", /===\s*void 0|!==\s*void 0/],
  ["transpiled_rest_helper", /\b__rest\b/],
  ["transpiled_temporary", /\bvar\s+_[a-z]/i],
  ["source_comment", /(^|\n)\s*\/[/\*]/],
  ["textual_ellipsis", new RegExp("\\u2026")],
  ["emoji", /\p{Extended_Pictographic}/u],
  [
    "promotional_tagline",
    /giải pháp toàn diện|tất cả trong một|nâng tầm trải nghiệm|đồng hành cùng bạn|bứt phá giới hạn|mạnh mẽ và linh hoạt|thông minh hơn mỗi ngày/i,
  ],
];

async function sourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await sourceFiles(target)));
    else if (extensions.has(path.extname(entry.name))) files.push(target);
  }
  return files;
}

const files = (
  await Promise.all(sourceRoots.map((directory) => sourceFiles(path.join(root, directory))))
).flat();
const violations = [];

for (const file of files) {
  const relative = path.relative(root, file);
  const source = await readFile(file, "utf8");
  for (const [code, pattern] of forbiddenPatterns) {
    if (pattern.test(source)) violations.push(`${relative}:${code}`);
  }
  if (relative.startsWith("app/") && relative.endsWith("/page.jsx")) {
    const lines = source.split("\n").length;
    if (lines > 20) violations.push(`${relative}:route_contains_feature_logic:${lines}`);
  }
  const serviceOwned =
    relative.includes("/services/") || relative === "shared/services/api-client.js";
  if (!serviceOwned && /\bfetch\s*\(/.test(source)) {
    violations.push(`${relative}:network_call_outside_service`);
  }
}

if (violations.length) {
  process.stderr.write(`${violations.join("\n")}\n`);
  process.exit(1);
}

process.stdout.write(`source_style_audit_passed files=${files.length}\n`);
