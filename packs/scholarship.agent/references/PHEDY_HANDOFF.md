# Phedy 연동 핸드오프 — 장학금 다이제스트 (scholarship agent)

> 대상: Phedy 백엔드 담당. 이 문서 하나로 cron 장학금 다이제스트를 붙일 수 있다.

## 한 줄 요약

Schift agent-hub에 **장학금 검색 에이전트(`scholarship`)**가 올라갔다. 학생 프로필을 주면
한국장학재단·대학·재단·기업 **공식 공고를 실시간 웹검색으로 그라운딩**해서, "지금 지원
가능 / 곧 열림 / 마감"으로 분류한 다이제스트를 만들어준다. **Phedy가 프로필을 보관하고
cron으로 호출 → 받은 다이제스트를 저장·노출**하면 된다. (Schift 쪽 추가 인프라 없음)

## Phedy가 구현할 것 (전부 Phedy repo)

1. **학생 프로필 저장** — 학교·학년·전공·GPA·소득분위(아는 만큼). 한 줄 자연어면 충분.
2. **cron** — 예: 매일 또는 주 1회. 학생/그룹별로 아래 시퀀스 1회 호출.
3. **다이제스트 저장** — 호출이 돌려주는 JSON payload를 DB에 저장.
4. **인앱 노출** — `digest_html`(바로 렌더) 또는 `digest_markdown` 표시.

## 인증 — 외부용 SCHIFT API Key (facade 경유, 권장)

Phedy는 agent-hub 내부 시크릿을 만지지 않는다. **공개 Schift API(`api.schift.io`)의
agent-hub facade**를 통해 호출하고, **SCHIFT API Key**로 인증한다:

- 엔드포인트 베이스: `https://api.schift.io/v1/agent-hub` (이 prefix 뒤에 세션 경로가 붙음)
- 헤더: `Authorization: Bearer <SCHIFT_API_KEY>`
- 필요한 key scope: **`agents:documents:run`** (포함). dogfood 키는 `*`(전체) scope로 발급됨.
- **발급 완료 (2026-06-14, dogfood)**: org `org_room821`(Room 821), key_id `key_cf94bd4df081`,
  preview `sch_vnKaSS...OGUE`, 365일. **raw 키는 GCP Secret Manager `phedy-scholarship-api-key`**
  (`gcloud secrets versions access latest --secret=phedy-scholarship-api-key --project=schift`).
  Phedy 배포는 이 시크릿을 참조. (dogfood라 `*` scope — 외부 고객엔 `agents:documents:run`만 발급할 것)
- facade가 내부 shared-secret + Cloud Run ID 토큰을 서버사이드로 주입하므로 Phedy는
  API key 하나만 관리하면 된다. 키는 발급자(org/user) 레이어로 행동한다.
- facade가 API key에 열어주는 경로는 **run 라이프사이클 최소 집합**(아래 4콜 + agents/config/intake)
  뿐이라, 키가 유출돼도 세션관리·메모리열람 같은 표면은 막혀 있다.

## 호출 시퀀스 (기존 세션 API 4콜, 새 엔드포인트 없음)

```
POST https://api.schift.io/v1/agent-hub/v1/sessions/{sid}/bootstrap
POST https://api.schift.io/v1/agent-hub/v1/sessions/{sid}/memory:append   # 학생 프로필 주입
POST https://api.schift.io/v1/agent-hub/v1/sessions/{sid}/agentic-runs     # 실행 (KST 날짜·웹검색 자동)
GET  https://api.schift.io/v1/agent-hub/v1/sessions/{sid}/artifacts         # 다이제스트 md/html 회수
```

- 전부 `Authorization: Bearer <SCHIFT_API_KEY>` 헤더.
- `sid` = `{tenant}:scholarship:{user}:{conversation_id}` 형식 (예시 참고).
- **레퍼런스 구현**: [`phedy_cron_client.py`](./phedy_cron_client.py) — 이 4콜을 그대로 담은
  파이썬. Phedy 스택(Node 등)으로 포팅하거나 그대로 cron에 걸어도 됨.

> 내부망(같은 GCP project) 직결이 필요하면 agent-hub 사설 URL + `X-Room821-Agent-Hub-Secret`
> 직호출도 가능하지만, **외부 제품(Phedy)은 facade + API key 경로를 쓴다.**

### 프로필 주입 형식 (memory:append body)

```json
{
  "tenant_id": "...", "agent_id": "scholarship", "user_id": "...", "conversation_id": "...",
  "role": "user", "kind": "fact",
  "content_redacted": "source_document:student_profile: 학생 조건: 생화학과 3학년, GPA 3.6/4.3, 소득분위 5구간 ...",
  "tags": ["memory:source-document", "source:student-profile"]
}
```

## 돌려받는 payload (Phedy가 저장할 모양)

```json
{
  "generated_at_kst": "2026-06-14T01:30:23+09:00",
  "run_id": "run_...", "status": "ok",
  "profile": "학생 조건: ...",
  "digest_markdown": "# 장학금 다이제스트\n...",   // 인앱 표시용
  "digest_html": "<...>",                          // 바로 렌더 가능
  "usage": { "billed_cost_usd": 0.003, ... }       // 회당 약 $0.003
}
```

다이제스트 구조: ① 검색조건 요약 ② 한국장학재단 공고 ③ 학교·재단·기업 공고
④ 상태분류(지금가능/곧열림/마감, 마감임박 D-7 최상단) ⑤ 적격성+다음행동.

## 정확도를 높이려면 (프로필에 넣을수록 좋음)

- **학교**: 교내장학금은 학교별이라, 학교를 주면 그 학교 공지를 우선 검색한다.
  미지정이면 여러 학교 교내장학금이 예시로 섞여 나오니, **"본인이 해당 학교 재학 시"**로
  안내하는 게 안전.
- **소득분위(학자금 지원구간)**: 국가장학금·지자체 지원의 핵심 자격 기준.
- GPA·전공·학년: 적격성 판정에 사용.

## 반드시 지켜야 할 것 (안전 계약)

- 다이제스트의 **금액·기간·자격은 공식 공고에서 최종 확인**해야 한다. 봇은 공식 출처
  URL을 함께 주니, 인앱에서 "원문 확인" 링크로 노출할 것. (`[확인 필요]` 표기 존중)
- 봇은 **신청·제출을 대신하지 않는다.** "어디에 무엇을" 안내까지만. 신청은 학생 본인.
- 마감/지원가능 분류는 KST 오늘 기준 자동 계산되지만, **마감 임박 건은 원문 재확인** 권장.

## 운영 메모

- prod agent-hub에서 이 팩은 **기본 OFF(베타)**. 켜려면 운영팀이 `AGENT_HUB_FEATURE_SCHOLARSHIP=1`.
- 데이터 소스 = 라이브 웹검색(MVP). "지난번 대비 새 공고만" 같은 diff가 필요해지면
  크롤러+버킷으로 승격 예정(그때 payload는 호환 유지).
- 회당 비용 ~$0.003 (학생 수 × cron 빈도로 추산).
