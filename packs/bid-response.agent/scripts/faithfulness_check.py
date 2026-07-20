#!/usr/bin/env python3
"""bid-response.agent faithfulness 게이트 — shim.

단일 정본은 `src/agent_hub/faithfulness_gate.py`(로직 이중화 금지). 이 스크립트는
apm.yml의 faithfulness-check 스킬이 참조하는 경로(`scripts/faithfulness_check.py`)와
기존 테스트(`services/agent-hub/tests/test_faithfulness_check.py`, 이 파일을
`sys.path` 경유로 import)를 그대로 유지하기 위한 re-export일 뿐이다. 실제
런타임 dispatch(post-react-run 배선)는 `agent_hub.bid_response_faithfulness`가
`agent_hub.faithfulness_gate.apply_gate`를 직접 호출한다.
"""
from __future__ import annotations

from agent_hub.faithfulness_gate import (
    GateResult,
    JudgeFn,
    NumericClaim,
    Violation,
    _normalize_number,
    apply_gate,
    build_allowed_numbers,
    extract_numeric_claims,
    find_violations,
    judge_violations,
)

__all__ = [
    "GateResult",
    "JudgeFn",
    "NumericClaim",
    "Violation",
    "apply_gate",
    "build_allowed_numbers",
    "extract_numeric_claims",
    "find_violations",
    "judge_violations",
]
