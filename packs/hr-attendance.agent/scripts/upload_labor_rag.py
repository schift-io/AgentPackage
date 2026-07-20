#!/usr/bin/env python3
"""HR/근태 APM 법률 RAG 콘텐츠를 Schift 버킷에 업로드.

사용:
  python3 scripts/upload_labor_rag.py --dry-run
  SCHIFT_API_KEY=<key> python3 scripts/upload_labor_rag.py
  SCHIFT_API_KEY=<key> python3 scripts/upload_labor_rag.py --bucket kr-labor-law-reference
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MAX_METADATA_JSON_BYTES = 4 * 1024
MAX_METADATA_KEYS = 32
MAX_METADATA_KEY_LENGTH = 64
MAX_METADATA_VALUE_LENGTH = 512
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_.\-]+$")
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
RESERVED_METADATA_KEYS = {
    "bucket_id",
    "chunk_id",
    "chunk_index",
    "doc_id",
    "document_id",
    "embed_model",
    "event_time",
    "file_name",
    "file_type",
    "ingest_job_id",
    "locator",
    "modality",
    "source_connection_id",
    "source_kind",
    "source_path",
    "source_pk",
    "source_row_id",
    "source_schema",
    "source_table",
    "status",
    "text",
}
ACCESS_POLICY_METADATA_KEYS = {
    "classification",
    "internal_accessible",
    "owner_department",
    "privacy_level",
    "public_accessible",
    "review_status",
    "scope",
    "uploaded_by_user_id",
}

DEFAULT_BUCKET = "kr-labor-law-reference"
DEFAULT_SOURCE_ROOT = (
    Path(__file__).resolve().parents[1] / "knowledge" / "rag-sources"
)
DEFAULT_REPORT_PATH = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
    / "labor-rag-upload-report.json"
)

LAW_AREA_MAP: dict[str, str] = {
    "01": "general",
    "02": "annual_leave",
    "03": "working_hours",
    "04": "holiday",
    "05": "premium_pay",
    "06": "leave_types",
    "07": "annual_leave",
    "08": "enforcement",
    "09": "faq",
}


def law_area_from_filename(path: Path) -> str:
    prefix = path.stem[:2]
    return LAW_AREA_MAP.get(prefix, "general")


def build_metadata(
    *,
    path: Path,
    root: Path,
    bucket: str,
    batch_id: str,
) -> dict[str, str]:
    stat = path.stat()
    return {
        "agent_hub_bucket_role": "regulation_reference",
        "agent_hub_contract": "SCHIFT_RAG_BUCKET",
        "agent_hub_default_bucket": DEFAULT_BUCKET,
        "agent_hub_schema": "hr_labor_rag.v1",
        "memory_scope": "regulation_reference",
        "memory_kind": "regulation_reference",
        "source_group": "kr-labor-law",
        "law_area": law_area_from_filename(path),
        "source_rel_path": str(path.relative_to(root)),
        "source_ext": path.suffix.lower().lstrip(".") or "none",
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_mtime_utc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
        "source_bytes": str(stat.st_size),
        "seed_batch": batch_id,
        "effective_date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "canonicality": "reference",
        "product_area": "hr_attendance",
        "rag_bucket": bucket,
    }


def validate_metadata(metadata: dict[str, Any]) -> None:
    encoded = json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    if len(encoded) > MAX_METADATA_JSON_BYTES:
        raise ValueError(f"metadata exceeds {MAX_METADATA_JSON_BYTES} bytes")
    if len(metadata) > MAX_METADATA_KEYS:
        raise ValueError(f"metadata has too many keys: {len(metadata)}")
    for key, value in metadata.items():
        if not isinstance(key, str):
            raise ValueError("metadata keys must be strings")
        if len(key) == 0 or len(key) > MAX_METADATA_KEY_LENGTH:
            raise ValueError(f"metadata key length invalid: {key}")
        if not KEY_PATTERN.fullmatch(key):
            raise ValueError(f"metadata key is not API-safe: {key}")
        if key.startswith("schift.") or key in RESERVED_METADATA_KEYS:
            raise ValueError(f"metadata key is reserved by Schift: {key}")
        if key in ACCESS_POLICY_METADATA_KEYS:
            raise ValueError(f"metadata key is server-stamped access policy: {key}")
        if value is None:
            raise ValueError(f"metadata value must not be null: {key}")
        if not isinstance(value, str):
            raise ValueError(f"metadata value must be a string: {key}")
        if len(value) > MAX_METADATA_VALUE_LENGTH:
            raise ValueError(f"metadata value exceeds {MAX_METADATA_VALUE_LENGTH}: {key}")
        if CONTROL_CHAR_PATTERN.search(value):
            raise ValueError(f"metadata value contains control character: {key}")


def multipart_body(
    *,
    field_name: str,
    file_path: Path,
    metadata: dict[str, str],
    chunk_size: int,
    chunk_overlap: int,
    ocr_strategy: str,
) -> tuple[bytes, str]:
    boundary = f"----laborrag{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()
    parts: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )

    add_field("ocr_strategy", ocr_strategy)
    add_field("chunk_size", str(chunk_size))
    add_field("chunk_overlap", str(chunk_overlap))
    add_field("metadata", json.dumps(metadata, ensure_ascii=False, separators=(",", ":")))
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(file_bytes)
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def request_json(
    method: str,
    url: str,
    *,
    api_key: str,
    body: bytes | None = None,
    content_type: str | None = None,
    timeout: int,
) -> tuple[int, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "schift-hr-labor-rag-uploader/0.1",
    }
    if content_type:
        headers["Content-Type"] = content_type
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, {"raw": raw}


def collect_documents(root: Path) -> list[Path]:
    paths = sorted(root.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"No .md files found in {root}")
    return paths


def sync_document(
    *,
    api_base_url: str,
    api_key: str,
    bucket: str,
    path: Path,
    root: Path,
    batch_id: str,
    timeout: int,
    dry_run: bool,
    chunk_size: int,
    chunk_overlap: int,
    ocr_strategy: str,
) -> dict[str, Any]:
    metadata = build_metadata(path=path, root=root, bucket=bucket, batch_id=batch_id)
    validate_metadata(metadata)
    rel_path = str(path.relative_to(root))
    item = {
        "file": rel_path,
        "metadata": metadata,
        "metadata_bytes": len(
            json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode(
                "utf-8"
            )
        ),
    }
    if dry_run:
        return {**item, "status": "dry_run"}
    body, content_type = multipart_body(
        field_name="files",
        file_path=path,
        metadata=metadata,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        ocr_strategy=ocr_strategy,
    )
    status, payload = request_json(
        "POST",
        f"{api_base_url}/v2/buckets/{bucket}/documents",
        api_key=api_key,
        body=body,
        content_type=content_type,
        timeout=timeout,
    )
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if status != 200 or not isinstance(jobs, list) or len(jobs) != 1:
        raise RuntimeError(
            f"upload failed for {rel_path}: status={status} payload={payload}"
        )
    return {**item, "status": "uploaded", "http_status": status, "jobs": jobs}


def delete_document(
    *, api_base_url: str, api_key: str, bucket: str, document_id: str, timeout: int
) -> dict[str, Any]:
    status, payload = request_json(
        "DELETE",
        f"{api_base_url}/v2/buckets/{bucket}/documents/{document_id}",
        api_key=api_key,
        timeout=timeout,
    )
    if status not in {200, 202, 404}:
        raise RuntimeError(f"delete failed for {document_id}: {status} {payload}")
    return {"document_id": document_id, "http_status": status, "payload": payload}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload HR/근태 APM labor-law RAG sources into Schift bucket."
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--bucket",
        default=os.getenv("SCHIFT_RAG_BUCKET", DEFAULT_BUCKET),
        help="Target bucket name or ID (default: kr-labor-law-reference)",
    )
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("SCHIFT_API_BASE_URL", "https://api.schift.io"),
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("SCHIFT_API_KEY")
        or os.getenv("SCHIFT_AGENT_HUB_UPLOAD_KEY"),
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(os.getenv("HR_LABOR_RAG_SOURCE_ROOT", DEFAULT_SOURCE_ROOT)),
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--batch-id", default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    )
    parser.add_argument(
        "--chunk-size", type=int, default=512, help="Chunk size for embedding"
    )
    parser.add_argument(
        "--chunk-overlap", type=int, default=50, help="Chunk overlap for embedding"
    )
    parser.add_argument(
        "--ocr-strategy", default="auto", help="OCR strategy (auto|off|force)"
    )
    parser.add_argument(
        "--delete-document-id",
        action="append",
        default=[],
        help="Delete a document before uploading (can be repeated).",
    )
    args = parser.parse_args()

    if not args.api_key and not args.dry_run:
        raise SystemExit(
            "SCHIFT_API_KEY or SCHIFT_AGENT_HUB_UPLOAD_KEY environment variable is required"
        )

    root = args.source_root.expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Source root does not exist: {root}")

    api_base_url = args.api_base_url.rstrip("/")
    documents = collect_documents(root)

    report: dict[str, Any] = {
        "bucket": args.bucket,
        "api_base_url": api_base_url,
        "source_root": str(root),
        "batch_id": args.batch_id,
        "dry_run": args.dry_run,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "ocr_strategy": args.ocr_strategy,
        "deleted": [],
        "uploaded": [],
    }

    for document_id in args.delete_document_id:
        if args.dry_run:
            report["deleted"].append({"document_id": document_id, "status": "dry_run"})
            continue
        report["deleted"].append(
            delete_document(
                api_base_url=api_base_url,
                api_key=args.api_key,
                bucket=args.bucket,
                document_id=document_id,
                timeout=args.timeout,
            )
        )

    failures = 0
    for path in documents:
        try:
            report["uploaded"].append(
                sync_document(
                    api_base_url=api_base_url,
                    api_key=args.api_key,
                    bucket=args.bucket,
                    path=path,
                    root=root,
                    batch_id=args.batch_id,
                    timeout=args.timeout,
                    dry_run=args.dry_run,
                    chunk_size=args.chunk_size,
                    chunk_overlap=args.chunk_overlap,
                    ocr_strategy=args.ocr_strategy,
                )
            )
        except RuntimeError as exc:
            failures += 1
            report["uploaded"].append(
                {
                    "file": str(path.relative_to(root)),
                    "status": "failed",
                    "error": str(exc),
                }
            )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "bucket": args.bucket,
                "batch_id": args.batch_id,
                "dry_run": args.dry_run,
                "deleted_count": len(report["deleted"]),
                "uploaded_count": len(report["uploaded"]),
                "failure_count": failures,
                "report": str(args.report),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    if failures:
        raise SystemExit(f"Upload completed with {failures} failure(s)")


if __name__ == "__main__":
    main()
