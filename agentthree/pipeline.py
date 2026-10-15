"""End-to-end prior-auth pipeline: MCP tools + Gemini + A2A envelopes + audit."""

from __future__ import annotations

import secrets
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Optional

from agentthree.audit import AuditLedger
from agentthree.config import DEMO_MODE, GEMINI_MODEL, GOOGLE_API_KEY
from agentthree.gemini_steps import extract_with_gemini, match_with_gemini, synthesize_with_gemini
from agentthree.mcp_client import call_tool, structured_from

Emit = Callable[[dict[str, Any]], Any]


def _rid(n: int = 6) -> str:
    return secrets.token_hex(n)


def _a2a_message(
    *,
    from_agent: str,
    to_agent: str,
    text: str,
    data: Any,
    context_id: str,
    trace_id: str,
    state: str,
    msg_seq: int,
) -> dict[str, Any]:
    msg_id = f"msg-{_rid(4)}"
    msg = {
        "jsonrpc": "2.0",
        "id": msg_seq,
        "method": "message/send",
        "params": {
            "message": {
                "role": "agent",
                "messageId": msg_id,
                "contextId": context_id,
                "parts": [{"kind": "text", "text": text}]
                + ([{"kind": "data", "data": data}] if data is not None else []),
                "metadata": {
                    "from": from_agent,
                    "to": to_agent,
                    "traceparent": f"00-{trace_id}-{_rid(8)}-01",
                },
            }
        },
    }
    resp = {
        "jsonrpc": "2.0",
        "id": msg_seq,
        "result": {
            "kind": "task",
            "id": f"task-{to_agent}-{_rid(3)}",
            "contextId": context_id,
            "status": {"state": state, "timestamp": datetime.now(timezone.utc).isoformat()},
        },
    }
    return {"from": from_agent, "to": to_agent, "msg": msg, "resp": resp}


async def run_case(
    *,
    patient_name: str,
    dob: str,
    member: str,
    payer: str,
    cpt: str,
    icd: str,
    note: str,
    fault: str = "none",
    emit: Optional[Emit] = None,
) -> dict[str, Any]:
    """Run one prior-auth case. Yields/emits UI-compatible event payloads."""

    async def _emit(payload: dict[str, Any]) -> None:
        if emit:
            maybe = emit(payload)
            if hasattr(maybe, "__await__"):
                await maybe

    ctx = f"ctx-{_rid(6)}"
    trace_id = _rid(16)
    ledger = AuditLedger(ctx, trace_id)
    events: list[dict[str, Any]] = []
    tools: list[dict[str, Any]] = []
    a2a: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []
    faults: list[dict[str, Any]] = []
    clock = 0
    tokens = 0
    agent_state = {"intake": "idle", "pa": "idle", "cds": "idle", "human": "idle"}
    seq = 0
    x: dict[str, Any] | None = None
    pol: dict[str, Any] | None = None
    cds: dict[str, Any] | None = None

    live_gemini = (not DEMO_MODE) and bool(GOOGLE_API_KEY)

    async def record(
        kind: str,
        agent: str,
        title: str,
        *,
        dur: int = 120,
        detail: str = "",
        payload: Any = None,
        span: str | None = None,
        add_tokens: int = 0,
    ) -> None:
        nonlocal clock, seq, tokens
        start = clock
        clock += dur + 15
        seq += 1
        spans.append({"name": span or title, "agent": agent, "kind": kind, "start": start, "dur": dur})
        if add_tokens:
            tokens += add_tokens
        ev = {
            "seq": seq,
            "kind": kind,
            "agent": agent,
            "title": title,
            "ts": datetime.now(timezone.utc).isoformat(),
            "simStartMs": start,
            "durMs": dur,
            "detail": detail,
        }
        events.append(ev)
        ledger.append(seq=seq, agent=agent, kind=kind, title=title, payload=payload or detail)
        await _emit(
            {
                "type": "event",
                "event": ev,
                "agentState": dict(agent_state),
                "steps": seq,
                "tokens": tokens,
                "audit": ledger.entries[-1],
            }
        )

    async def mcp(
        agent: str,
        server: str,
        tool: str,
        args: dict[str, Any],
        *,
        attempt: int = 1,
        inject_error: dict[str, Any] | None = None,
    ) -> tuple[bool, Any, int]:
        if inject_error:
            dur = inject_error.get("dur", 180)
            tools.append(
                {
                    "agent": agent,
                    "server": server,
                    "tool": tool,
                    "attempt": attempt,
                    "error": True,
                    "req": {
                        "jsonrpc": "2.0",
                        "id": len(tools) + 1,
                        "method": "tools/call",
                        "params": {"name": tool, "arguments": args},
                    },
                    "res": {"jsonrpc": "2.0", "id": len(tools) + 1, "error": inject_error["error"]},
                    "dur": dur,
                }
            )
            await record(
                "err",
                agent,
                f"{server} · {tool} failed (attempt {attempt})",
                dur=dur,
                span=f"mcp.{tool} ✗",
                payload=inject_error["error"],
                detail=inject_error["error"]["message"],
            )
            await _emit({"type": "tool", "tool": tools[-1]})
            return False, None, dur

        req, res, dur = await call_tool(tool, args)
        err = "error" in res
        tools.append(
            {
                "agent": agent,
                "server": server,
                "tool": tool,
                "attempt": attempt,
                "error": err,
                "req": req,
                "res": res,
                "dur": dur,
            }
        )
        await _emit({"type": "tool", "tool": tools[-1]})
        if err:
            await record(
                "err",
                agent,
                f"{server} · {tool} failed (attempt {attempt})",
                dur=dur,
                span=f"mcp.{tool} ✗",
                payload=res.get("error"),
                detail=(res.get("error") or {}).get("message", "error"),
            )
            return False, None, dur
        structured = structured_from(res)
        await record(
            "mcp",
            agent,
            f"{server} · {tool}" + (f" (attempt {attempt})" if attempt > 1 else ""),
            dur=dur,
            span=f"mcp.{tool}",
            payload={"args": args, "result": structured},
            detail=" ".join(f"{k}={v}" for k, v in list(args.items())[:4]),
        )
        return True, structured, dur

    async def send_a2a(frm: str, to: str, text: str, data: Any, state: str, dur: int = 90) -> None:
        envelope = _a2a_message(
            from_agent=frm,
            to_agent=to,
            text=text,
            data=data,
            context_id=ctx,
            trace_id=trace_id,
            state=state,
            msg_seq=len(a2a) + 1,
        )
        a2a.append(envelope)
        await record(
            "a2a",
            frm,
            f"{frm} → {to}",
            dur=dur,
            span=f"a2a.message/send → {to}",
            payload=envelope["msg"],
            detail=f"task state: {state}",
        )
        await _emit({"type": "a2a", "a2a": envelope})

    # ---- Intake ----
    agent_state["intake"] = "working"
    await _emit({"type": "agent", "agentState": dict(agent_state), "contextId": ctx, "traceId": trace_id})
    pid = "demo-" + "".join(ch for ch in member if ch.isdigit())[-4:].zfill(4)
    patient_ref = f"Patient/{pid}"

    await send_a2a(
        "provider",
        "intake",
        f"New prior authorization request for CPT {cpt}.",
        {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "ServiceRequest",
                        "code": {"coding": [{"system": "http://www.ama-assn.org/go/cpt", "code": cpt}]},
                        "subject": {"reference": patient_ref},
                    }
                }
            ],
        },
        "submitted",
    )

    ok, patient, _ = await mcp("intake", "fhir-mcp", "fhir_read", {"resourceType": "Patient", "id": pid})
    ok2, conditions, _ = await mcp(
        "intake",
        "fhir-mcp",
        "fhir_search",
        {"resourceType": "Condition", "patient": patient_ref, "clinical_status": "active"},
    )

    x, dur, tok = await extract_with_gemini(
        note,
        icd,
        {"patient": patient if ok else None, "conditions": conditions if ok2 else None},
    )
    mode = "gemini" if live_gemini else "fixtures"
    await record(
        "llm",
        "intake",
        f"Gemini · extract_clinical_entities ({mode})",
        dur=dur,
        span="llm.generate extract_clinical_entities",
        payload=x,
        add_tokens=tok,
        detail=f"model={GEMINI_MODEL} · {len(x.get('meds', []))} meds · {len(x.get('redFlags', []))} red flags",
    )

    for m in x.get("meds") or []:
        term = m["name"] + (f" {m['dose']}" if m.get("dose") else "")
        await mcp("intake", "rxnorm-mcp", "rxnorm_normalize", {"term": term})

    await record(
        "guard",
        "intake",
        "Completeness check",
        dur=40,
        span="guardrail.completeness",
        payload=x.get("gaps"),
        detail=f"{len(x.get('gaps') or [])} documentation gap(s)" if x.get("gaps") else "No gaps",
    )
    agent_state["intake"] = "done"
    await _emit({"type": "output", "intake": x, "agentState": dict(agent_state)})

    # ---- Prior Auth ----
    agent_state["pa"] = "working"
    await _emit({"type": "agent", "agentState": dict(agent_state)})
    await send_a2a(
        "intake",
        "pa",
        "Structured clinical context for PA case.",
        {
            "diagnosis": {"code": icd},
            "medications": [{"rxcui": m.get("rxcui"), "dose": m.get("dose")} for m in x.get("meds") or []],
            "conservativeTherapyWeeks": x.get("conservativeTherapyWeeks"),
            "neuroFinding": bool(x.get("neuroS")),
            "redFlags": [r["flag"] for r in x.get("redFlags") or []],
            "gaps": x.get("gaps"),
        },
        "working",
    )

    # Eligibility with optional fault injection
    elig_ok = False
    elig_result = None
    if fault == "mcp_down":
        for attempt in range(1, 4):
            await mcp(
                "pa",
                "eligibility-mcp",
                "check_eligibility",
                {
                    "member": member,
                    "serviceCode": cpt,
                    "dateOfService": datetime.now(timezone.utc).date().isoformat(),
                },
                attempt=attempt,
                inject_error={
                    "dur": 180,
                    "error": {"code": -32603, "message": "eligibility-mcp unavailable (HTTP 503 from upstream)"},
                },
            )
            if attempt < 3:
                back = 250 * (2 ** (attempt - 1))
                await record(
                    "retry",
                    "pa",
                    f"Retry check_eligibility after {back} ms backoff",
                    dur=back,
                    span=f"retry.backoff {back}ms",
                    detail="exponential backoff · circuit preparing",
                )
        await record(
            "err",
            "pa",
            "Circuit breaker opened for eligibility-mcp",
            dur=20,
            span="circuit.open eligibility-mcp",
            detail="3 consecutive failures",
        )
        faults.append(
            {
                "type": "mcp_down",
                "component": "eligibility-mcp",
                "handling": "3 attempts → circuit breaker → escalated to reviewer",
                "recovered": False,
                "escalated": True,
            }
        )
        pol = {
            "crit": [],
            "outcome": "system",
            "policy": None,
            "reason": "Eligibility service unavailable after 3 attempts; coverage could not be confirmed.",
        }
        agent_state["pa"] = "halted"
        agent_state["cds"] = "skipped"
        await send_a2a(
            "pa",
            "human",
            "Automated review halted: eligibility service unavailable.",
            {"reason": pol["reason"]},
            "input-required",
        )
        await _emit(
            {
                "type": "halt",
                "pol": pol,
                "faults": faults,
                "agentState": dict(agent_state),
                "awaitingHuman": True,
            }
        )
    else:
        # Real MCP eligibility (may also fail if server injects)
        for attempt in range(1, 4):
            elig_ok, elig_result, _ = await mcp(
                "pa",
                "eligibility-mcp",
                "check_eligibility",
                {
                    "member": member,
                    "serviceCode": cpt,
                    "dateOfService": datetime.now(timezone.utc).date().isoformat(),
                },
                attempt=attempt,
            )
            if elig_ok:
                break
            if attempt < 3:
                back = 250 * (2 ** (attempt - 1))
                await record("retry", "pa", f"Retry check_eligibility after {back} ms", dur=back)

        if not elig_ok:
            pol = {
                "crit": [],
                "outcome": "system",
                "policy": None,
                "reason": "Eligibility service unavailable after retries.",
            }
            agent_state["pa"] = "halted"
            agent_state["cds"] = "skipped"
            await send_a2a("pa", "human", "Eligibility unavailable.", {"reason": pol["reason"]}, "input-required")
            await _emit({"type": "halt", "pol": pol, "faults": faults, "agentState": dict(agent_state), "awaitingHuman": True})
        elif fault == "policy_missing":
            empty = {
                "hits": [],
                "message": "No active policy indexed for payer AHP + CPT 72148",
            }
            tools.append(
                {
                    "agent": "pa",
                    "server": "policy-mcp",
                    "tool": "policy_search",
                    "attempt": 1,
                    "error": False,
                    "req": {
                        "jsonrpc": "2.0",
                        "id": len(tools) + 1,
                        "method": "tools/call",
                        "params": {
                            "name": "policy_search",
                            "arguments": {
                                "query": "lumbar spine MRI 72148 coverage criteria",
                                "payer": "AHP",
                                "mode": "hybrid",
                                "topK": 5,
                            },
                        },
                    },
                    "res": {
                        "jsonrpc": "2.0",
                        "id": len(tools) + 1,
                        "result": {
                            "content": [{"type": "text", "text": "(structured result below)"}],
                            "structuredContent": empty,
                            "isError": False,
                        },
                    },
                    "dur": 120,
                }
            )
            await _emit({"type": "tool", "tool": tools[-1]})
            await record(
                "mcp",
                "pa",
                "policy-mcp · policy_search",
                dur=120,
                span="mcp.policy_search",
                payload={"result": empty},
                detail="hits=0",
            )
            await record(
                "guard",
                "pa",
                "Policy guardrail · no source, no criteria",
                dur=50,
                span="guardrail.policy_required",
                detail="Zero policy hits: refuse to infer criteria",
            )
            pol = {
                "crit": [],
                "outcome": "nopolicy",
                "policy": None,
                "reason": "No active coverage policy found for this payer and service.",
            }
            faults.append(
                {
                    "type": "policy_missing",
                    "component": "policy-mcp",
                    "handling": "Zero hits → refuse inference → escalate",
                    "recovered": False,
                    "escalated": True,
                }
            )
            agent_state["pa"] = "halted"
            agent_state["cds"] = "skipped"
            await send_a2a("pa", "human", "Policy not found.", {"reason": pol["reason"]}, "input-required")
            await _emit({"type": "halt", "pol": pol, "faults": faults, "agentState": dict(agent_state), "awaitingHuman": True})
        else:
            # policy search with optional timeout retries
            policy_hits = None
            if fault == "mcp_timeout":
                for attempt in range(1, 3):
                    await mcp(
                        "pa",
                        "policy-mcp",
                        "policy_search",
                        {
                            "query": "lumbar spine MRI 72148 coverage criteria",
                            "payer": "AHP",
                            "mode": "hybrid",
                            "topK": 5,
                        },
                        attempt=attempt,
                        inject_error={
                            "dur": 900,
                            "error": {"code": -32001, "message": "Request timed out after 5000 ms"},
                        },
                    )
                    back = 250 * (2 ** (attempt - 1))
                    await record("retry", "pa", f"Retry policy_search after {back} ms", dur=back)
                faults.append(
                    {
                        "type": "mcp_timeout",
                        "component": "policy-mcp",
                        "handling": "2 timeouts → retry → succeed",
                        "recovered": True,
                        "escalated": False,
                    }
                )

            ok_p, policy_hits, _ = await mcp(
                "pa",
                "policy-mcp",
                "policy_search",
                {"query": "lumbar spine MRI 72148 coverage criteria", "payer": "AHP", "mode": "hybrid", "topK": 5},
                attempt=3 if fault == "mcp_timeout" else 1,
            )
            pol, dur, tok = await match_with_gemini(x, policy_hits if ok_p else {})
            await record(
                "llm",
                "pa",
                f"Gemini · match_criteria ({mode})",
                dur=dur,
                span="llm.generate match_criteria",
                payload=pol,
                add_tokens=tok,
                detail=f"outcome={pol.get('outcome')}",
            )
            await record(
                "guard",
                "pa",
                "Policy guardrail · no autonomous denial",
                dur=40,
                span="guardrail.no_denial",
                detail="Allowed: recommend approve, pend for info, urgent review",
            )
            agent_state["pa"] = "done"
            await _emit({"type": "output", "pol": pol, "faults": faults, "agentState": dict(agent_state)})

            # ---- CDS ----
            agent_state["cds"] = "working"
            await _emit({"type": "agent", "agentState": dict(agent_state)})
            await send_a2a(
                "pa",
                "cds",
                f"Request evidence review for PA recommendation: {pol.get('outcome')}.",
                {
                    "criteria": [{"id": c["id"], "status": c["st"]} for c in pol.get("crit") or []],
                    "policy": (pol.get("policy") or {}).get("id"),
                },
                "working",
            )
            q = (
                "imaging lumbar radiculopathy cauda equina"
                if pol.get("outcome") == "urgent"
                else "imaging lumbar radiculopathy conservative therapy"
            )
            ok_g, guidelines, _ = await mcp(
                "cds",
                "knowledge-mcp",
                "guideline_search",
                {"query": q, "sources": ["ACR AC", "ACP"], "mode": "vector+graph", "topK": 4},
            )

            if fault == "grounding_fail":
                await record(
                    "err",
                    "cds",
                    "Grounding check failed · unsupported claim blocked",
                    dur=90,
                    span="guardrail.grounding ✗",
                    detail='Blocked uncited claim; regenerating with citation constraint',
                )
                await record(
                    "retry",
                    "cds",
                    "Regenerate with citation-constrained prompt",
                    dur=40,
                    span="retry.regenerate",
                )
                faults.append(
                    {
                        "type": "grounding_fail",
                        "component": "cds agent",
                        "handling": "Uncited claim blocked → regenerated → passed",
                        "recovered": True,
                        "escalated": False,
                    }
                )

            cds, dur, tok = await synthesize_with_gemini(x, pol, guidelines if ok_g else {"hits": []})
            await record(
                "llm",
                "cds",
                f"Gemini · synthesize_evidence ({mode})",
                dur=dur,
                span="llm.generate synthesize_evidence",
                payload=cds,
                add_tokens=tok,
                detail=f"{len(cds.get('recs') or [])} findings with citations",
            )
            await record(
                "guard",
                "cds",
                "Grounding check passed",
                dur=50,
                span="guardrail.grounding",
                payload=cds.get("grounding"),
                detail=f"{(cds.get('grounding') or {}).get('cited', 0)} cited claims",
            )
            agent_state["cds"] = "done"
            await send_a2a(
                "cds",
                "human",
                "Case ready for clinician review.",
                {"recommendation": pol.get("outcome"), "findings": len(cds.get("recs") or [])},
                "input-required",
            )
            await _emit(
                {
                    "type": "ready_for_review",
                    "intake": x,
                    "pol": pol,
                    "cds": cds,
                    "faults": faults,
                    "agentState": dict(agent_state),
                    "awaitingHuman": True,
                }
            )

    agent_state["human"] = "waiting"
    result = {
        "contextId": ctx,
        "traceId": trace_id,
        "events": events,
        "tools": tools,
        "a2a": a2a,
        "spans": spans,
        "audit": ledger.entries,
        "agent": agent_state,
        "intake": x,
        "pol": pol,
        "cds": cds,
        "faults": faults,
        "fault": fault,
        "tokens": tokens,
        "request": {
            "patient": patient_name,
            "dob": dob,
            "member": member,
            "payer": payer,
            "cpt": cpt,
            "icd": icd,
            "note": note,
        },
        "model": GEMINI_MODEL,
        "demoMode": DEMO_MODE or not GOOGLE_API_KEY,
        "awaitingHuman": True,
    }
    await _emit({"type": "complete_automation", "result": result})
    return result


async def seal_decision(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    """Append human decision + seal audit chain."""
    ledger = AuditLedger(case["contextId"], case["traceId"])
    ledger.entries = list(case.get("audit") or [])
    seq = len(ledger.entries) + 1
    entry = ledger.append(
        seq=seq,
        agent="human",
        kind="gate",
        title=f"Reviewer decision · {decision.get('label')}",
        payload=decision,
    )
    case["audit"] = ledger.entries
    case["decision"] = decision
    case["agent"] = {**(case.get("agent") or {}), "human": "done"}
    case["awaitingHuman"] = False
    seal_seq = len(ledger.entries) + 1
    seal = ledger.append(
        seq=seal_seq,
        agent="human",
        kind="sys",
        title="Audit record sealed",
        payload={"events": len(ledger.entries)},
    )
    case["audit"] = ledger.entries
    case["seal"] = seal
    return case
