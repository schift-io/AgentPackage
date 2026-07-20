#!/usr/bin/env python3
"""`.apm` 발행 — R2 put(dedup) + schift-api 레지스트리 ref 등록.

## 왜 이게 여기 있나

발행이 **agent-hub 배포에만 붙어 있었다**. 그래서 팩만 고치고 서비스를 배포하지
않으면 레지스트리가 그대로 썩는다 — 2026-07-20 실측으로 **6일간 방치**돼 있었고,
그 사이 prod 레지스트리의 image-gen 은 폐기된 taxonomy 버전을 가리키고 있었다.

팩은 배포물이므로 **팩 변경 자체가 발행을 트리거**해야 한다. 이 스크립트가 그
진입점이고, agent-hub 에 의존하지 않는다(팩 repo 가 서비스 코드를 import 하면
분리한 의미가 없다).

## 계약

- content-hash 가 주소다. 같은 hash 가 R2 에 이미 있으면 업로드를 건너뛴다(dedup).
- 레지스트리는 **같은 버전에 다른 hash 를 거부**한다(`ApmRefConflictError`, 409).
  내용이 바뀌면 버전을 올려야 한다 — 여기서 409 는 **정상 동작**이므로 실패로
  세지 않고 건너뛴다. 한 팩의 409 가 나머지 발행을 막으면 안 된다.
- ACL(visibility / owner_org / allowed_orgs)은 apm.yml 선언에서 파생한다.
  미선언이면 서버 기본 private — 즉 아무도 못 본다(fail-closed).

## 환경변수

  SCHIFT_ADMIN_KEY        레지스트리 등록 (필수)
  R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY   (필수)
  R2_BUCKET               기본 schift-data
  SCHIFT_API_URL          기본 https://api.schift.io
  APM_PUBLISH_DRY_RUN=1   빌드·비교만 하고 쓰지 않음
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = KIT_DIR.parent
sys.path.insert(0, str(KIT_DIR))

from apm_codec import build_apm_bundle  # noqa: E402

# api.schift.io 는 Cloudflare 뒤라 기본 UA 는 WAF 403 위험(사고 이력).
_UA = "SchiftAgentPackage/1.0 (+https://schift.io)"


def _load_yaml(path: Path) -> dict:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _acl_from_manifest(manifest: dict) -> dict:
    """apm.yml 최상위 ACL 선언 → 등록 payload. 미선언 키는 생략(서버 기본 private)."""
    acl: dict = {}
    vis = manifest.get("visibility")
    if isinstance(vis, str) and vis.strip():
        acl["visibility"] = vis.strip()
    owner = manifest.get("owner_org") or manifest.get("owner_org_id")
    if isinstance(owner, str) and owner.strip():
        acl["owner_org"] = owner.strip()
    allowed = manifest.get("allowed_orgs")
    if isinstance(allowed, list) and allowed:
        acl["allowed_orgs"] = [str(o).strip() for o in allowed if str(o).strip()]
    return acl


def _version_of(manifest: dict) -> str:
    ref = str(manifest.get("package_ref") or "")
    if "@" in ref:
        return ref.rsplit("@", 1)[1].strip() or "0.0.0"
    return str(manifest.get("version") or "0.0.0")


def build_pack(pack_dir: Path) -> dict:
    manifest = _load_yaml(pack_dir / "apm.yml")
    manifest = dict(manifest)
    manifest.setdefault("agent_id", pack_dir.name.removesuffix(".agent"))
    files = {
        str(p.relative_to(pack_dir)): p.read_bytes()
        for p in sorted(pack_dir.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }
    blob, chash = build_apm_bundle(manifest, files)
    built = {
        "agent_id": str(manifest["agent_id"]),
        "version": _version_of(manifest),
        "content_hash": chash,
        "blob": blob,
        "size_bytes": len(blob),
    }
    built.update(_acl_from_manifest(manifest))
    return built


def _r2_client():
    import boto3

    account = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def _register(api_base: str, admin_key: str, payload: dict) -> None:
    req = urllib.request.Request(
        f"{api_base.rstrip('/')}/v1/apm/registry",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {admin_key}",
            "Content-Type": "application/json",
            "User-Agent": _UA,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30):
        return


def main() -> int:
    dry = os.getenv("APM_PUBLISH_DRY_RUN", "").strip() in ("1", "true", "yes")
    api_base = os.getenv("SCHIFT_API_URL", "https://api.schift.io")
    bucket = os.getenv("R2_BUCKET", "schift-data")

    targets = sorted(p for p in (REPO_ROOT / "packs").glob("*.agent") if p.is_dir())
    if not targets:
        print("no packs found", file=sys.stderr)
        return 1

    if not dry:
        admin_key = os.environ["SCHIFT_ADMIN_KEY"]
        s3 = _r2_client()

    published = skipped = failed = 0
    for pack_dir in targets:
        try:
            built = build_pack(pack_dir)
        except Exception as exc:  # noqa: BLE001 — 한 팩 빌드 실패가 나머지를 막지 않는다
            print(f"✗ build {pack_dir.name}: {exc}", file=sys.stderr)
            failed += 1
            continue

        key = f"apm/objects/{built['content_hash']}.apm"
        label = f"{built['agent_id']}@{built['version']}"
        if dry:
            print(f"· {label} {built['content_hash'][:12]}… (dry-run)")
            continue

        try:
            try:
                s3.head_object(Bucket=bucket, Key=key)
                uploaded = False
            except Exception:  # noqa: BLE001 — 없으면 올린다
                s3.put_object(Bucket=bucket, Key=key, Body=built["blob"])
                uploaded = True

            payload = {
                "agent_id": built["agent_id"],
                "version": built["version"],
                "content_hash": built["content_hash"],
                "r2_key": key,
                "size_bytes": built["size_bytes"],
            }
            for acl_key in ("visibility", "owner_org", "allowed_orgs"):
                if built.get(acl_key) is not None:
                    payload[acl_key] = built[acl_key]
            _register(api_base, admin_key, payload)
            published += 1
            print(f"✓ {label} {'uploaded' if uploaded else 'dedup'}")
        except urllib.error.HTTPError as exc:
            if exc.code == 409:
                # 같은 버전에 다른 hash — 버전을 올려야 한다는 뜻이다. 정상 동작.
                skipped += 1
                print(f"· {label} 이미 등록된 버전(내용 변경 시 버전 bump 필요)")
            else:
                failed += 1
                print(f"✗ {label}: HTTP {exc.code}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"✗ {label}: {exc}", file=sys.stderr)

    print(f"\n발행 {published} / 건너뜀 {skipped} / 실패 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
