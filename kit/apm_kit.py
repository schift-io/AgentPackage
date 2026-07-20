#!/usr/bin/env python3
"""apm-kit — `.apm` 팩 점검/빌드 키트.

팩 repo(`schift-packs`)의 CI가 돌리는 검증 도구. **agent-hub에 의존하지 않는다** —
팩은 배포물이고 배포물이 서비스 코드를 import하면 분리한 의미가 없다.

명령:
  check  <pack> [--host agent-hub|local-byo]  호스트 능력 대조 (fail-closed)
  lint   <pack>                                어휘·필수 필드·테넌트 정체성 스캔
  market                                       .claude-plugin/marketplace.json 생성

발행 정책은 **fail-closed**: `apm.yml`에 `marketplace.publish: true`를 명시하지 않은
팩은 마켓플레이스에 실리지 않는다. 선언이 없는 것이 기본이고, 그게 안전한 기본값이다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

KIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = KIT_DIR.parent
PACKS_DIR = REPO_ROOT / "packs"
CAPS = json.loads((KIT_DIR / "capabilities.json").read_text(encoding="utf-8"))

VOCAB: set[str] = set(CAPS["capabilities"])
CLOUD_ONLY: set[str] = set(CAPS["cloud_only"])

#: 공개 마켓플레이스에 나가면 안 되는 테넌트 정체성 흔적. 팩이 특정 org 이름/브랜드를
#: 하드코딩하면 다른 org가 설치했을 때 그 정체성이 새어나간다(2026-07-20 tenancy
#: leakage 감사에서 실재 확인). 공개 발행 전 차단한다.
TENANT_IDENTITY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bRoom\s?821\b", "Room821 정체성"),
    (r"\broom821\b", "room821 식별자"),
    (r"#FF4D00", "Schift 브랜드 컬러"),
    (r"\bkimbyun\b", "폐기된 legal 트랙 식별자"),
)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:  # pragma: no cover - 환경 문제는 즉시 알린다
        sys.exit("apm-kit requires PyYAML: pip install pyyaml")
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _pack_dirs(name: str | None) -> list[Path]:
    if name:
        for candidate in (PACKS_DIR / name, PACKS_DIR / f"{name}.agent"):
            if candidate.is_dir():
                return [candidate]
        sys.exit(f"pack not found: {name}")
    return sorted(p for p in PACKS_DIR.glob("*.agent") if p.is_dir())


def _required_caps(pack: Path) -> set[str]:
    boundary = _load_yaml(pack / "apm.yml").get("runtime_boundary") or {}
    declared = boundary.get("host_services_only") or []
    if isinstance(declared, str):
        declared = [declared]
    return {str(c).strip() for c in declared if str(c).strip()}


def _host_provides(host: str) -> set[str]:
    spec = CAPS["hosts"].get(host)
    if spec is None:
        sys.exit(f"unknown host: {host} (known: {', '.join(CAPS['hosts'])})")
    if spec.get("provides") == "*":
        return set(VOCAB)
    return VOCAB - set(spec.get("excludes") or [])


def cmd_check(args: argparse.Namespace) -> int:
    provides = _host_provides(args.host)
    failed = 0
    for pack in _pack_dirs(args.pack):
        required = _required_caps(pack)
        unknown = required - VOCAB
        missing = (required & VOCAB) - provides
        if not required:
            print(f"·  {pack.name}: no host_services_only declared (no requirement)")
            continue
        if unknown or missing:
            failed += 1
            reasons = []
            if unknown:
                reasons.append(f"unknown {sorted(unknown)}")
            if missing:
                reasons.append(f"host {args.host!r} lacks {sorted(missing)}")
            print(f"✗  {pack.name}: {'; '.join(reasons)}")
        else:
            print(f"✓  {pack.name}: satisfied by {args.host} ({len(required)} caps)")
    return 1 if failed else 0


def cmd_lint(args: argparse.Namespace) -> int:
    failed = 0
    for pack in _pack_dirs(args.pack):
        problems: list[str] = []
        manifest = _load_yaml(pack / "apm.yml")

        if not manifest.get("name"):
            problems.append("apm.yml missing 'name'")
        if not manifest.get("version"):
            problems.append("apm.yml missing 'version'")
        if not (pack / "agent.md").is_file():
            problems.append("agent.md missing")

        unknown = _required_caps(pack) - VOCAB
        if unknown:
            problems.append(f"unknown capabilities {sorted(unknown)}")

        # 공개 발행 대상만 정체성 스캔 — 내부 전용 팩은 org 정체성을 가져도 정상이다.
        if (manifest.get("marketplace") or {}).get("publish"):
            for path in sorted(pack.rglob("*")):
                if not path.is_file() or path.suffix not in {".md", ".yml", ".yaml"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for pattern, label in TENANT_IDENTITY_PATTERNS:
                    if re.search(pattern, text):
                        rel = path.relative_to(pack)
                        problems.append(f"publish-blocked: {label} in {rel}")

        if problems:
            failed += 1
            print(f"✗  {pack.name}")
            for problem in problems:
                print(f"     - {problem}")
        else:
            print(f"✓  {pack.name}")
    return 1 if failed else 0


def cmd_market(args: argparse.Namespace) -> int:
    """`marketplace.publish: true` 를 선언한 팩만 실어 marketplace.json 을 만든다.

    **source는 이 repo 안의 상대경로가 아니라 각 팩의 공개 repo를 가리킨다.**
    이 repo(AgentPackage)는 private이고 내부 팩 24개를 담고 있어서, 마켓플레이스로
    쓰려고 public으로 뒤집으면 그 24개 소스가 통째로 노출된다 — `marketplace.json`은
    *목록에 뭘 싣느냐*만 통제하지 *repo에 뭐가 보이느냐*는 통제하지 못한다.

    그래서 공개 팩은 **팩마다 자기 public repo**를 갖고, 여기서는 그 repo를
    `git-subdir`/`url` 소스로 가리키기만 한다. 공식 Claude 마켓플레이스가 쓰는
    형식과 동일하며, `sha` 핀이 곧 무결성 보증이다(우리 content-hash와 같은 철학).

        marketplace:
          publish: true
          repo: https://github.com/schift-io/<pack>.git
          ref: main
          sha: <40-hex>        # 없으면 ref만 — 재현 불가라 경고한다
          path: <subdir>       # repo 안 하위경로면 git-subdir
    """
    plugins: list[dict[str, Any]] = []
    skipped: list[str] = []
    unpinned: list[str] = []
    for pack in _pack_dirs(None):
        manifest = _load_yaml(pack / "apm.yml")
        market = manifest.get("marketplace") or {}
        if not market.get("publish"):
            skipped.append(pack.name)
            continue

        repo_url = market.get("repo")
        if not repo_url:
            sys.exit(
                f"{pack.name}: marketplace.publish is true but 'repo' is missing. "
                "공개 팩은 자기 public repo를 가리켜야 한다(이 repo는 private)."
            )
        source: dict[str, Any] = {
            "source": "git-subdir" if market.get("path") else "url",
            "url": repo_url,
        }
        if market.get("path"):
            source["path"] = market["path"]
        if market.get("ref"):
            source["ref"] = market["ref"]
        if market.get("sha"):
            source["sha"] = market["sha"]
        else:
            unpinned.append(pack.name)

        plugins.append(
            {
                "name": market.get("name") or pack.name.removesuffix(".agent"),
                "description": market.get("description")
                or (manifest.get("description") or "").strip().replace("\n", " "),
                "source": source,
                "category": market.get("category", "productivity"),
                "tags": list(market.get("tags") or []),
            }
        )

    doc = {
        "name": "agent-package",
        "description": "Agent Package — sealed, RAG-native agent packs. "
        "Grounding and execution via Schift Cloud (API key required).",
        "owner": {"name": "Schift", "url": "https://github.com/schift-io"},
        "plugins": plugins,
    }
    out = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"wrote {out.relative_to(REPO_ROOT)} — {len(plugins)} published")
    if skipped:
        # 조용한 누락 금지: 무엇이 왜 빠졌는지 항상 말한다.
        print(f"  not published ({len(skipped)}, no marketplace.publish): {', '.join(skipped)}")
    if unpinned:
        # ref만 있고 sha가 없으면 설치 시점마다 내용이 달라질 수 있다 — 재현 불가.
        print(f"  ⚠ unpinned (no sha, not reproducible): {', '.join(unpinned)}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """팩 디렉토리 → `.apm` 아티팩트. **apm.yml 이 단일 정본이다.**

    agent-hub 의 `build_pack_apm` 은 매니페스트를 **코드**(`AGENT_PACKS`)에서 만든다.
    그래서 오늘은 두 빌드의 hash 가 다르다 — 그 차이가 곧 이중 선언 부채(S1)이며,
    `manifest_overrides` 를 폐기하고 apm.yml 파생으로 수렴시키면 사라진다.
    이 명령은 **수렴 후의 정답 형태**를 미리 구현해 둔 것이다.
    """
    from apm_codec import build_apm_bundle

    out_dir = Path(args.out or (REPO_ROOT / "dist"))
    out_dir.mkdir(parents=True, exist_ok=True)
    rc = 0
    for pack in _pack_dirs(args.pack):
        manifest = _load_yaml(pack / "apm.yml")
        if not manifest:
            print(f"✗  {pack.name}: apm.yml missing/empty")
            rc = 1
            continue
        manifest = dict(manifest)
        manifest.setdefault("agent_id", pack.name.removesuffix(".agent"))

        files: dict[str, bytes] = {}
        for path in sorted(pack.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files[str(path.relative_to(pack))] = path.read_bytes()

        blob, chash = build_apm_bundle(manifest, files)
        target = out_dir / f"{manifest['agent_id']}-{manifest.get('version', '0.0.0')}.apm"
        target.write_bytes(blob)
        print(
            f"✓  {pack.name}: {len(files)} files, {len(blob)} bytes, "
            f"hash {chash[:16]}… → {target.relative_to(REPO_ROOT)}"
        )
    return rc


def main() -> int:
    parser = argparse.ArgumentParser(prog="apm-kit", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="host capability check")
    p_check.add_argument("pack", nargs="?")
    p_check.add_argument("--host", default="agent-hub")
    p_check.set_defaults(func=cmd_check)

    p_lint = sub.add_parser("lint", help="vocabulary / required fields / identity scan")
    p_lint.add_argument("pack", nargs="?")
    p_lint.set_defaults(func=cmd_lint)

    p_build = sub.add_parser("build", help="pack dir -> .apm artifact (apm.yml = 정본)")
    p_build.add_argument("pack", nargs="?")
    p_build.add_argument("--out", help="output dir (default: dist/)")
    p_build.set_defaults(func=cmd_build)

    p_market = sub.add_parser("market", help="generate .claude-plugin/marketplace.json")
    p_market.set_defaults(func=cmd_market)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
