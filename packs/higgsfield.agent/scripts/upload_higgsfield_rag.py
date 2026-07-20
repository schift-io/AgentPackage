#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# ─── How to run ───
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Preview without network access (default):
#      uv run upload_higgsfield_rag.py
# 3. Upload only after explicit approval:
#      uv run upload_higgsfield_rag.py --live \
#        --confirm-live-upload upload-higgsfield-directing
# ──────────────────
from __future__ import annotations

import runpy


if __name__ == "__main__":
    runpy.run_module("higgsfield_rag.cli", run_name="__main__")
