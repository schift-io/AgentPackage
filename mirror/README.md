# Agent Package (`.apm`)

에이전트 팩을 **봉인된 아티팩트 하나**로 유통하는 포맷. `.zip` 처럼 파일까지 통째로
봉인하고, content-hash 가 곧 주소이며, **요구하는 호스트 능력을 스스로 선언**한다.

- **[`SPEC.md`](SPEC.md) 가 규범적 사양이다.** 여기 적힌 것과 구현이 다르면 구현이 버그다.
- 참조 구현: [`kit/`](kit) — `apm_codec.py`(컨테이너·해시) · `capabilities.json`(능력 어휘) ·
  `apm_kit.py`(검증·빌드 CLI). stdlib + PyYAML 만 쓴다.
- 예시: [`examples/higgsfield-demo.agent`](examples) — 능력 협상·스크립트·스킬을 한 팩에서.
- 라이선스: Apache-2.0.

> ⚠️ **이름 충돌.** 여기서 APM 은 **Agent Package** — 봉인 아티팩트 포맷이다.
> [`microsoft/apm`](https://github.com/microsoft/apm)("Agent Package Manager", npm 식
> 의존성 관리자)과 **무관하며 코드·스키마 어느 쪽도 참조하지 않는다.**

## 왜 스킬 폴더가 아닌가

**스킬은 에이전트가 *참조*하는 것이고, 팩은 에이전트가 *그 위에서 도는* 것이다.**

참조 자료는 우아하게 열화한다 — 파일 하나 없으면 답이 조금 나빠진다. 실행 정의는
**조용히 오작동**한다 — 파일 하나 없으면 틀린 행동을 한다. 메일을 보내고, 문서를
제출하고, 돈을 쓴다. 그래서 실행 단위에는 참조 자료에 없던 요구가 생긴다.

**능력 협상이 핵심이다.** "이 호스트가 이 팩이 시도할 일을 실제로 할 수 있나"를 실행
전에 묻고, 못 채우면 **fail-closed 로 거절**한다. 두 호스트 체제(클라우드 / 로컬)에서
가장 위험한 실패 모드는 크래시가 아니라 **조용히 반쯤 도는 것**이다.

```
$ python3 kit/apm_kit.py check higgsfield-demo.agent --host local-byo --packs-dir examples
✗  higgsfield-demo.agent: host 'local-byo' lacks ['higgsfield_mcp', 'stitch_worker', 'usage_ledger']

$ python3 kit/apm_kit.py check higgsfield-demo.agent --host agent-hub --packs-dir examples
✓  higgsfield-demo.agent: satisfied by agent-hub (8 caps)
```

## 빠르게 해보기

```bash
pip install pyyaml

python3 kit/apm_kit.py lint  higgsfield-demo.agent --packs-dir examples
python3 kit/apm_kit.py build higgsfield-demo.agent --packs-dir examples --out /tmp/out
# → 30 files, 43191 bytes, hash 95abd2a904a8f639…
```

같은 입력은 **바이트 단위로 같은 `.apm`** 을 낸다(gzip mtime=0, tar 메타 고정, 경로
정렬, canonical JSON). 결정성이 깨지면 content-hash 가 주소로서 쓸모없어지기 때문이다.

## 상태

- **v1.** 포맷 버전은 해시 접두사 `apm-v1` 이 들고 있다.
- **서명은 아직 없다.** content-hash 는 변조를 잡지만 **출처를 증명하지 못한다.**
  제3자 팩을 받기 시작하는 순간 서명이 함께 필요하다 — `SPEC.md` §9.
- 이 저장소는 **파생**이다. 정본은 사내 `schift-io/AgentPackage` 의 `SPEC.md`·`kit/`
  이고 여기로 단방향 복사된다. 이슈/PR 은 받되 반영은 정본에서 이뤄진다.
