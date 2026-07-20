"""`.apm` 코덱 — 포맷의 정본 구현.

이건 **서비스가 아니라 포맷**이다. tar+canonical-JSON 매니페스트를 결정적으로 묶고
content-hash를 계산하는 규칙이므로 팩 repo가 소유한다. agent-hub 는 장차 이 구현을
소비하도록 수렴시킨다(현재는 `src/agent_hub/apm_package.py` 사본이 있다).

결정성 보장: gzip mtime=0, tar 항목 mtime/uid/gid/mode 고정, 경로 정렬,
canonical JSON(sort_keys + 고정 구분자). 같은 입력 → 같은 바이트 → 같은 hash.

"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from typing import Any

# .apm 안에서 canonical manifest가 놓이는 경로.
MANIFEST_NAME = "manifest.json"


class ApmHashMismatch(ValueError):
    """받은 .apm의 content-hash가 기대값(DB 등록 hash)과 다르다 — 변조/drift."""


def _canonical_json(obj: Any) -> bytes:
    """정렬·고정 구분자 JSON 바이트. 같은 의미 → 같은 바이트(해시 안정)."""
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


# content-hash 는 **팩 내용**의 주소다. 아래 키들은 내용이 아니라 *호스트가 이 팩을
# 어떻게 등록/전시하는가*(라우터 힌트·허브 UI 라벨·플래그·노출 토글)라서 주소에서
# 제외한다. 번들에는 그대로 실린다 — 해시 범위에서만 빠진다.
#
# ⚠️ **agent-hub 의 `apm_package.HASH_EXCLUDED_KEYS` 와 반드시 같아야 한다.**
# 한쪽만 바꾸면 같은 팩에 다른 hash 가 나와 두 발행자가 서로 덮어쓰거나 409 를
# 반복한다. 실제로 이 불일치 때문에 발행 자동화를 켤 수 없었다(2026-07-21).
HASH_EXCLUDED_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "router_enabled",
        "router_topic_hints",
        "router_shortcut_keywords",
        "router_slash_commands",
        "router_requires_attachment",
        "router_scope",
        "router_session_scope",
        "router_min_confidence",
        "router_description",
        "router_default_handler",
        "hub_label",
        "hub_role",
        "hub_inputs",
        "hub_output",
        "hub_review",
        "intake_question",
        "intake_options",
        "feature_flag",
        "hidden",
        "owner_org_id",
    }
)


def hashable_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """content-hash 계산에 쓰는 매니페스트 투영 — 전시/등록 메타를 뺀 것."""
    return {k: v for k, v in manifest.items() if k not in HASH_EXCLUDED_KEYS}


def content_hash(manifest: dict[str, Any], files: dict[str, bytes]) -> str:
    """manifest + 모든 번들 파일을 덮는 결정적 sha256 (hex).

    파일은 경로순 정렬해 (path, sha256(bytes))를 누적 → 순서 무관·전체 커버.
    manifest 는 `hashable_manifest()` 로 투영해 전시/등록 메타를 제외한다.
    """
    h = hashlib.sha256()
    h.update(b"apm-v1\n")
    h.update(
        hashlib.sha256(_canonical_json(hashable_manifest(manifest)))
        .hexdigest()
        .encode()
    )
    h.update(b"\n")
    for path in sorted(files):
        h.update(path.encode("utf-8"))
        h.update(b"\0")
        h.update(hashlib.sha256(files[path]).hexdigest().encode())
        h.update(b"\n")
    return h.hexdigest()


def build_apm_bundle(
    manifest: dict[str, Any], files: dict[str, bytes] | None = None
) -> tuple[bytes, str]:
    """(.apm tar.gz 바이트, content_hash) 반환. 결정적."""
    files = dict(files or {})
    chash = content_hash(manifest, files)

    raw = io.BytesIO()
    # mtime=0 gzip (결정성) — gzip 헤더의 타임스탬프 제거.
    with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        tar_buf = io.BytesIO()
        with tarfile.open(fileobj=tar_buf, mode="w") as tar:
            entries = {MANIFEST_NAME: _canonical_json(manifest), **files}
            for path in sorted(entries):
                data = entries[path]
                info = tarfile.TarInfo(name=path)
                info.size = len(data)
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(data))
        gz.write(tar_buf.getvalue())
    return raw.getvalue(), chash


def read_apm_bundle(data: bytes) -> tuple[dict[str, Any], dict[str, bytes]]:
    """.apm 바이트 → (manifest, files). manifest는 MANIFEST_NAME에서 파싱."""
    files: dict[str, bytes] = {}
    manifest: dict[str, Any] = {}
    with gzip.GzipFile(fileobj=io.BytesIO(data), mode="rb") as gz:
        with tarfile.open(fileobj=io.BytesIO(gz.read()), mode="r") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                f = tar.extractfile(member)
                if f is None:
                    continue
                content = f.read()
                if member.name == MANIFEST_NAME:
                    manifest = json.loads(content.decode("utf-8"))
                else:
                    files[member.name] = content
    return manifest, files


def verify_apm_bundle(data: bytes, expected_hash: str) -> dict[str, Any]:
    """.apm를 언팩하고 content-hash가 expected와 같은지 검증. 다르면 ApmHashMismatch.

    반환: 검증된 manifest(dict). (이후 validate_manifest 화이트리스트 게이트는 별도.)
    """
    manifest, files = read_apm_bundle(data)
    actual = content_hash(manifest, files)
    if actual != expected_hash:
        raise ApmHashMismatch(
            f"content-hash mismatch: expected {expected_hash[:12]}…, got {actual[:12]}…"
        )
    return manifest
