# APM registry release provenance v1

## 범위

`apm.release.v1`은 registry가 sealed `.apm` artifact를 특정 조직과 실행 권한으로
발행했다는 사실을 증명하는 선택적 release receipt profile이다. `.apm` 포맷과 content
hash 식은 그대로이고, receipt는 artifact 밖 registry ref에 붙는다.

Private 또는 corporate release를 실행하는 Runtime은 registry authorization과 receipt
검증을 둘 다 통과해야 한다. 어느 하나라도 없거나 맞지 않으면 실행하지 않는다.

## 서명 대상

Registry는 다음 JSON object를 UTF-8, key sort, `,`와 `:` separator로 canonicalize한 뒤
Ed25519로 서명한다. `signature`는 base64이며 `key_id`는 Runtime이 설정한 trusted public
key를 고르는 식별자다.

```json
{
  "protocol": "apm.release.v1",
  "issuer": "<registry issuer>",
  "key_id": "<issuer key id>",
  "release_id": "<immutable release id>",
  "agent_id": "<agent id>",
  "version": "<semver>",
  "content_hash": "<apm-v1 sha256 hex>",
  "r2_key": "<opaque registry artifact object key>",
  "visibility": "private|corporate|public",
  "allowed_orgs": ["<org id>"],
  "owner_org": "<publisher org id>",
  "uploaded_by": "<publisher principal id>",
  "issued_at": "<RFC3339 UTC timestamp>"
}
```

`r2_key`는 v1 field name이지만 object store provider를 뜻하지 않는다. Runtime은 이를
opaque locator로 비교만 하고 해석하지 않는다. recipient 목록은 중복 없이 lexical order로
정규화한다. public release는 빈 목록을 사용한다.

## Immutable release rule

`agent_id@version`은 release identity다. 이미 존재하는 identity는 다음 필드를 바꿀 수
없다: content hash, object key, visibility, allowed organizations, owner, uploader, receipt.
동일한 값의 재시도만 기존 receipt를 그대로 돌려준다. 내용, recipient, visibility 또는
provenance를 바꾸려면 새 version을 발행한다.

## Runtime verification

1. Runtime은 caller 조직으로 exact registry ref를 resolve하고 registry authorization을
   확인한다.
2. configured `key_id` public key로 receipt signature를 확인한다.
3. receipt claim의 identity, version, content hash, object key, visibility, recipients,
   owner, uploader를 resolved ref와 정확히 비교한다.
4. private/corporate release는 caller 조직이 `allowed_orgs`에 있는지 확인한다.
5. 검증된 hash의 `.apm`을 내려받아 package integrity와 runtime capability/sandbox
   contract를 별도로 확인한 뒤에만 실행한다.

Legacy unsigned public release는 migration 기간에만 허용할 수 있다. Runtime은 strict
deployment setting으로 unsigned public release까지 거절할 수 있어야 한다.

## 수정과 재발행

`extract`는 artifact를 편집 가능한 source로 복원한다. `fork`는 새 agent identity와
version을 선언한다. 어느 경우에도 원 receipt를 복사하거나 재사용하면 안 된다. source를
수정·build한 뒤 registry에 새 immutable release로 push해 새 receipt를 받아야 한다.
