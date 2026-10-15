"""Deterministic clinical helpers used in DEMO_MODE and as grounding fallbacks."""

from __future__ import annotations

import re
from typing import Any

MEDS = [
    {"name": "naproxen", "rxcui": "7258", "cls": "NSAID"},
    {"name": "cyclobenzaprine", "rxcui": "21949", "cls": "Muscle relaxant"},
    {"name": "gabapentin", "rxcui": "25480", "cls": "Anticonvulsant (neuropathic pain)"},
    {"name": "ibuprofen", "rxcui": "5640", "cls": "NSAID"},
    {"name": "prednisone", "rxcui": "8640", "cls": "Oral corticosteroid"},
]
ICD = {
    "M54.16": "Radiculopathy, lumbar region",
    "M54.50": "Low back pain, unspecified",
}
NEG = re.compile(r"\b(no|denies|without|negative for|full strength)\b", re.I)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def find_affirmed(note: str, pattern: str) -> str | None:
    cre = re.compile(pattern, re.I)
    for s in _sentences(note):
        m = cre.search(s)
        if m and not NEG.search(s[: m.start()]):
            return s
    return None


def extract_entities(note: str, icd: str) -> dict[str, Any]:
    t = note.lower()
    meds = []
    for m in MEDS:
        if m["name"] in t:
            mm = re.search(rf"{m['name']}\s+(\d+\s*mg)", t)
            meds.append({**m, "dose": mm.group(1).replace(" ", " ") if mm else None})
    pt_m = re.search(r"(\d+)\s*weeks?\s+of\s+(physical therapy|pt\b)", t)
    sym_m = re.search(r"for\s+(?:about\s+)?(\d+)\s*weeks?", t)
    pt_weeks = int(pt_m.group(1)) if pt_m else 0
    symptom_weeks = int(sym_m.group(1)) if sym_m else (0 if re.search(r"\b\d+\s*hours?\b", t) else None)
    conservative = pt_weeks or (symptom_weeks if meds and symptom_weeks else 0)
    neuro = find_affirmed(note, r"(numbness|weakness|reflex|foot drop|straight-leg raise)")
    radic = find_affirmed(note, r"(radiat|radicular|sciatica|down the (left|right)? ?leg)")
    cauda = find_affirmed(note, r"(saddle|urinary retention|incontinence)")
    cancer = find_affirmed(note, r"(history of cancer|malignancy|metasta)")
    prior = find_affirmed(note, r"(prior|previous)\s+(lumbar\s+)?(mri|imaging)")
    red_flags = []
    if cauda:
        red_flags.append({"flag": "Possible cauda equina syndrome", "evidence": cauda})
    if cancer:
        red_flags.append({"flag": "History of malignancy", "evidence": cancer})
    gaps: list[str] = []
    if not red_flags and (conservative or 0) < 6:
        gaps.append(
            f"Conservative therapy documented for {conservative} week(s); policy requires 6."
            if conservative
            else "No documented course of physical therapy or 6-week conservative treatment."
        )
    if not neuro and not radic:
        gaps.append("No objective neurologic finding or radicular symptom documented.")
    if not red_flags and any(m.get("dose") is None for m in meds):
        gaps.append("Medication dose or duration missing for at least one agent.")
    return {
        "icd": icd,
        "icdText": ICD.get(icd, icd),
        "meds": meds,
        "ptWeeks": pt_weeks,
        "symptomWeeks": symptom_weeks,
        "conservativeTherapyWeeks": conservative or 0,
        "neuroS": neuro,
        "radicS": radic,
        "redFlags": red_flags,
        "prior": prior,
        "gaps": gaps,
    }


def evaluate_policy(x: dict[str, Any]) -> dict[str, Any]:
    urgent = bool(x.get("redFlags"))
    crit = [
        {
            "id": "C1",
            "text": "Diagnosis consistent with lumbar radiculopathy or persistent low back pain",
            "sec": "§3.1",
            "st": "met",
            "ev": f"{x['icd']} · {x['icdText']}",
        },
        {
            "id": "C2",
            "text": "At least 6 weeks of documented conservative therapy (PT, NSAIDs, activity modification)",
            "sec": "§3.2",
            "st": "waive" if urgent else ("met" if x.get("conservativeTherapyWeeks", 0) >= 6 else "not"),
            "ev": (
                "Waived under §4 red-flag exception"
                if urgent
                else (
                    f"{x.get('conservativeTherapyWeeks')} weeks documented"
                    if x.get("conservativeTherapyWeeks")
                    else "Not documented"
                )
            ),
        },
        {
            "id": "C3",
            "text": "Objective neurologic deficit or persistent radicular symptoms",
            "sec": "§3.3",
            "st": "met" if (x.get("neuroS") or x.get("radicS")) else "not",
            "ev": x.get("neuroS") or x.get("radicS") or "Not documented",
        },
        {
            "id": "C4",
            "text": "No lumbar MRI in prior 12 months without interval change",
            "sec": "§3.4",
            "st": "not" if x.get("prior") else "met",
            "ev": x.get("prior") or "No prior lumbar imaging in claims history (eligibility tool)",
        },
    ]
    if urgent:
        crit.append(
            {
                "id": "C5",
                "text": "Red-flag exception: suspected cauda equina, malignancy, infection, or fracture",
                "sec": "§4",
                "st": "met",
                "ev": "; ".join(r["flag"] for r in x["redFlags"]),
            }
        )
    all_met = all(c["st"] != "not" for c in crit)
    outcome = "urgent" if urgent else ("meets" if all_met else "pend")
    return {
        "crit": crit,
        "outcome": outcome,
        "policy": {
            "id": "AHP-RAD-014",
            "title": "Advanced Imaging of the Lumbar Spine (fictional)",
            "version": "3.2",
            "effective": "2026-07-01",
        },
    }


def cds_evaluate(x: dict[str, Any], pol: dict[str, Any]) -> dict[str, Any]:
    outcome = pol["outcome"]
    if outcome == "urgent":
        recs = [
            {
                "t": "Emergent imaging is indicated. Findings of saddle anesthesia with urinary retention warrant same-day MRI and surgical evaluation.",
                "conf": 0.95,
                "cite": ["GL-ACR-LBP v.red-flag", "GL-NASS-CES §2"],
            },
            {
                "t": "Route as expedited review under the urgent decision timeframe.",
                "conf": 0.92,
                "cite": ["REG-CMS-0057-F timeframes"],
            },
        ]
        risks = ["Delay risks permanent neurologic injury"]
    elif outcome == "meets":
        recs = [
            {
                "t": "MRI is appropriate: radicular symptoms with objective deficit persist after 6+ weeks of conservative care, and the patient is a candidate for intervention.",
                "conf": 0.88,
                "cite": ["GL-ACR-LBP v.subacute-radiculopathy", "GL-ACP-2017 rec 3"],
            },
            {
                "t": "Consider documenting PT discharge summary in the record to strengthen audit trail.",
                "conf": 0.71,
                "cite": ["POL-AHP-RAD-014 §5"],
            },
        ]
        risks = ["Incidental findings are common on lumbar MRI; correlate clinically"]
    else:
        recs = [
            {
                "t": "Imaging within the first 6 weeks of uncomplicated low back pain without red flags is generally not recommended.",
                "conf": 0.86,
                "cite": ["GL-ACR-LBP v.acute-uncomplicated", "GL-ACP-2017 rec 1"],
            },
            {
                "t": "Alternative: continue conservative therapy and reassess at 6 weeks; request PT records or exam documenting neurologic findings if present.",
                "conf": 0.79,
                "cite": ["GL-ACP-2017 rec 2", "POL-AHP-RAD-014 §3.2"],
            },
        ]
        risks = ["Early imaging may lead to low-value downstream procedures"]
    return {
        "recs": recs,
        "risks": risks,
        "grounding": {"claims": len(recs), "cited": len(recs), "unsupported": 0},
    }
