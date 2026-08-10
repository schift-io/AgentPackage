from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from typing import TypeAlias
from urllib.error import HTTPError
from urllib.request import Request, urlopen

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)


class BucketAPIError(RuntimeError):
    pass


def request_json(
    method: str,
    url: str,
    *,
    api_key: str,
    body: bytes | None = None,
    content_type: str | None = None,
    timeout: int,
) -> tuple[int, JsonValue]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "schift-higgsfield-directing-rag-uploader/0.1",
    }
    if content_type:
        headers["Content-Type"] = content_type
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw, status = response.read().decode(), response.status
    except HTTPError as exc:
        raw, status = exc.read().decode(errors="replace"), exc.code
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, {"raw": raw}


def resolve_bucket_id(
    api_base_url: str, api_key: str, bucket: str, timeout: int
) -> str:
    status, payload = request_json(
        "GET", f"{api_base_url}/v2/buckets", api_key=api_key, timeout=timeout
    )
    if status != 200:
        raise BucketAPIError(f"bucket list failed: status={status} payload={payload}")
    items: list[dict[str, JsonValue]] = []
    if isinstance(payload, list):
        items = [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        raw_buckets = payload.get("buckets")
        if isinstance(raw_buckets, list):
            items = [item for item in raw_buckets if isinstance(item, dict)]
    for item in items:
        if item.get("id") == bucket or item.get("name") == bucket:
            bucket_id = item.get("id")
            if isinstance(bucket_id, str) and bucket_id:
                return bucket_id
    body = json.dumps(
        {
            "name": bucket,
            "description": (
                "Shared Schift directing craft references for the Higgsfield APM"
            ),
        }
    ).encode()
    status, created = request_json(
        "POST",
        f"{api_base_url}/v2/buckets",
        api_key=api_key,
        body=body,
        content_type="application/json",
        timeout=timeout,
    )
    candidate: JsonValue = created
    if isinstance(created, dict):
        candidate = created.get("bucket", created)
    bucket_id = candidate.get("id") if isinstance(candidate, dict) else None
    if status not in {200, 201} or not isinstance(bucket_id, str) or not bucket_id:
        raise BucketAPIError(f"bucket create failed: status={status} payload={created}")
    return bucket_id


def multipart_body(path: Path, metadata: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----higgsfieldrag{uuid.uuid4().hex}"
    fields = {
        "ocr_strategy": "auto",
        "chunk_size": "512",
        "chunk_overlap": "50",
        "metadata": json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
    }
    parts = [
        (
            f"--{boundary}\r\nContent-Disposition: form-data; "
            f'name="{name}"\r\n\r\n{value}\r\n'
        ).encode()
        for name, value in fields.items()
    ]
    content_type = mimetypes.guess_type(path.name)[0] or "text/markdown"
    parts.extend(
        [
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="files"; '
                f'filename="{path.name}"\r\nContent-Type: {content_type}\r\n\r\n'
            ).encode(),
            path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def upload_document(
    *,
    api_base_url: str,
    api_key: str,
    bucket_id: str,
    path: Path,
    metadata: dict[str, str],
    timeout: int,
) -> JsonValue:
    body, content_type = multipart_body(path, metadata)
    status, payload = request_json(
        "POST",
        f"{api_base_url}/v2/buckets/{bucket_id}/documents",
        api_key=api_key,
        body=body,
        content_type=content_type,
        timeout=timeout,
    )
    jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if status != 200 or not isinstance(jobs, list) or len(jobs) != 1:
        raise BucketAPIError(
            f"upload failed for {path.name}: status={status} payload={payload}"
        )
    return payload
