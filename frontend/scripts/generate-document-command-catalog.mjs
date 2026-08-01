import { readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const components = path.join(root, "features", "compilation", "components");
const output = path.join(components, "document-command-catalog.generated.json");
const current = JSON.parse(await readFile(output, "utf8"));
const implementationById = new Map(
  current.map((command) => [command.id, command.implementation]),
);

function stringField(source, name) {
  return source.match(new RegExp(`readonly ${name} = "([^"]+)"`))?.[1] ?? "";
}

const files = (await readdir(components))
  .filter((name) => /^DocLib.+\.ts$/.test(name))
  .sort((left, right) => left.localeCompare(right));
const commands = [];
for (const file of files) {
  const source = await readFile(path.join(components, file), "utf8");
  const id = stringField(source, "id");
  const mode = stringField(source, "mode");
  const category = source.match(/readonly category = "([^"]+)"/)?.[1] ?? "format";
  const selection = source.match(/readonly requiresSelection = (true|false)/)?.[1] === "true";
  if (!id || !mode || !source.includes("async execute(")) continue;
  const rawTitle = stringField(source, "title").replace(/^DocLib\s+/, "");
  commands.push({
    id,
    title: rawTitle || mode,
    category,
    mode,
    requiresSelection: selection,
    implementation: implementationById.get(id) ?? "bridge",
  });
}
await writeFile(output, `${JSON.stringify(commands)}\n`, "utf8");
process.stdout.write(`document_command_catalog_generated commands=${commands.length}\n`);
