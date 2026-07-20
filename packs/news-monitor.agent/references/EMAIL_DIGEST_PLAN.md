# 뉴스 브리핑 이메일 구독 — 설계 & 핸드오프 (news-monitor)

> 유저가 "키워드 등록 → 매일 아침 이메일로 브리핑 받기"를 **opt-in으로 선택**하는 기능.
> scholarship은 외부 consumer(Phedy)가 cron을 소유했지만, 이건 **schift 제품 유저 대상**이라
> schift-api가 구독·cron·발송을 직접 소유한다. 전부 기존 blog 인프라 재사용.

## 재사용 매핑 (새로 만들 게 거의 없음)

| 필요 | 재사용 원본 |
|------|-----------|
| 구독 테이블 + double opt-in + unsubscribe token | `schift-api/server/blog/models.py` `BlogSubscriber` 패턴 |
| SES 발송(HTML+Text multipart, DKIM, light-only 메일) | `schift-api/server/blog/service.py` boto3 SES |
| opt-in / confirm / unsubscribe 라우트 | `schift-api/server/routes/blog.py` |
| Cloud Scheduler cron | `infra/core/platform/platform-scheduler.tf` |
| X-Cron-Secret 보호 엔드포인트 | `schift-api/server/routes/jobs.py` 패턴 |
| 키워드 브리핑 생성(agentic-run, ReAct, fetch_news) | **이미 구현됨** — agent-hub facade 4콜 (scholarship `phedy_cron_client.py`와 동일 시퀀스) |

## 새 DB 테이블 — `news_monitor_subscriptions` (public schema)

`BlogSubscriber` 미러 + 뉴스 전용 필드:

| 컬럼 | 타입 | 비고 |
|------|------|------|
| id, email, created_at | — | blog와 동일 |
| org_id, user_id | str? | 제품 유저 귀속(로그인 유저). 비로그인 이메일-only도 허용 |
| keywords | JSON list[str] | 추적 키워드 |
| schedule | str | `daily_09kst` 등 (cron이 이 그룹 단위로 실행) |
| consent_marketing | int 0/1 | opt-in 동의 (정보통신망법 — 뉴스는 본인요청 정보성, [광고] 불필요) |
| confirmation_token | str? | 24h TTL, single-use (blog와 동일 burn) |
| unsubscribe_token | str? | 영구, 별개 값 |
| status | str | pending / confirmed / unsubscribed |
| seen_links | JSON list[str] | **멱등성 핵심** — 이미 보낸 originallink 누적(최근 N개 ring). 다음 run에 fetch_news `seen_links`로 주입 → 새 기사만 |
| last_sent_at | datetime? | 발송 이력 |

alembic revision 1개 (`20260619_create_news_monitor_subscriptions`). **prod 적용은 GO 후** (working tree에서 prod DB에 직접 도는 함정 주의 — [[project_landing_concierge_widget_streaming]]).

## opt-in 흐름 (유저가 "이메일로 받기" 선택)

```
1. 유저: 키워드 입력 + 이메일 + "매일 이메일로 받기" 체크 → POST /v1/news-monitor/subscribe
2. 서버: 행 생성(status=pending) + confirmation_token → SES로 확인 메일 발송
3. 유저: 확인 링크 클릭 → GET /v1/news-monitor/confirm?token=... → status=confirmed, token burn
4. (매일) Cloud Scheduler → POST /v1/news-monitor/cron/run (X-Cron-Secret)
     → confirmed 구독 그룹 순회:
        a. agent-hub facade agentic-run (news-monitor 팩, keywords + seen_links 주입)
        b. 브리핑 HTML 아티팩트 회수
        c. SES 발송 (light-only HTML + text, unsubscribe 링크 footer)
        d. seen_links 갱신(이번 originallink 합치고 ring 자름), last_sent_at
5. 해지: unsubscribe_token 링크 → status=unsubscribed
```

## 라우트 (신규, `schift-api/server/routes/news_monitor.py`)

- `POST /v1/news-monitor/subscribe` — {email, keywords[], schedule?} → 확인 메일
- `GET  /v1/news-monitor/confirm` — token → confirmed
- `GET  /v1/news-monitor/unsubscribe` — token → unsubscribed
- `POST /v1/news-monitor/cron/run` — X-Cron-Secret, 배치 실행 (per-subscription run+send)

## 빌링

브리핑 1회 = agentic-run 1회(LLM + fetch_news). 기존 통합 빌링(`SCHIFT_UNIFIED_RUN_BILLING`)으로
구독 소유 org에 차감. 비로그인 이메일-only 구독은 dogfood org 또는 무료 쿼터 정책 결정 필요(미결).

## 미결정 (GO 전 확인)

1. **발송 주기 옵션** — daily만 vs daily/weekly 선택 노출?
2. **비로그인 구독 허용 여부** + 그 경우 빌링 귀속(무료 한도/캡).
3. **키워드 수 상한** (구독당 5개? 빌링·발송 길이 영향).
4. **seen_links ring 크기** (최근 200개? 키워드×기간 따라).
5. UI 위치 — 앱 콘솔 news-monitor 실행 화면 내 "이메일로도 받기" 토글 vs 랜딩 별도 폼.

## 상태
설계 확정 · 부품 전부 확인됨. **구현(DB+cron+SES+라우트)은 GO 대기** — schift-api 대상,
prod DB 마이그레이션·Cloud Scheduler terraform apply 포함이라 건별 승인 후 진행.
