#!/usr/bin/env bash
# AgentPackage → schift-io/apm-spec 단방향 복사. **손으로 돌린다.**
#
# CI 로 안 하는 이유: 다른 저장소에 push 하려면 GITHUB_TOKEN 으로 안 되고 별도
# 토큰(SYNC_TOKEN)을 시크릿으로 상주시켜야 한다. SPEC.md·kit/ 는 거의 안 변하는데
# (2026-08-10 이 사실상 첫 변경) 그 빈도를 위해 "다른 저장소에 쓸 수 있는 권한"을
# CI 에 두고 만료·회전까지 관리하는 건 남는 장사가 아니다. 오너 결정(2026-08-10).
#
# 나가는 것만 명시적으로 복사한다(allow-list). deny-list 로 하면 나중에 추가되는
# 파일이 **기본값으로 따라 나간다**.
#   나간다:   SPEC.md · LICENSE · docs/runtime-adapter.md ·
#             kit/{apm_codec,apm_kit,capabilities.json} · examples/** ·
#             mirror/README.md → README.md · mirror/gitignore → .gitignore
#   안 나간다: identity-patterns.json(정체성 문자열 자체) · kit/publish.py(사내 발행
#             인프라, 포맷 아님) · packs/** · dist/** · .github/**
#
# 사용:
#   scripts/sync-apm-spec.sh            # 조립 + 게이트까지만 (기본값, push 안 함)
#   scripts/sync-apm-spec.sh --push     # 게이트 통과 시 apm-spec 에 push
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="$(mktemp -d)/out"
PUSH=0
[[ "${1:-}" == "--push" ]] && PUSH=1

cd "$REPO_ROOT"

# ── 1. 조립 ────────────────────────────────────────────────────────────────
mkdir -p "$STAGE/kit" "$STAGE/docs"
cp SPEC.md LICENSE "$STAGE/"
cp mirror/README.md "$STAGE/README.md"
cp mirror/gitignore "$STAGE/.gitignore"
cp docs/runtime-adapter.md "$STAGE/docs/runtime-adapter.md"
cp kit/apm_codec.py kit/apm_kit.py kit/capabilities.json "$STAGE/kit/"
cp -R examples "$STAGE/examples"
find "$STAGE" -name __pycache__ -type d -prune -exec rm -rf {} +
echo "조립: $STAGE ($(find "$STAGE" -type f | wc -l | tr -d ' ') files)"

# ── 2. 정체성 게이트 (fail-closed) ─────────────────────────────────────────
# 팩 안 .md/.yml 만 보는 apm-kit lint 로는 SPEC 본문·README·경로명이 안 잡힌다.
# 2026-08-10 에 같은 실수를 네 번 했다: 소스 하드코딩 → kit/ 안 배치 → SPEC 본문
# 복사 → 커밋 저자 메일. 셋은 grep 축이 서로 달랐고 lint 는 넷 다 못 잡았다.
[[ -f identity-patterns.json ]] || { echo "identity-patterns.json 없음 — 검사할 패턴이 없으면 미러하지 않는다."; exit 1; }
STAGE="$STAGE" python3 - <<'PY'
import json, os, re, sys
from pathlib import Path

stage = Path(os.environ["STAGE"])
patterns = json.loads(Path("identity-patterns.json").read_text(encoding="utf-8"))["patterns"]
hits = []
for path in sorted(stage.rglob("*")):
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(stage)
    for entry in patterns:
        if re.search(entry["pattern"], text):
            hits.append(f"{rel}: {entry['label']}")
        # 경로명에도 건다 — 내용만 보면 "어디에 뒀는가"가 사각지대다.
        if re.search(entry["pattern"], str(rel)):
            hits.append(f"{rel} (경로): {entry['label']}")
if hits:
    print("정체성 잔존 — 미러 중단:")
    for hit in hits:
        print(f"  ✗ {hit}")
    sys.exit(1)
print(f"✓ 정체성 0건 ({len(patterns)} 패턴 × 전 파일)")
PY

# ── 3. kit 이 packs 없이 자립적으로 도는지 ─────────────────────────────────
(
  cd "$STAGE"
  python3 kit/apm_kit.py lint higgsfield-demo.agent --packs-dir examples
  # local-byo 에서는 능력 부족으로 거절되는 것이 정상 — 통과하면 시연이 깨진 것이다.
  if python3 kit/apm_kit.py check higgsfield-demo.agent --host local-byo --packs-dir examples; then
    echo "✗ 예시 팩이 local-byo 에서 통과했다 — fail-closed 시연이 깨졌다."
    exit 1
  fi
  python3 kit/apm_kit.py check higgsfield-demo.agent --host agent-hub --packs-dir examples
  python3 kit/apm_kit.py build higgsfield-demo.agent --packs-dir examples --out "$(mktemp -d)"
)

if [[ "$PUSH" -eq 0 ]]; then
  echo
  echo "게이트 통과. push 하려면: $0 --push"
  exit 0
fi

# ── 4. push ────────────────────────────────────────────────────────────────
CLONE="$(mktemp -d)/apm-spec"
git clone -q https://github.com/schift-io/apm-spec.git "$CLONE"
# 추적 파일을 지우고 스테이징으로 덮는다 — 저쪽에만 있는 파일은 사라져야 단방향이다.
(cd "$CLONE" && git ls-files -z | xargs -0 rm -f)
cp -R "$STAGE"/. "$CLONE"/
cd "$CLONE"
if git diff --quiet && git diff --cached --quiet && [[ -z "$(git status --porcelain)" ]]; then
  echo "변경 없음 — push 생략."
  exit 0
fi
git add -A
git -c user.name='Schift' -c user.email='hello@schift.io' \
  commit -q -m "sync from AgentPackage@$(cd "$REPO_ROOT" && git rev-parse --short HEAD)"
git push -q origin main
echo "✓ pushed → schift-io/apm-spec"
