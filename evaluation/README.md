# Evaluation

Synthetic prior-auth cases scored on **outcome accuracy** (meets / pend / urgent).

```bash
.venv/bin/python -m evaluation.run_eval
```

| File | Purpose |
|------|---------|
| `cases.json` | Golden scenarios aligned with the Live Run presets |
| `run_eval.py` | Deterministic scorer (domain helpers; no Gemini required) |
| `last_results.json` | Latest metrics (gitignored) — paste into the UI Evaluation tab |

## Metrics (roadmap)

Align with the Live Run Evaluation tab: documentation completeness, criterion match, citation grounding, escalation correctness, latency budgets.
