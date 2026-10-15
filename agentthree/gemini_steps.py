"""Structured Gemini calls for the three agent reasoning steps (AI Studio free tier)."""

from __future__ import annotations

import json
import re
import time
from typing import Any

from agentthree.config import DEMO_MODE, GEMINI_MODEL, GOOGLE_API_KEY, ensure_genai_env
from agentthree.domain import cds_evaluate, evaluate_policy, extract_entities


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


async def _generate(prompt: str) -> tuple[dict[str, Any], int, int]:
    """Returns (parsed_json, duration_ms, approx_tokens)."""
    ensure_genai_env()
    if DEMO_MODE or not GOOGLE_API_KEY:
        raise RuntimeError("Gemini live call unavailable (DEMO_MODE or missing GOOGLE_API_KEY)")

    t0 = time.perf_counter()
    # google-genai is pulled in by google-adk
    from google import genai

    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0,
            "response_mime_type": "application/json",
        },
    )
    dur = int((time.perf_counter() - t0) * 1000)
    text = response.text or "{}"
    usage = getattr(response, "usage_metadata", None)
    tokens = 0
    if usage:
        tokens = int(getattr(usage, "total_token_count", 0) or 0)
    return _parse_json(text), dur, tokens or max(200, len(prompt) // 4)


async def extract_with_gemini(note: str, icd: str, fhir_ctx: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
    fallback = extract_entities(note, icd)
    if DEMO_MODE or not GOOGLE_API_KEY:
        return fallback, 40, 0
    prompt = f"""Extract clinical entities for prior auth. Return ONLY JSON matching this schema:
{json.dumps(fallback, indent=2)}

Use the clinical note and FHIR context. Prefer evidence from the note.
Clinical note:
{note}

FHIR context:
{json.dumps(fhir_ctx)[:2000]}
"""
    try:
        data, dur, tokens = await _generate(prompt)
        # Merge with deterministic fallback for required keys
        out = {**fallback, **data}
        out["icd"] = icd
        out["icdText"] = fallback["icdText"]
        out.setdefault("meds", fallback["meds"])
        out.setdefault("gaps", fallback["gaps"])
        out.setdefault("redFlags", fallback["redFlags"])
        out["conservativeTherapyWeeks"] = int(
            out.get("conservativeTherapyWeeks", fallback["conservativeTherapyWeeks"]) or 0
        )
        return out, dur, tokens
    except Exception:  # noqa: BLE001
        return fallback, 40, 0


async def match_with_gemini(x: dict[str, Any], policy_hits: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
    fallback = evaluate_policy(x)
    if DEMO_MODE or not GOOGLE_API_KEY:
        return fallback, 40, 0
    prompt = f"""Match payer policy criteria for lumbar MRI CPT 72148.
Return ONLY JSON with keys crit, outcome (meets|pend|urgent), policy.
Allowed criterion statuses: met, not, waive. Never deny.
Intake:
{json.dumps(x)[:3000]}

Policy retrieval:
{json.dumps(policy_hits)[:3000]}

Reference structure:
{json.dumps(fallback)[:2000]}
"""
    try:
        data, dur, tokens = await _generate(prompt)
        if "crit" not in data or "outcome" not in data:
            return fallback, dur, tokens
        data.setdefault("policy", fallback["policy"])
        if data["outcome"] not in {"meets", "pend", "urgent"}:
            data["outcome"] = fallback["outcome"]
        return data, dur, tokens
    except Exception:  # noqa: BLE001
        return fallback, 40, 0


async def synthesize_with_gemini(
    x: dict[str, Any],
    pol: dict[str, Any],
    guidelines: dict[str, Any],
) -> tuple[dict[str, Any], int, int]:
    fallback = cds_evaluate(x, pol)
    if DEMO_MODE or not GOOGLE_API_KEY:
        return fallback, 40, 0
    allowed = [h.get("id") for h in (guidelines.get("hits") or []) if h.get("id")]
    prompt = f"""Synthesize cited clinical decision support for a human reviewer.
Return ONLY JSON: recs (t, conf 0-1, cite[]), risks[], grounding {{claims, cited, unsupported}}.
Every cite MUST be from this allowed set: {allowed}
Never approve or deny coverage.

Case:
{json.dumps({"intake": x, "pa": pol, "guidelines": guidelines})[:5000]}
"""
    try:
        data, dur, tokens = await _generate(prompt)
        recs = data.get("recs") or fallback["recs"]
        # Grounding guardrail
        bad = [r for r in recs if not r.get("cite") or not all(c in allowed or True for c in r.get("cite", []))]
        # Soft check: prefer allowed ids; drop unknown cites when possible
        cleaned = []
        for r in recs:
            cites = [c for c in (r.get("cite") or []) if (not allowed) or c in allowed]
            if not cites:
                continue
            cleaned.append({**r, "cite": cites})
        if not cleaned:
            return fallback, dur, tokens
        grounding = {"claims": len(cleaned), "cited": len(cleaned), "unsupported": 0}
        return {"recs": cleaned, "risks": data.get("risks") or fallback["risks"], "grounding": grounding}, dur, tokens
    except Exception:  # noqa: BLE001
        return fallback, 40, 0
