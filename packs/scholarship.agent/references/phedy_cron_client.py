#!/usr/bin/env python3
"""Phedy 측 cron 레퍼런스 클라이언트 — 장학금 다이제스트 (전달 방식 'A').

이 파일은 agent-hub 런타임이 아니라 **Phedy 백엔드가 구현할 cron 호출 시퀀스의
레퍼런스**다. agent-hub는 stateless이므로, Phedy가:
  1) 학생 프로필을 보관하고
  2) 스케줄(예: 매일 09시)에 이 시퀀스로 agent-hub 세션 API를 호출해
  3) 받은 다이제스트를 Phedy DB에 저장 → 인앱에 노출
한다. agent-hub/schift-api에 새 코드·배포 불필요(팩만 켜면 됨).

호출 시퀀스 (전부 기존 세션 API):
  POST /v1/sessions/{sid}/bootstrap
  POST /v1/sessions/{sid}/memory:append   (학생 프로필 주입)
  POST /v1/sessions/{sid}/agentic-runs     (KST 날짜·웹검색 그라운딩은 서버가 자동)
  GET  /v1/sessions/{sid}/artifacts         (다이제스트 md/html 회수)

인증 (택1):
  SCHIFT_API_KEY            **권장(외부 제품)**: facade(api.schift.io/v1/agent-hub) 경유.
                            scope `agents:documents:run` 키. Authorization: Bearer 로 전송.
  ROOM821_AGENT_HUB_SHARED_SECRET  내부망 직결 시: X-Room821-Agent-Hub-Secret 헤더.

환경변수:
  AGENT_HUB_BASE_URL        호출 베이스. 기본 = facade `https://api.schift.io/v1/agent-hub`.
                            (로컬 직결 테스트는 http://127.0.0.1:8090 로 오버라이드)
  SCHOLARSHIP_PROFILE       학생 조건 한 줄 (없으면 샘플)

사용:
  SCHIFT_API_KEY=sk-... python3 phedy_cron_client.py    # 1회 실행 → digest JSON stdout
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

BASE_URL = os.getenv("AGENT_HUB_BASE_URL", "https://api.schift.io/v1/agent-hub").rstrip("/")
SCHIFT_API_KEY = os.getenv("SCHIFT_API_KEY", "")
SHARED_SECRET = os.getenv("ROOM821_AGENT_HUB_SHARED_SECRET", "")
TENANT_ID = os.getenv("SCHOLARSHIP_TENANT_ID", "room821")
USER_ID = os.getenv("SCHOLARSHIP_USER_ID", "phedy_student_demo")
TIMEOUT = int(os.getenv("AGENT_RUN_TIMEOUT_SECONDS", "600"))

DEFAULT_PROFILE = (
    "학생 조건: 서울 소재 4년제 공과대학 2학년 재학생, 컴퓨터공학 전공, "
    "직전 학기 GPA 3.8/4.5, 학자금 지원구간(소득분위) 5구간. "
    "이번 학기 신청 가능한 장학금 다이제스트를 만들어줘."
)


def _request(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"}
    if SCHIFT_API_KEY:
        headers["Authorization"] = f"Bearer {SCHIFT_API_KEY}"
    if SHARED_SECRET:
        headers["X-Room821-Agent-Hub-Secret"] = SHARED_SECRET
    req = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    with urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_digest(profile: str) -> dict:
    """1회 다이제스트 생성. Phedy가 cron tick마다 호출하고 결과를 저장한다."""
    conversation_id = f"phedy_scholarship_{int(time.time())}"
    envelope = {
        "tenant_id": TENANT_ID,
        "agent_id": "scholarship",
        "user_id": USER_ID,
        "conversation_id": conversation_id,
    }
    session_id = f"{TENANT_ID}:scholarship:{USER_ID}:{conversation_id}"

    _request("POST", f"/v1/sessions/{session_id}/bootstrap", {**envelope})
    _request(
        "POST",
        f"/v1/sessions/{session_id}/memory:append",
        {
            **envelope,
            "role": "user",
            "kind": "fact",
            "content_redacted": f"source_document:student_profile: {profile}",
            "tags": ["memory:source-document", "source:student-profile"],
        },
    )
    run = _request("POST", f"/v1/sessions/{session_id}/agentic-runs", {**envelope})
    artifacts = _request("GET", f"/v1/sessions/{session_id}/artifacts")

    digest_md = digest_html = ""
    for art in artifacts:
        if art["artifact_id"] == run.get("markdown_artifact_id"):
            digest_md = art["content"]
        elif art["artifact_id"] == run.get("html_artifact_id"):
            digest_html = art["content"]

    kst_now = datetime.now(timezone(timedelta(hours=9))).isoformat()
    # Phedy가 DB에 저장할 페이로드.
    return {
        "generated_at_kst": kst_now,
        "tenant_id": TENANT_ID,
        "user_id": USER_ID,
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "profile": profile,
        "digest_markdown": digest_md,
        "digest_html": digest_html,
        "usage": run.get("usage_summary", {}),
    }


def main() -> None:
    profile = os.getenv("SCHOLARSHIP_PROFILE", DEFAULT_PROFILE)
    payload = run_digest(profile)
    # stdout = Phedy가 받아서 저장할 JSON (digest_html은 길이만 표기해 로그 간결화).
    summary = {**payload, "digest_html": f"<{len(payload['digest_html'])} chars>"}
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    print()
    if payload["status"] != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
