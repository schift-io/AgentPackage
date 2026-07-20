import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const allowedExts = new Set([".html", ".txt", ".md", ".pdf", ".hwpx"]);

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

function listFiles(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...listFiles(fullPath));
      continue;
    }
    if (allowedExts.has(path.extname(entry.name).toLowerCase())) {
      files.push(fullPath);
    }
  }
  return files;
}

function xmlToText(xml) {
  return xml
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

function extractHwpxText(file) {
  const list = spawnSync("unzip", ["-Z1", file], { encoding: "utf-8" });
  if (list.status !== 0) {
    throw new Error(`Cannot inspect HWPX file with unzip: ${file}`);
  }

  const xmlPaths = list.stdout
    .split(/\r?\n/)
    .filter((item) => item.endsWith(".xml"))
    .filter((item) => item.startsWith("Contents/") || item.startsWith("Preview/"));

  if (xmlPaths.length === 0) {
    throw new Error(`No XML entries found in HWPX file: ${file}`);
  }

  const chunks = [];
  for (const xmlPath of xmlPaths) {
    const extracted = spawnSync("unzip", ["-p", file, xmlPath], {
      encoding: "utf-8",
      maxBuffer: 20 * 1024 * 1024,
    });
    if (extracted.status !== 0 || !extracted.stdout.trim()) continue;
    const text = xmlToText(extracted.stdout);
    if (text) chunks.push(`## ${xmlPath}\n\n${text}`);
  }

  if (chunks.length === 0) {
    throw new Error(`No text extracted from HWPX file: ${file}`);
  }

  return [
    `Source file: ${path.basename(file)}`,
    "Source type: hwpx",
    `Extracted at: ${new Date().toISOString()}`,
    "",
    chunks.join("\n\n"),
    "",
  ].join("\n");
}

function fileForUpload(file) {
  const ext = path.extname(file).toLowerCase();
  if (ext !== ".hwpx") {
    return {
      filename: path.basename(file),
      blob: new Blob([fs.readFileSync(file)]),
    };
  }

  const text = extractHwpxText(file);
  return {
    filename: `${path.basename(file, ext)}.hwpx.txt`,
    blob: new Blob([text], { type: "text/plain" }),
  };
}

const args = parseArgs(process.argv.slice(2));
const apiKey = args["api-key"] ?? process.env.SCHIFT_API_KEY;
const bucketId = args["bucket-id"] ?? process.env.SCHIFT_BUCKET_ID;
const apiUrl = (args["api-url"] ?? process.env.SCHIFT_API_URL ?? "https://api.schift.io").replace(/\/+$/, "");
const dir = path.resolve(root, args.dir ?? "raw");
const dryRun = args["dry-run"] === "true";

if (!apiKey && !dryRun) throw new Error("SCHIFT_API_KEY or --api-key is required.");
if (!bucketId && !dryRun) throw new Error("SCHIFT_BUCKET_ID or --bucket-id is required.");
if (!fs.existsSync(dir)) throw new Error(`Directory not found: ${dir}`);

const files = listFiles(dir);
if (dryRun) {
  for (const file of files) console.log(path.relative(root, file));
  process.exit(0);
}

console.log(`Uploading ${files.length} files from ${dir} to bucket ${bucketId}`);

let ok = 0;
let failed = 0;

for (const file of files) {
  const upload = fileForUpload(file);
  const form = new FormData();
  form.append("files", upload.blob, upload.filename);

  const response = await fetch(`${apiUrl}/v1/buckets/${bucketId}/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}` },
    body: form,
  });

  if (response.ok) {
    ok += 1;
  } else {
    failed += 1;
    const body = await response.text().catch(() => "");
    console.warn(`${file}: ${response.status} ${body.slice(0, 240)}`);
  }
}

console.log(`Done. ok=${ok} failed=${failed}`);
if (failed > 0) process.exitCode = 1;
