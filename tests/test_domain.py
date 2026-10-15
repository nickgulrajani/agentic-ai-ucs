from agentthree.domain import evaluate_policy, extract_entities


def test_meets_criteria_extraction():
    note = (
        "58-year-old with low back pain radiating down the left leg for 9 weeks. "
        "Completed 6 weeks of physical therapy (12 visits). Trialed naproxen 500 mg. "
        "Exam: positive straight-leg raise on the left, diminished left ankle reflex."
    )
    x = extract_entities(note, "M54.16")
    assert x["conservativeTherapyWeeks"] >= 6
    assert x["neuroS"] or x["radicS"]
    pol = evaluate_policy(x)
    assert pol["outcome"] == "meets"


def test_red_flag_urgent():
    note = (
        "Acute worsening low back pain with new saddle numbness and urinary retention. "
        "Bilateral leg weakness on exam."
    )
    x = extract_entities(note, "M54.16")
    assert x["redFlags"]
    assert evaluate_policy(x)["outcome"] == "urgent"


def test_audit_chain_links():
    from agentthree.audit import AuditLedger

    ledger = AuditLedger("ctx-test", "trace-test")
    a = ledger.append(seq=1, agent="intake", kind="sys", title="start", payload={"a": 1})
    b = ledger.append(seq=2, agent="pa", kind="sys", title="next", payload={"b": 2})
    assert a["prevHash"] == "0" * 64
    assert b["prevHash"] == a["hash"]
    assert a["hash"] != b["hash"]
