---
name: k-startup-support
description: K-skill for fetching, uploading, and retrieving Korean startup-support public notices and user-uploaded PDF/TXT/MD/HWPX documents.
model: gpt-4o-mini
rag: startup-support-demo
allowed-tools:
  - rag_search
  - rag_startup_support_demo
procedures:
  - retrieve-before-answering
  - classify-founder-stage
  - cite-document-source
  - ask-for-missing-current-notice
constraints:
  - no-answer-without-retrieval
  - no-manual-eligibility-guarantee
  - no-stale-deadline-claim
---

# Startup Support RAG Skill

This K-skill is for a RAG demo where the knowledge comes from uploaded
documents, not from hand-written program summaries. The skill bundles source
fetching instructions and source registry files; the answer must come from the
bound bucket.

## Rules

1. Search the RAG bucket before answering.
2. If the bucket has no hits, read bundled `sources.json` and ask the operator
   to fetch/upload the relevant official notice, PDF, TXT, MD, or HWPX file.
3. Cite the retrieved document name, source URL if present, and date if present.
4. If the retrieved text does not include deadline, target, budget, or required
   documents, say the uploaded material is insufficient.
5. If the user asks about a current application period but only stale documents
   are retrieved, say that the current 공고문 or 첨부 PDF/HWPX must be uploaded.
6. Do not guarantee eligibility or selection.

## Stage Questions

If needed, ask for:

- 사업자등록 여부
- 법인/개인사업자 설립일
- 폐업 또는 재창업 여부
- 업종: cafe, franchise, hotel, SaaS, manufacturing, public-sector supplier
- goal: 사업화, R&D, 융자, 재도전, 소상공인 정책자금
