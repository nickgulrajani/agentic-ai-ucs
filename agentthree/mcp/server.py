"""Unified FastMCP server: FHIR, RxNorm, policy, eligibility, guidelines."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx
from fastmcp import FastMCP

from agentthree.config import DATA_DIR, MCP_PORT

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("AgentThree Clinical MCP")

_PATIENTS = json.loads((DATA_DIR / "fhir" / "patients.json").read_text())
_CONDITIONS = json.loads((DATA_DIR / "fhir" / "conditions.json").read_text())
_POLICY = json.loads((DATA_DIR / "policies" / "AHP-RAD-014.json").read_text())

# Local RxNorm fallbacks when NLM is unreachable (demo must work offline)
_RXNORM_LOCAL = {
    "naproxen": {"rxcui": "7258", "name": "naproxen", "tty": "IN", "class": "NSAID"},
    "cyclobenzaprine": {
        "rxcui": "21949",
        "name": "cyclobenzaprine",
        "tty": "IN",
        "class": "Muscle relaxant",
    },
    "gabapentin": {
        "rxcui": "25480",
        "name": "gabapentin",
        "tty": "IN",
        "class": "Anticonvulsant (neuropathic pain)",
    },
    "ibuprofen": {"rxcui": "5640", "name": "ibuprofen", "tty": "IN", "class": "NSAID"},
    "prednisone": {
        "rxcui": "8640",
        "name": "prednisone",
        "tty": "IN",
        "class": "Oral corticosteroid",
    },
}

# Fault injection (set by API via env for a single run — process-local)
_FAULT: str | None = os.getenv("MCP_FAULT")
_ELIG_FAILS = 0
_POLICY_FAILS = 0


def set_fault(fault: str | None) -> None:
    global _FAULT, _ELIG_FAILS, _POLICY_FAILS
    _FAULT = fault or None
    _ELIG_FAILS = 0
    _POLICY_FAILS = 0


@mcp.tool()
def fhir_read(resourceType: str, id: str) -> dict[str, Any]:
    """Read a FHIR R4 resource by type and id from the demo store.

    Args:
        resourceType: FHIR resource type, e.g. Patient.
        id: Resource id, e.g. demo-7781.
    """
    logger.info("fhir_read %s/%s", resourceType, id)
    if resourceType != "Patient":
        return {"error": f"Demo store only supports Patient reads, got {resourceType}"}
    for member, patient in _PATIENTS.items():
        if patient["id"] == id:
            out = dict(patient)
            out["name"] = "[redacted in tool response]"
            out["_member"] = member
            return out
    return {"error": f"Patient/{id} not found"}


@mcp.tool()
def fhir_search(resourceType: str, patient: str, clinical_status: str = "active") -> dict[str, Any]:
    """Search FHIR resources for a patient.

    Args:
        resourceType: e.g. Condition.
        patient: Patient reference or id (Patient/demo-7781 or demo-7781).
        clinical_status: clinical-status filter, default active.
    """
    logger.info("fhir_search %s patient=%s", resourceType, patient)
    pid = patient.split("/")[-1]
    if resourceType != "Condition":
        return {"total": 0, "entry": [], "message": f"Unsupported search type {resourceType}"}
    entries = _CONDITIONS.get(pid, [])
    if clinical_status:
        entries = [
            e
            for e in entries
            if e.get("clinicalStatus", {}).get("coding", [{}])[0].get("code") == clinical_status
            or not clinical_status
        ]
    return {"total": len(entries), "entry": entries}


@mcp.tool()
def rxnorm_normalize(term: str) -> dict[str, Any]:
    """Normalize a medication string to RxNorm RxCUI via NLM RxNav (with local fallback).

    Args:
        term: Free-text medication, e.g. 'naproxen 500 mg'.
    """
    logger.info("rxnorm_normalize %s", term)
    key = term.strip().lower().split()[0] if term.strip() else ""
    # Try NLM RxNav (free, no key)
    try:
        with httpx.Client(timeout=4.0) as client:
            r = client.get(
                "https://rxnav.nlm.nih.gov/REST/rxcui.json",
                params={"name": key or term, "search": 1},
            )
            r.raise_for_status()
            data = r.json()
            rxcui = (data.get("idGroup") or {}).get("rxnormId") or [None]
            rxcui = rxcui[0] if rxcui else None
            if rxcui:
                local = _RXNORM_LOCAL.get(key, {})
                return {
                    "rxcui": str(rxcui),
                    "name": local.get("name", key),
                    "tty": local.get("tty", "IN"),
                    "class": local.get("class", "unknown"),
                    "source": "nlm-rxnav",
                }
    except Exception as exc:  # noqa: BLE001
        logger.warning("RxNav unavailable (%s); using local table", exc)

    if key in _RXNORM_LOCAL:
        return {**_RXNORM_LOCAL[key], "source": "local-fallback"}
    return {"error": f"Unable to normalize term: {term}", "rxcui": None}


@mcp.tool()
def policy_search(
    query: str,
    payer: str = "AHP",
    mode: str = "hybrid",
    topK: int = 5,
) -> dict[str, Any]:
    """Search payer prior-auth policy chunks (demo hybrid retrieval).

    Args:
        query: Natural language policy query.
        payer: Payer code.
        mode: Retrieval mode label (hybrid).
        topK: Max hits.
    """
    global _POLICY_FAILS
    logger.info("policy_search q=%s payer=%s", query, payer)

    if _FAULT == "mcp_timeout":
        _POLICY_FAILS += 1
        if _POLICY_FAILS <= 2:
            raise TimeoutError("Request timed out after 5000 ms")

    if _FAULT == "policy_missing":
        return {
            "hits": [],
            "message": f"No active policy indexed for payer {payer} + CPT 72148",
            "policyVersion": None,
        }

    q = query.lower()
    scored: list[tuple[float, dict[str, Any]]] = []
    for chunk in _POLICY["chunks"]:
        score = 0.4
        tokens = set(re.findall(r"[a-z0-9]+", chunk["text"].lower()))
        for tok in re.findall(r"[a-z0-9]+", q):
            if tok in tokens:
                score += 0.08
        if "72148" in q or "mri" in q or "lumbar" in q:
            score += 0.2
        scored.append((min(score, 0.99), chunk))
    scored.sort(key=lambda x: -x[0])
    hits = [{"chunk": c["id"], "score": round(s, 2), "text": c["text"]} for s, c in scored[:topK]]
    return {
        "hits": hits,
        "policyVersion": _POLICY["version"],
        "policyId": _POLICY["id"],
        "title": _POLICY["title"],
        "effective": _POLICY["effective"],
        "reranker": "lexical-demo",
        "mode": mode,
        "payer": payer,
    }


@mcp.tool()
def check_eligibility(member: str, serviceCode: str, dateOfService: str) -> dict[str, Any]:
    """Check member eligibility and whether PA is required for a service.

    Args:
        member: Member ID.
        serviceCode: CPT code.
        dateOfService: ISO date YYYY-MM-DD.
    """
    global _ELIG_FAILS
    logger.info("check_eligibility member=%s cpt=%s", member, serviceCode)

    if _FAULT == "mcp_down":
        _ELIG_FAILS += 1
        if _ELIG_FAILS <= 3:
            raise RuntimeError("eligibility-mcp unavailable (HTTP 503 from upstream)")

    patient = _PATIENTS.get(member)
    if not patient:
        return {"active": False, "error": f"Unknown member {member}"}
    return {
        "active": True,
        "plan": "Acme Gold PPO (fictional)",
        "paRequired": serviceCode == "72148",
        "priorLumbarImaging12mo": False,
        "member": member,
        "dateOfService": dateOfService,
        "serviceCode": serviceCode,
    }


@mcp.tool()
def guideline_search(
    query: str,
    sources: list[str] | None = None,
    mode: str = "vector+graph",
    topK: int = 4,
) -> dict[str, Any]:
    """Retrieve clinical guideline chunks for evidence synthesis.

    Args:
        query: Clinical question.
        sources: Preferred sources (e.g. ACR, ACP).
        mode: Retrieval mode label.
        topK: Max hits.
    """
    logger.info("guideline_search q=%s", query)
    q = query.lower()
    scored: list[tuple[float, dict[str, Any]]] = []
    for g in _POLICY["guidelines"]:
        score = 0.35
        blob = (g["id"] + " " + g["text"]).lower()
        for tok in re.findall(r"[a-z0-9]+", q):
            if tok in blob:
                score += 0.07
        if "cauda" in q and "ces" in g["id"].lower():
            score += 0.4
        if "radicul" in q and "radicul" in blob:
            score += 0.25
        scored.append((min(score, 0.99), g))
    scored.sort(key=lambda x: -x[0])
    hits = [{"id": g["id"], "score": round(s, 2), "text": g["text"]} for s, g in scored[:topK]]
    return {"hits": hits, "graphHops": 2, "sources": sources or ["ACR AC", "ACP"], "mode": mode}


def main() -> None:
    port = int(os.getenv("PORT", str(MCP_PORT)))
    logger.info("AgentThree MCP listening on http://0.0.0.0:%s/mcp", port)
    mcp.run(transport="http", host="0.0.0.0", port=port, path="/mcp")


if __name__ == "__main__":
    main()
