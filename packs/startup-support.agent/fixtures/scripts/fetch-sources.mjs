import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const value = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : "true";
    out[key] = value;
  }
  return out;
}

function htmlToText(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, "\n")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .split(/\r?\n/)
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join("\n");
}

const args = parseArgs(process.argv.slice(2));
const dryRun = args["dry-run"] === "true";
const sources = JSON.parse(fs.readFileSync(path.join(root, "sources.json"), "utf-8"));
const rawDir = path.join(root, "raw");
const textDir = path.join(root, "text");

if (dryRun) {
  for (const source of sources) {
    console.log(`${source.id}\t${source.url}`);
  }
  process.exit(0);
}

fs.mkdirSync(rawDir, { recursive: true });
fs.mkdirSync(textDir, { recursive: true });

for (const source of sources) {
  const response = await fetch(source.url, {
    headers: {
      "User-Agent": "Schift RAG source fetcher (+https://schift.io)",
    },
  });

  if (!response.ok) {
    console.warn(`${source.id}: ${response.status} ${response.statusText}`);
    continue;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const ext = contentType.includes("html") ? "html" : "bin";
  const rawPath = path.join(rawDir, `${source.id}.${ext}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  fs.writeFileSync(rawPath, bytes);

  if (ext === "html") {
    const text = htmlToText(bytes.toString("utf-8"));
    const header = [
      `Source ID: ${source.id}`,
      `Title: ${source.title}`,
      `Source URL: ${source.url}`,
      `Fetched at: ${new Date().toISOString()}`,
      "",
    ].join("\n");
    fs.writeFileSync(path.join(textDir, `${source.id}.txt`), `${header}${text}\n`);
  }

  console.log(`${source.id}: saved ${rawPath}`);
}

