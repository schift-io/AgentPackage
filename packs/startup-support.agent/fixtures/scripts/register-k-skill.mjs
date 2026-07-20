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

function parseSkillMarkdown(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!match) throw new Error("SKILL.md must contain frontmatter.");

  const frontmatter = {};
  let currentListKey = null;
  for (const rawLine of match[1].split(/\r?\n/)) {
    const line = rawLine.trimEnd();
    if (!line.trim()) continue;
    const listItem = line.match(/^\s*-\s+(.+)$/);
    if (listItem && currentListKey) {
      frontmatter[currentListKey].push(listItem[1].trim());
      continue;
    }
    const kv = line.match(/^([a-zA-Z0-9_-]+):\s*(.*)$/);
    if (!kv) continue;
    const [, key, value] = kv;
    if (value === "") {
      frontmatter[key] = [];
      currentListKey = key;
    } else {
      frontmatter[key] = value;
      currentListKey = null;
    }
  }

  if (!frontmatter.name || !frontmatter.description) {
    throw new Error("SKILL.md frontmatter requires name and description.");
  }

  return {
    name: String(frontmatter.name),
    description: String(frontmatter.description),
    instructions: match[2].trim(),
    frontmatter,
  };
}

async function api(pathname, init = {}) {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${apiKey}`);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${apiUrl}${pathname}`, { ...init, headers });
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(`Schift API ${response.status} ${pathname}: ${text.slice(0, 500)}`);
  }
  return body;
}

function readBundleFile(relPath) {
  return {
    path: relPath,
    content: fs.readFileSync(path.join(root, relPath), "utf-8"),
  };
}

const args = parseArgs(process.argv.slice(2));
const dryRun = args["dry-run"] === "true";
const apiKey = args["api-key"] ?? process.env.SCHIFT_API_KEY;
const apiUrl = (args["api-url"] ?? process.env.SCHIFT_API_URL ?? "https://api.schift.io").replace(/\/+$/, "");
let bucketId = args["bucket-id"] ?? process.env.SCHIFT_BUCKET_ID;
const createBucket = args["create-bucket"] === "true";

const descriptor = JSON.parse(fs.readFileSync(path.join(root, "k-skill.json"), "utf-8"));
const skillMd = fs.readFileSync(path.join(root, descriptor.skill_file), "utf-8");
const skill = parseSkillMarkdown(skillMd);
const files = [
  readBundleFile("k-skill.json"),
  readBundleFile("sources.json"),
  readBundleFile("source_urls.txt"),
  readBundleFile("questions.json"),
  readBundleFile("scripts/fetch-sources.mjs"),
  readBundleFile("scripts/upload-folder.mjs"),
];

const payloadBase = {
  name: skill.name,
  description: skill.description,
  instructions: skill.instructions,
  frontmatter: {
    ...skill.frontmatter,
    source_registry: descriptor.source_registry,
    fetch_script: descriptor.fetch_script,
    upload_script: descriptor.upload_script,
  },
  files,
};

if (dryRun) {
  console.log(JSON.stringify({ ...payloadBase, bucket_ids: bucketId ? [bucketId] : [] }, null, 2));
  process.exit(0);
}

if (!apiKey) throw new Error("SCHIFT_API_KEY or --api-key is required.");

if (!bucketId && createBucket) {
  const bucket = await api("/v1/buckets", {
    method: "POST",
    body: JSON.stringify({
      name: descriptor.bucket_name,
      description: "Korean startup-support RAG demo bucket created from k-skill source pack.",
      metadata: {
        fixture: "startup-support",
        k_skill: descriptor.name,
        source_registry: descriptor.source_registry,
      },
    }),
  });
  bucketId = bucket.id;
}

if (!bucketId) {
  throw new Error("SCHIFT_BUCKET_ID/--bucket-id is required unless --create-bucket is set.");
}

const payload = { ...payloadBase, bucket_ids: [bucketId] };
const existing = await api("/v1/skills");
const previous = existing.find((item) => item.name === skill.name);
const result = previous
  ? await api(`/v1/skills/${previous.id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  : await api("/v1/skills", {
      method: "POST",
      body: JSON.stringify(payload),
    });

console.log(JSON.stringify({
  skill_id: result.id,
  skill_name: result.name,
  bucket_id: bucketId,
  invoke_path: `/v1/skills/${result.id}/invoke`,
  source_registry_path: `/v1/skills/${result.id}/files/sources.json`,
}, null, 2));

