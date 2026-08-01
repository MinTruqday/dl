import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const components = path.join(root, "features", "compilation", "components");
const catalog = JSON.parse(
  await readFile(path.join(components, "document-command-catalog.generated.json"), "utf8"),
);
const issues = [];
const ids = new Set();
for (const command of catalog) {
  if (!command.id || ids.has(command.id)) {
    issues.push(`duplicate_or_empty_id:${command.id ?? ""}`);
    continue;
  }
  ids.add(command.id);
  let source = "";
  try {
    source = await readFile(path.join(components, `${command.id}.ts`), "utf8");
  } catch {
    issues.push(`missing_file:${command.id}`);
    continue;
  }
  for (const token of [
    `export default class ${command.id}`,
    `readonly id = "${command.id}"`,
    `readonly mode = "${command.mode}"`,
    "async execute(",
  ]) {
    if (!source.includes(token)) issues.push(`invalid_component:${command.id}:${token}`);
  }
  if (command.implementation === "bridge" && !source.includes("new CustomEvent(")) {
    issues.push(`missing_bridge_event:${command.id}`);
  }
  if (command.implementation === "bridge" && !source.includes("cancelable: true")) {
    issues.push(`uncancellable_bridge:${command.id}`);
  }
}
if (issues.length) {
  process.stderr.write(`${issues.join("\n")}\n`);
  process.exit(1);
}
process.stdout.write(`document_component_runtime_audit_passed commands=${catalog.length}\n`);
