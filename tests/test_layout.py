from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_expected_top_level_folders_exist():
    for name in ("agents", "mcp_servers", "agentthree", "tests", "evaluation", "docs", "ui", "data"):
        assert (ROOT / name).is_dir(), name


def test_agent_packages_present():
    for name in ("clinical_intake", "prior_auth", "clinical_decision_support"):
        assert (ROOT / "agents" / name / "agent.py").is_file()


def test_mcp_clinical_server_present():
    assert (ROOT / "mcp_servers" / "clinical" / "server.py").is_file()
