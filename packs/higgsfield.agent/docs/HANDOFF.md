# Higgsfield Directing Pack — 완료 기록

> 2026-07-10 기준 구현, OAuth 연결, production read-only MCP 검증, directing RAG 업로드와 배포를 완료했다. 유료 체험이나 생성 과금 호출은 실행하지 않았다.

## 0. 결론

`higgsfield`는 `Gemini txt2img grid → 승인 패널만 Higgsfield video → ffmpeg stitch` 흐름을 따르는 연출 전용 APM 팩이다.

- H1 공식 조사: 완료
- H2 Streamable HTTP와 동적 `tools/list`: 완료, production 200 확인
- H3 사용자별 OAuth PKCE/refresh lifecycle: 완료, production 연결 및 연속 refresh 확인
- H4 feature flag: 완료
- H5 Higgsfield txt2img backend: 선택 항목에서 제외, Gemini grid 유지
- H6 directing RAG: 완료, 전용 bucket 10/10 문서 ready
- H7 ffmpeg stitch job: 완료
- H8 승인 패널 mock flow: 완료

## 1. Production proof

### OAuth와 MCP

- APM package: `room821-higgsfield-agent@0.1.1`
- Public OAuth client: `QNP5mWUEMJILvoPG`
- Redirect: `https://connect.schift.io/oauth/higgsfield/callback`
- PKCE S256, secure HttpOnly verifier cookie, 사용자별 sealed refresh token을 사용한다.
- Schift Connect 화면에서 Room 821 사용자 연결을 완료했다.
- 유료 3일 체험은 선택하지 않고 `Skip & proceed to MCP`로 진행했다.
- Agent Hub는 토큰을 받지 않는다. 사용자·조직·run·session identity만 schift-api 내부 bridge에 전달한다.
- schift-api가 access token을 mint하고 `https://mcp.higgsfield.ai/mcp`를 호출한다.
- refresh grant가 새 refresh token을 반환하면 같은 사용자 전용 vault reference에 즉시 덮어쓴다.
- production `tools/list`를 연속 2회 호출해 모두 HTTP 200, 72 tools를 확인했다. 두 번째 호출도 성공해 refresh rotation 보존을 검증했다.

확인된 video 입력 계약:

1. 승인 패널 URL을 `media_import_url({url, type: "image"})`로 가져온다.
2. 반환된 `media_id`를 `generate_video.params.medias[]`의 `{value, role: "start_image"}`로 전달한다.
3. `generate_video` 입력은 `{params: {model, prompt, medias, duration, aspect_ratio, get_cost}}` 형태다.
4. 생성 전 `get_cost: true`로 provider credit preflight를 실행한다.

이 계약은 `src/agent_hub/higgsfield_clip_adapter.py`와 `tests/test_higgsfield_flow.py`에 고정했다.

### Directing RAG

- Bucket name: `higgsfield-directing`
- Bucket ID: `cf881f88e1cd491e944fa199f0eaf7c1`
- 10개 seed 문서가 모두 `ready` 상태이며 업로드 hash가 로컬 source와 일치한다.
- 실제 bucket ID를 아래 세 surface에 동일하게 반영했다.
  - `src/agent_hub/higgsfield_assets.py`
  - `src/agent_hub/agent_packs.py`
  - `apm/higgsfield.agent/apm.yml`

## 2. 구현 경계

- `src/agent_hub/mcp_client.py`: initialize, initialized notification, session ID, negotiated protocol, JSON/SSE `tools/list`/`tools/call`
- `src/agent_hub/higgsfield_mcp_proxy.py`: schift-api 내부 bridge 호출
- `src/agent_hub/mcp_tool_registry.py`: production schema 기반 동적 tool 등록
- `src/agent_hub/higgsfield_clip_adapter.py`: 승인 패널 URL import와 실제 `generate_video.params` 변환
- `src/agent_hub/higgsfield_stitch.py`: 승인 순서 보존 stitch job
- `apm/higgsfield.agent/scripts/upload_higgsfield_rag.py`: 전용 bucket seed uploader

## 3. 안전 경계

- 실제 video/image generation, Soul training, 결제·체험 시작은 별도 명시 승인 없이는 실행하지 않는다.
- 생성 전 provider cost preflight를 사용한다.
- 승인되지 않은 패널은 video 생성에 전달하지 않는다.
- provider token, refresh token, MCP session detail은 Agent Hub나 사용자 화면에 노출하지 않는다.
- canonical directing 지식은 `default`나 `agent-hub-session-memory`가 아니라 `higgsfield-directing`만 사용한다.
- H5는 완료 범위에서 제외했다. grid 기본 backend는 Gemini다.

## 4. 검증

```bash
cd /Users/jskang/Projects/schift/services/agent-hub

.venv/bin/python -m pytest \
  tests/test_mcp_client.py \
  tests/test_higgsfield_stitch.py \
  tests/test_higgsfield_flow.py \
  tests/test_upload_higgsfield_rag.py \
  tests/test_pack_manifest.py \
  tests/test_apm_pipeline_declaration.py \
  tests/test_config_contract.py \
  tests/test_subagent_inloop_tools.py -q
```

완료 증거:

- Agent Hub Higgsfield transport/flow 집중 검증 통과
- schift-api OAuth/MCP bridge 집중 검증 통과
- production API health 200
- production `/v1/auth/me` 200
- production Higgsfield OAuth 연결 완료
- production `tools/list` 연속 2회 HTTP 200, 72 tools
- `higgsfield-directing` 10/10 ready
- Agent Hub, API, web/connect production 배포 완료

남은 Higgsfield TODO는 없다.
