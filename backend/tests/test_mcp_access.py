"""
Unit tests for the parts of mcp_access/ that don't need a live database —
PKCE verification, the response envelope, the taxonomy tool, password
hashing, and list_tracked_companies (a pure read of a static dict). Every
scope/plan/rate-limit/revocation check in server.py needs a real Postgres
connection (mcp_connections, mcp_tokens, mcp_usage) and is exercised by
running the app locally instead — see the run instructions in
changes/2026-09-13-mcp-ai-agent-access.md's Decision Log.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv_linux/bin/python ../tests/test_mcp_access.py

Every `test_*` function is a plain assert, so `pytest` picks them up
unchanged if it is ever added (same convention as test_curated_match.py).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import auth  # noqa: E402
from mcp_access import db_helpers, envelope, tools  # noqa: E402
from mcp_access.taxonomy import get_taxonomy  # noqa: E402


def test_pkce_round_trip():
    verifier = "a" * 64  # a valid-shaped PKCE verifier (43-128 chars)
    import base64
    import hashlib
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
    assert db_helpers.verify_pkce(verifier, challenge)
    assert not db_helpers.verify_pkce(verifier, "wrong-challenge")
    assert not db_helpers.verify_pkce("different-verifier" * 4, challenge)


def test_password_hash_round_trip():
    hashed = auth.hash_password("correct horse battery staple")
    assert auth.verify_password("correct horse battery staple", hashed)
    assert not auth.verify_password("wrong password", hashed)
    # Never stores the plaintext.
    assert "correct horse battery staple" not in hashed


def test_build_envelope_shape():
    env = envelope.build_envelope(
        {"rows": [{"role_category": "Designer", "count": 5}]},
        unit="count of postings",
        scope={"role_category": ["Designer"]},
        time_window=envelope.time_window_label("2026-01-01", "2026-02-01"),
        source="test",
        total_matching=5,
    )
    assert env["data"]["rows"][0]["count"] == 5
    assert env["meta"]["unit"] == "count of postings"
    assert env["meta"]["time_window"]["label"] == "2026-01-01 to 2026-02-01"
    assert env["meta"]["total_matching"] == 5


def test_time_window_label_single_day():
    label = envelope.time_window_label("2026-01-01", "2026-01-01")
    assert label["label"] == "2026-01-01"


def test_time_window_label_empty():
    label = envelope.time_window_label(None, None)
    assert label["label"] == "no data in range"


def test_curated_errors_have_a_type_and_message():
    for err in (
        envelope.scope_denied("jobs.read", "get_job_demand"),
        envelope.plan_required(),
        envelope.rate_limited("midnight UTC"),
        envelope.revoked(),
    ):
        assert "error" in err
        assert err["error"]["type"]
        assert err["error"]["message"]


def test_get_taxonomy_covers_the_documented_dimensions():
    result = get_taxonomy()
    data = result["data"]
    for key in (
        "role_category", "level", "track", "work_arrangement", "education_required",
        "employment_event_type", "employment_event_direction", "employment_event_confidence",
    ):
        assert key in data, f"missing taxonomy dimension: {key}"
        assert len(data[key]) > 0
    # role_category must include the two non-tracked-occupation escape
    # hatches (job-classification.md — Unknown vs. Other) — a caller who
    # only saw "Designer/PM/Engineer" would assume those are the only
    # valid filter values.
    role_values = {v["value"] for v in data["role_category"]}
    assert {"Designer", "Product Manager", "Engineer", "other", "unknown"} <= role_values


def test_list_tracked_companies_is_a_real_static_list():
    result = tools.list_tracked_companies()
    companies = result["data"]["companies"]
    assert len(companies) > 0
    assert result["meta"]["total_matching"] == len(companies)
    # Every company has a non-empty industry — industries.py is curated,
    # not sparse, for every company it lists at all.
    assert all(c["industry"] for c in companies)


def test_tool_scopes_cover_every_scoped_tool():
    # Every tool server.py registers behind _enforce_and_call must have an
    # entry here — a missing one would raise a KeyError at call time
    # instead of failing this test up front.
    for tool_name in ("get_job_demand", "get_skill_demand", "get_salary_stats", "get_employment_risk", "list_tracked_companies"):
        assert tool_name in tools.TOOL_SCOPES
    assert tools.TOOL_SCOPES["get_salary_stats"] == "compensation.read"
    assert "get_salary_stats" in tools.PREMIUM_ONLY_TOOLS
    assert "get_job_demand" not in tools.PREMIUM_ONLY_TOOLS


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")
