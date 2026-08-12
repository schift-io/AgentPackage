#!/usr/bin/env python3
"""apm-kit — `.apm` 팩 점검/빌드 키트.

팩 repo(`schift-packs`)의 CI가 돌리는 검증 도구. **agent-hub에 의존하지 않는다** —
팩은 배포물이고 배포물이 서비스 코드를 import하면 분리한 의미가 없다.

명령:
  check  <pack> [--host HOST]                  호스트 능력 대조 (fail-closed)
  lint   <pack> [--identity-patterns PATH]     어휘·필수 필드·테넌트 정체성 스캔
  vendor --dest <dir> [--check]                 정본 코덱 내보내기 / 갈림 검사
  market                                       .claude-plugin/marketplace.json 생성

4개 서브커맨드 전부 `--packs-dir PATH`(기본: `<repo>/packs`)를 받는다 — 이 repo 밖으로
kit만 떼어낼 때 packs 위치를 지정하기 위함. 디렉터리가 없으면 에러로 죽는다(빈손 성공
금지). `lint`의 테넌트 정체성 패턴은 `kit/identity-patterns.json`(기본값)에서 읽는다 —
파일이 없으면 스캔을 건너뛰고 그 사실을 명시적으로 출력한다(조용한 게이트 무력화 금지).

발행 정책은 **fail-closed**: `apm.yml`에 `marketplace.publish: true`를 명시하지 않은
팩은 마켓플레이스에 실리지 않는다. 선언이 없는 것이 기본이고, 그게 안전한 기본값이다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from runtime_contract import (
    declared_host_capabilities,
    runtime_required_capabilities,
    validate_runtime_contract,
)

KIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = KIT_DIR.parent
DEFAULT_PACKS_DIR = REPO_ROOT / "packs"
# ⚠️ **`kit/` 밖(레포 루트)에 둔다.** 이 파일은 막으려는 정체성 문자열 자체를 담고
# 있어서, `kit/` 안에 있으면 kit 을 공개 repo 로 미러하는 순간 그대로 따라간다.
# "미러에서 제외하기"를 잊지 않는 것에 기대는 대신 디렉터리로 갈라 둔다.
DEFAULT_IDENTITY_PATTERNS = REPO_ROOT / "identity-patterns.json"
CAPS = json.loads((KIT_DIR / "capabilities.json").read_text(encoding="utf-8"))

VOCAB: set[str] = set(CAPS["capabilities"])
CLOUD_ONLY: set[str] = set(CAPS["cloud_only"])


def _display_path(path: Path) -> str:
    """레포 밖 경로도 죽지 않고 출력한다.

    `--out`/`--packs-dir` 이 레포 밖(또는 상대경로)을 가리키면 `relative_to(REPO_ROOT)`
    가 ValueError 로 죽는다 — **빌드는 이미 성공했는데 출력 한 줄 때문에 exit 1** 이
    되어 CI 가 실패로 읽는다. 레포 안이면 짧게, 밖이면 절대경로 그대로.
    """
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:  # pragma: no cover - 환경 문제는 즉시 알린다
        sys.exit("apm-kit requires PyYAML: pip install pyyaml")
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _pack_dirs(name: str | None, packs_dir: Path) -> list[Path]:
    if not packs_dir.is_dir():
        sys.exit(f"packs dir not found: {packs_dir} (--packs-dir 로 위치를 지정하라)")
    if name:
        for candidate in (packs_dir / name, packs_dir / f"{name}.agent"):
            if candidate.is_dir():
                return [candidate]
        sys.exit(f"pack not found: {name} (packs-dir={packs_dir})")
    dirs = sorted(p for p in packs_dir.glob("*.agent") if p.is_dir())
    if not dirs:
        # 조용한 성공 금지 — packs-dir 이 비어 있으면 "0개 검사됨"이 곧 게이트가
        # 죽어 있다는 신호다(빈 리포트를 초록으로 착각하지 않게).
        print(f"·  0개 팩 검사됨 (packs-dir={packs_dir}, *.agent 디렉터리 없음)")
    return dirs


def _load_identity_patterns(path: Path) -> list[tuple[str, str]]:
    """테넌트 정체성 패턴을 외부 JSON에서 읽는다. `kit/identity-patterns.json`이 정본 —

    이 파일을 소스에 다시 하드코딩하지 않는다(정체성 패턴 자체가 leak 소스이기
    때문에, leak을 막는 코드가 leak 원인이 되는 것을 막으려는 목적).
    """
    if not path.is_file():
        # 조용히 스캔을 건너뛰면 게이트가 죽은 줄 아무도 모른다 — 명시적으로 알린다.
        print(f"·  정체성 스캔 비활성(패턴 파일 없음): {path}")
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"identity-patterns 파일이 유효한 JSON이 아니다: {path} ({exc})")
    patterns = data.get("patterns") or []
    if not patterns:
        print(f"·  정체성 스캔 활성이나 패턴 0개: {path}")
    return [(str(p["pattern"]), str(p["label"])) for p in patterns]


def _manifest_of(pack: Path) -> dict[str, Any]:
    """SPEC §5 의 정본 판정 순서. `pack.json` 이 있으면 그대로, 없으면 `apm.yml` 파생.

    `pack.json` 을 파생 없이 그대로 쓰기 때문에 **누가 빌드하든 같은 매니페스트**가
    나오고, 따라서 소비자와 hash 가 자동으로 맞는다.
    """
    pack_json = pack / "pack.json"
    if pack_json.is_file():
        manifest = json.loads(pack_json.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            sys.exit(f"{pack.name}: pack.json 이 JSON 객체가 아니다")
    else:
        manifest = dict(_load_yaml(pack / "apm.yml"))
    if not manifest:
        return {}
    manifest.setdefault("agent_id", pack.name.removesuffix(".agent"))
    return manifest


def _version_of(manifest: dict[str, Any]) -> str:
    """SPEC §8 — 버전을 가르는 값은 `package_ref` 의 `@` 뒤. top-level 은 폴백."""
    ref = str(manifest.get("package_ref") or "")
    if "@" in ref:
        return ref.rsplit("@", 1)[1]
    return str(manifest.get("version") or "0.0.0")


def _required_caps(pack: Path) -> set[str]:
    manifest = _manifest_of(pack)
    return declared_host_capabilities(manifest) | runtime_required_capabilities(manifest)


def _host_provides(host: str) -> set[str]:
    spec = CAPS["hosts"].get(host)
    if spec is None:
        sys.exit(f"unknown host: {host} (known: {', '.join(CAPS['hosts'])})")
    if spec.get("provides") == "*":
        return set(VOCAB)
    if isinstance(spec.get("provides"), list):
        return {str(capability) for capability in spec["provides"]}
    return VOCAB - set(spec.get("excludes") or [])


def cmd_check(args: argparse.Namespace) -> int:
    provides = _host_provides(args.host)
    failed = 0
    for pack in _pack_dirs(args.pack, Path(args.packs_dir)):
        manifest = _manifest_of(pack)
        contract_problems = validate_runtime_contract(manifest, pack_root=pack)
        if contract_problems:
            failed += 1
            print(f"✗  {pack.name}: invalid runtime_contract")
            for problem in contract_problems:
                print(f"     - {problem}")
            continue
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
    identity_patterns = _load_identity_patterns(Path(args.identity_patterns))
    failed = 0
    for pack in _pack_dirs(args.pack, Path(args.packs_dir)):
        problems: list[str] = []
        manifest = _manifest_of(pack)
        authoring = _load_yaml(pack / "apm.yml")

        if not authoring.get("name"):
            problems.append("apm.yml missing 'name'")
        if not authoring.get("version"):
            problems.append("apm.yml missing 'version'")
        if not (pack / "agent.md").is_file():
            problems.append("agent.md missing")

        problems.extend(validate_runtime_contract(manifest, pack_root=pack))

        unknown = _required_caps(pack) - VOCAB
        if unknown:
            problems.append(f"unknown capabilities {sorted(unknown)}")

        # 공개 발행 대상만 정체성 스캔 — 내부 전용 팩은 org 정체성을 가져도 정상이다.
        if (authoring.get("marketplace") or {}).get("publish") and identity_patterns:
            for path in sorted(pack.rglob("*")):
                if not path.is_file() or path.suffix not in {".md", ".yml", ".yaml"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for pattern, label in identity_patterns:
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
    AgentPackage 규약 repo와 조직 전용 팩 repo의 공개 범위는 분리해야 한다.
    `marketplace.json`은 *목록에 뭘 싣느냐*만 통제하지 *repo에 뭐가 보이느냐*는
    통제하지 못하므로, private 팩은 별도 repo에 둔다.

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
    for pack in _pack_dirs(None, Path(args.packs_dir)):
        manifest = _load_yaml(pack / "apm.yml")
        market = manifest.get("marketplace") or {}
        if not market.get("publish"):
            skipped.append(pack.name)
            continue

        repo_url = market.get("repo")
        if not repo_url:
            sys.exit(
                f"{pack.name}: marketplace.publish is true but 'repo' is missing. "
                "공개 팩은 자기 public repo를 가리켜야 한다. private 팩은 별도 repo에 둔다."
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
        "Grounding and execution are supplied by the selected Runtime adapter.",
        "owner": {"name": "Schift", "url": "https://github.com/schift-io"},
        "plugins": plugins,
    }
    out = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"wrote {_display_path(out)} — {len(plugins)} published")
    if skipped:
        # 조용한 누락 금지: 무엇이 왜 빠졌는지 항상 말한다.
        print(f"  not published ({len(skipped)}, no marketplace.publish): {', '.join(skipped)}")
    if unpinned:
        # ref만 있고 sha가 없으면 설치 시점마다 내용이 달라질 수 있다 — 재현 불가.
        print(f"  ⚠ unpinned (no sha, not reproducible): {', '.join(unpinned)}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """팩 디렉토리 → `.apm` 아티팩트. **매니페스트 정본은 SPEC §5 의 판정 순서를 따른다.**

    1. `pack.json` 이 있으면 **그대로** 매니페스트로 쓴다(파생 없음).
    2. 없으면 `apm.yml` 에서 파생한다.

    ⚠️ 이 순서를 안 지키면 **소비자와 hash 가 구조적으로 갈린다.** 2026-08-10 실측:
    apm.yml 로만 빌드하던 시절 agent-hub 와 8/8 팩이 전부 달랐고, `pack.json` 을
    쓰도록 고치자 일치했다. 팩 36/36 이 `pack.json` 을 갖고 있으므로 실질적으로는
    항상 1번 경로다. `apm.yml` 은 **저작 포맷**이지 정본이 아니다(§5).
    """
    from apm_codec import build_apm_bundle

    out_dir = Path(args.out or (REPO_ROOT / "dist"))
    out_dir.mkdir(parents=True, exist_ok=True)
    rc = 0
    for pack in _pack_dirs(args.pack, Path(args.packs_dir)):
        manifest = _manifest_of(pack)
        if not manifest:
            print(f"✗  {pack.name}: pack.json/apm.yml missing or empty")
            rc = 1
            continue

        files: dict[str, bytes] = {}
        for path in sorted(pack.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files[str(path.relative_to(pack))] = path.read_bytes()

        blob, chash = build_apm_bundle(manifest, files)
        target = out_dir / f"{manifest['agent_id']}-{_version_of(manifest)}.apm"
        target.write_bytes(blob)
        print(
            f"✓  {pack.name}: {len(files)} files, {len(blob)} bytes, "
            f"hash {chash[:16]}… → {_display_path(target)}"
        )
    return rc


VENDOR_HEADER = """\
# ⚠️ 생성된 파일 — 직접 고치지 마라. 고치면 `apm-kit vendor --check` 가 빨개진다.
#
# 정본: schift-io/AgentPackage `kit/{source_name}`
# 갱신: 그 repo 에서 `python3 kit/apm_kit.py vendor --dest <이 파일의 디렉터리>`
#
# 이 파일이 왜 사본으로 존재하나: `.apm` 포맷은 AgentPackage 가 소유하는데, 그 repo 는
# 소비자(agent-hub) 의 빌드 컨텍스트에 없다(별도 private checkout, gitignored). 배포
# 경로를 만들기 전까지 vendor 로 잇되, **정본은 하나이고 이 파일은 파생**이라는 것을
# 헤더와 sha256 게이트로 강제한다. 손으로 고친 흔적은 게이트가 잡는다.
#
# source-sha256: {sha}
"""


def _vendor_python_payload(source_name: str) -> tuple[str, str]:
    raw = (KIT_DIR / source_name).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    return (
        VENDOR_HEADER.format(source_name=source_name, sha=sha)
        + "\n"
        + raw.decode("utf-8"),
        sha,
    )


def _vendor_payload() -> tuple[str, str]:
    return _vendor_python_payload("apm_codec.py")


def _vendor_runtime_contract_payload() -> tuple[str, str]:
    return _vendor_python_payload("runtime_contract.py")


def _vendor_caps_payload() -> tuple[str, str]:
    """(능력 어휘 JSON, 원본 sha256) — 정본 capabilities.json 에서 파생.

    JSON 은 주석을 못 다니 `_vendored` 블록에 출처와 sha 를 심는다. 소비자는 이걸
    읽어 어휘·호스트 프로필을 만들고, 코드에 이름을 **다시 적지 않는다**.
    """
    raw = (KIT_DIR / "capabilities.json").read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    doc = json.loads(raw.decode("utf-8"))
    doc["_vendored"] = {
        "source": "schift-io/AgentPackage kit/capabilities.json",
        "source_sha256": sha,
        "warning": "생성된 파일 — 직접 고치지 마라. `apm-kit vendor --check` 가 잡는다.",
        "regenerate": "AgentPackage 에서 python3 kit/apm_kit.py vendor --dest <이 파일의 디렉터리>",
    }
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", sha


def cmd_vendor(args: argparse.Namespace) -> int:
    """정본 코덱을 소비자 repo 로 내보낸다 / 내보낸 것이 안 갈렸는지 검사한다.

    `--check` 는 소비자 CI 가 부르는 쪽이다. 파일이 없거나, 헤더가 없거나, 기록된
    sha 가 지금 정본과 다르거나, 본문이 손으로 수정됐으면 **exit 1**.
    """
    targets = [
        (Path(args.dest) / "apm_codec_vendored.py", *_vendor_payload()),
        (
            Path(args.dest) / "apm_runtime_contract_vendored.py",
            *_vendor_runtime_contract_payload(),
        ),
        (Path(args.dest) / "apm_capabilities_vendored.json", *_vendor_caps_payload()),
    ]
    rc = 0
    for dest, payload, sha in targets:
        rc |= _vendor_one(dest, payload, sha, check=args.check)
    return rc


def _vendor_one(dest: Path, payload: str, sha: str, *, check: bool) -> int:
    if check:
        if not dest.is_file():
            print(f"✗  vendor 파일 없음: {_display_path(dest)}")
            return 1
        actual = dest.read_text(encoding="utf-8")
        if actual != payload:
            recorded = ""
            for line in actual.splitlines()[:20]:
                if "source-sha256:" in line:
                    recorded = line.split("source-sha256:")[1].strip()
            print(f"✗  vendor 파일이 정본과 갈렸다: {_display_path(dest)}")
            # 원인을 갈라 말한다. 둘은 대응이 다르다 — 전자는 남의 수정을 되살릴지
            # 판단해야 하고, 후자는 그냥 다시 뽑으면 된다.
            if recorded == sha:
                print("     기록된 sha 는 정본과 같은데 본문이 다르다")
                print(f"     → **이 파일을 손으로 고쳤다.** 고친 내용을 정본"
                      f"(kit/apm_codec.py)에 옮긴 뒤 `vendor` 를 다시 돌려라.")
            else:
                print(f"     기록된 sha={recorded or '(없음)'}")
                print(f"     정본   sha={sha}")
                print("     → 정본이 바뀌었다. `vendor` 를 다시 돌려 갱신하라.")
            return 1
        print(f"✓  vendor 일치 (sha {sha[:16]}…)")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(payload, encoding="utf-8")
    print(f"✓  wrote {_display_path(dest)} (sha {sha[:16]}…)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="apm-kit", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="host capability check")
    p_check.add_argument("pack", nargs="?")
    p_check.add_argument("--host", default="agent-hub")
    p_check.add_argument("--packs-dir", default=str(DEFAULT_PACKS_DIR))
    p_check.set_defaults(func=cmd_check)

    p_lint = sub.add_parser("lint", help="vocabulary / required fields / identity scan")
    p_lint.add_argument("pack", nargs="?")
    p_lint.add_argument("--packs-dir", default=str(DEFAULT_PACKS_DIR))
    p_lint.add_argument(
        "--identity-patterns",
        default=str(DEFAULT_IDENTITY_PATTERNS),
        help="테넌트 정체성 패턴 JSON 경로 (기본: kit/identity-patterns.json). "
        "파일이 없으면 정체성 스캔을 건너뛰고 명시적으로 알린다.",
    )
    p_lint.set_defaults(func=cmd_lint)

    p_build = sub.add_parser("build", help=".agent dir -> .apm artifact")
    p_build.add_argument("pack", nargs="?")
    p_build.add_argument("--out", help="output dir (default: dist/)")
    p_build.add_argument("--packs-dir", default=str(DEFAULT_PACKS_DIR))
    p_build.set_defaults(func=cmd_build)

    p_vendor = sub.add_parser(
        "vendor", help="정본 코덱을 소비자 repo 로 내보내기 / 갈렸는지 검사(--check)"
    )
    p_vendor.add_argument("--dest", required=True, help="소비자 패키지 디렉터리")
    p_vendor.add_argument("--check", action="store_true", help="쓰지 않고 대조만")
    p_vendor.set_defaults(func=cmd_vendor)

    p_market = sub.add_parser("market", help="generate .claude-plugin/marketplace.json")
    p_market.add_argument("--packs-dir", default=str(DEFAULT_PACKS_DIR))
    p_market.set_defaults(func=cmd_market)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
