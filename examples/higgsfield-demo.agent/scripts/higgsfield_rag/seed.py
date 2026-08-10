from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

DEFAULT_BUCKET: Final = "higgsfield-directing"
LIVE_CONFIRMATION: Final = "upload-higgsfield-directing"
DEFAULT_SOURCE_ROOT: Final = (
    Path(__file__).resolve().parents[2] / "knowledge" / "rag-sources"
)
REQUIRED_KINDS: Final[frozenset[str]] = frozenset(
    (
        "shot_grammar camera_movement lighting_preset mood_grade lens_focus "
        "anchor_template edit_rhythm negative_anti_slop composition_recipe "
        "channel_aspect"
    ).split()
)
MAX_METADATA_BYTES: Final = 4 * 1024
SAFE_KEY: Final = re.compile(r"^[A-Za-z0-9_.\-]+$")
CONTROL_CHAR: Final = re.compile(r"[\x00-\x1f\x7f]")
RESERVED_KEYS: Final = frozenset(
    "bucket_id chunk_id document_id file_name source_kind source_path status text".split()
)
SERVER_POLICY_KEYS: Final = frozenset(
    "classification internal_accessible owner_department privacy_level "
    "public_accessible review_status scope uploaded_by_user_id".split()
)


class SeedContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SeedDocument:
    file_name: str
    kind: str
    source_id: str


SEED_DOCUMENTS: Final[tuple[SeedDocument, ...]] = (
    SeedDocument("01-shot-grammar.md", "shot_grammar", "hf://shot/grammar-001"),
    SeedDocument(
        "02-camera-movement.md",
        "camera_movement",
        "hf://movement/dolly-in-001",
    ),
    SeedDocument(
        "03-lighting-preset.md",
        "lighting_preset",
        "hf://lighting/window-side-001",
    ),
    SeedDocument("04-mood-grade.md", "mood_grade", "hf://grade/warm-tungsten-001"),
    SeedDocument("05-lens-focus.md", "lens_focus", "hf://lens/35mm-shallow-001"),
    SeedDocument(
        "06-anchor-template.md",
        "anchor_template",
        "hf://anchor/identity-lock-001",
    ),
    SeedDocument("07-edit-rhythm.md", "edit_rhythm", "hf://edit/match-cut-001"),
    SeedDocument(
        "08-negative-anti-slop.md",
        "negative_anti_slop",
        "hf://negative/video-001",
    ),
    SeedDocument(
        "09-composition-recipe.md",
        "composition_recipe",
        "hf://composition/copy-safe-001",
    ),
    SeedDocument(
        "10-channel-aspect.md",
        "channel_aspect",
        "hf://channel/aspect-001",
    ),
)


def collect_documents(root: Path) -> list[SeedDocument]:
    missing = [
        seed.file_name
        for seed in SEED_DOCUMENTS
        if not (root / seed.file_name).is_file()
    ]
    if missing:
        raise FileNotFoundError(f"Missing Higgsfield RAG seeds: {', '.join(missing)}")
    for seed in SEED_DOCUMENTS:
        text = (root / seed.file_name).read_text(encoding="utf-8")
        if f'"kind": "{seed.kind}"' not in text:
            raise SeedContractError(
                f"Seed kind mismatch: {seed.file_name} must contain {seed.kind}"
            )
    kinds = {seed.kind for seed in SEED_DOCUMENTS}
    if kinds != set(REQUIRED_KINDS):
        raise SeedContractError(
            f"Directing ontology coverage mismatch: {sorted(kinds)}"
        )
    return list(SEED_DOCUMENTS)


def build_metadata(
    seed: SeedDocument,
    *,
    path: Path,
    root: Path,
    bucket: str,
    batch_id: str,
) -> dict[str, str]:
    stat = path.stat()
    return {
        "agent_hub_bucket_role": "directing_reference",
        "agent_hub_contract": "HIGGSFIELD_DIRECTING_RAG_BUCKET",
        "agent_hub_default_bucket": DEFAULT_BUCKET,
        "agent_hub_schema": "higgsfield_directing_rag.v1",
        "memory_scope": "directing_reference",
        "memory_kind": "directing_reference",
        "source_group": "higgsfield-directing-ontology",
        "directing_kind": seed.kind,
        "source_id": seed.source_id,
        "source_rel_path": str(path.relative_to(root)),
        "source_ext": path.suffix.lower().lstrip(".") or "none",
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_mtime_utc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
        "source_bytes": str(stat.st_size),
        "seed_batch": batch_id,
        "canonicality": "reference",
        "product_area": "higgsfield",
        "locale": "ko-KR",
        "rag_bucket": bucket,
    }


def validate_metadata(metadata: dict[str, str]) -> None:
    encoded = json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode()
    if len(encoded) > MAX_METADATA_BYTES:
        raise SeedContractError(f"metadata exceeds {MAX_METADATA_BYTES} bytes")
    for key, value in metadata.items():
        if not SAFE_KEY.fullmatch(key):
            raise SeedContractError(f"metadata key is not API-safe: {key}")
        if key.startswith("schift.") or key in RESERVED_KEYS:
            raise SeedContractError(f"metadata key is reserved by Schift: {key}")
        if key in SERVER_POLICY_KEYS:
            raise SeedContractError(
                f"metadata key is server-stamped access policy: {key}"
            )
        if len(key) > 64 or len(value) > 512 or CONTROL_CHAR.search(value):
            raise SeedContractError(f"metadata value is invalid: {key}")


def require_live_confirmation(*, live: bool, confirmation: str | None) -> bool:
    if not live:
        return True
    if confirmation != LIVE_CONFIRMATION:
        message = (
            "Live upload refused. Pass --confirm-live-upload "
            f"{LIVE_CONFIRMATION} only after user approval."
        )
        raise SystemExit(message)
    return False
