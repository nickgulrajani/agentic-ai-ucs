"""Score synthetic prior-auth cases on policy outcome match (offline-friendly)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agentthree.domain import cds_evaluate, evaluate_policy, extract_entities  # noqa: E402


def main() -> int:
    cases = json.loads((Path(__file__).parent / "cases.json").read_text())
    rows = []
    for case in cases:
        x = extract_entities(case["note"], case["icd"])
        pol = evaluate_policy(x)
        cds = cds_evaluate(x, pol)
        ok = pol["outcome"] == case["expected_outcome"]
        rows.append(
            {
                "id": case["id"],
                "expected": case["expected_outcome"],
                "actual": pol["outcome"],
                "pass": ok,
                "gaps": x.get("gaps"),
                "findings": len(cds.get("recs") or []),
            }
        )
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {case['id']}: expected={case['expected_outcome']} actual={pol['outcome']}")

    passed = sum(1 for r in rows if r["pass"])
    total = len(rows)
    metrics = {
        "outcome_accuracy": passed / total if total else 0.0,
        "cases": total,
        "passed": passed,
        "source": "evaluation/run_eval.py · deterministic domain scorer",
        "rows": rows,
    }
    out = ROOT / "evaluation" / "last_results.json"
    out.write_text(json.dumps(metrics, indent=2))
    print(f"\noutcome_accuracy={metrics['outcome_accuracy']:.2f} ({passed}/{total})")
    print(f"wrote {out}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
