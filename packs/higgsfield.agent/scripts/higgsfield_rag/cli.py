from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from .http import (
    BucketAPIError,
    JsonValue,
    resolve_bucket_id,
    upload_document,
)
from .seed import (
    DEFAULT_BUCKET,
    DEFAULT_SOURCE_ROOT,
    REQUIRED_KINDS,
    build_metadata,
    collect_documents,
    require_live_confirmation,
    validate_metadata,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the dedicated Higgsfield directing-reference RAG bucket."
    )
    parser.add_argument(
        "--live", action="store_true", help="Enable external bucket writes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly select the default preview mode",
    )
    parser.add_argument("--confirm-live-upload")
    parser.add_argument(
        "--bucket",
        default=os.getenv("HIGGSFIELD_DIRECTING_RAG_BUCKET", DEFAULT_BUCKET),
    )
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("SCHIFT_API_BASE_URL", "https://api.schift.io"),
    )
    parser.add_argument(
        "--api-key",
        default=(
            os.getenv("SCHIFT_KNOWLEDGE_API_KEY")
            or os.getenv("SCHIFT_API_KEY")
            or os.getenv("SCHIFT_AGENT_HUB_UPLOAD_KEY")
        ),
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--batch-id", default=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    )
    args = parser.parse_args()
    if args.live and args.dry_run:
        raise SystemExit("Choose either --live or --dry-run, not both.")
    dry_run = require_live_confirmation(
        live=args.live, confirmation=args.confirm_live_upload
    )
    if not dry_run and not args.api_key:
        raise SystemExit(
            "SCHIFT_KNOWLEDGE_API_KEY or SCHIFT_API_KEY is required for --live"
        )
    root = args.source_root.expanduser().resolve()
    documents = collect_documents(root)
    api_base_url = args.api_base_url.rstrip("/")
    bucket_id = (
        None
        if dry_run
        else resolve_bucket_id(api_base_url, args.api_key, args.bucket, args.timeout)
    )
    results: list[JsonValue] = []
    for seed in documents:
        path = root / seed.file_name
        metadata = build_metadata(
            seed,
            path=path,
            root=root,
            bucket=args.bucket,
            batch_id=args.batch_id,
        )
        validate_metadata(metadata)
        metadata_json: dict[str, JsonValue] = {
            key: value for key, value in metadata.items()
        }
        item: dict[str, JsonValue] = {
            "file": seed.file_name,
            "metadata": metadata_json,
            "status": "dry_run",
        }
        if not dry_run:
            if bucket_id is None:
                raise BucketAPIError("live upload requires a resolved bucket_id")
            item.update(
                {
                    "status": "uploaded",
                    "response": upload_document(
                        api_base_url=api_base_url,
                        api_key=args.api_key,
                        bucket_id=bucket_id,
                        path=path,
                        metadata=metadata,
                        timeout=args.timeout,
                    ),
                }
            )
        results.append(item)
    required_kinds: list[JsonValue] = list(sorted(REQUIRED_KINDS))
    report: dict[str, JsonValue] = {
        "bucket": args.bucket,
        "bucket_id": bucket_id,
        "dry_run": dry_run,
        "network_requests": 0 if dry_run else None,
        "required_kinds": required_kinds,
        "documents": results,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "bucket": args.bucket,
                "bucket_id": bucket_id,
                "dry_run": dry_run,
                "document_count": len(results),
                "required_kinds": sorted(REQUIRED_KINDS),
                "report": str(args.report) if args.report else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
