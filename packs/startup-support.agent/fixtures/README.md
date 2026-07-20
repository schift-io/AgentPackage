# Startup Support RAG Source Pack

This fixture is not a pre-written answer corpus.

It is a source pack for building a K-skill integrated RAG demo from public
Korean startup-support materials. The primary path is the Schift web console:
the operator selects public sources or adds a notice/attachment URL, the
website-crawler service fetches and normalizes those documents, Schift API
uploads them into a bucket, and the `k-startup-support` skill answers from
retrieved evidence.

The local scripts are only fallback/dev tools for inspecting the same source
pack. They are not the product flow.

## What Is Included

- `sources.json` - official source registry only.
- `source_urls.txt` - URL list for quick inspection.
- `k-skill.json` - declarative K-skill package descriptor.
- `scripts/fetch-sources.mjs` - downloads source pages/files into ignored local
  folders.
- `scripts/upload-folder.mjs` - uploads fetched `.html`, `.txt`, `.md`, and
  `.pdf` files to a Schift bucket; `.hwpx` files are converted to text first.
- `scripts/register-k-skill.mjs` - registers the K-skill and binds it to a
  Schift bucket.
- `skills/startup-support.md` - routing and answer rules, not source content.
- `questions.json` - smoke questions for demo runs.

## Website Flow

Use the app route:

```text
/app/console/k-skill-rag
```

The page calls:

```text
GET  /v1/k-skills/source-rag/sources
POST /v1/k-skills/source-rag/run
```

The API then calls the crawler service:

```text
POST /v1/website-crawler/source-documents
```

This keeps crawling/parsing in the crawler service and keeps bucket storage,
document ingestion, chunking, indexing, skill registration, and retrieval in
Schift API.

## What Is Not Included

- No hand-written program summaries.
- No baked answers.
- No copied full public pages committed to git.

RAG should retrieve from the documents the user or demo operator provides. If
the assistant can answer without retrieved evidence, the demo is cheating.

## Build A Local Corpus

```bash
cd resources/fixtures/startup-support
node scripts/fetch-sources.mjs
```

This creates ignored local folders:

- `raw/` - original downloaded files.
- `text/` - lightly extracted text for HTML pages.

For PDFs/HWPX files, place them directly under `raw/` or `uploads/`. The upload
script accepts these extensions:

```text
.html .txt .md .pdf .hwpx
```

HWPX is a zipped XML format. The upload script extracts text with the local
`unzip` command and sends a generated `.txt` file to Schift, so the bucket still
contains searchable evidence without requiring the API to ingest HWPX directly.

## Upload To Schift From Local Files

Create or choose a bucket first. Then upload the fetched raw files or extracted
text.

```bash
SCHIFT_API_KEY=sch_... SCHIFT_BUCKET_ID=startup-support-demo \
  node scripts/upload-folder.mjs --dir raw
```

or upload extracted text:

```bash
SCHIFT_API_KEY=sch_... SCHIFT_BUCKET_ID=startup-support-demo \
  node scripts/upload-folder.mjs --dir text
```

Use `raw` when the API handles the file type directly. Use `text` when you want
to show plain extraction for HTML pages.

## Connect The K-Skill From Local Files

After upload, bind the K-skill to the bucket:

```bash
SCHIFT_API_KEY=sch_... SCHIFT_BUCKET_ID=<real-bucket-id> \
  node scripts/register-k-skill.mjs
```

Or let the script create a bucket and register the skill in one step:

```bash
SCHIFT_API_KEY=sch_... node scripts/register-k-skill.mjs --create-bucket
```

The registered skill bundles:

- `sources.json`
- `source_urls.txt`
- `questions.json`
- `scripts/fetch-sources.mjs`
- `scripts/upload-folder.mjs`

The skill is the control plane. The bucket is the evidence store. Invocation
should go through `/v1/skills/{skill_id}/invoke`, which returns `SKILL.md` plus
retrieved bucket hits.

## Demo Rule

The chatbot should answer only after retrieval and should cite the retrieved
file/source. If deadline or eligibility is missing from retrieved material, it
must say so and ask the user to upload the current 공고문 or 첨부 PDF/HWPX.
