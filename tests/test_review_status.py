"""Checks run on every push. They call ./review-status <id> --as-of 2026-11-16 --json."""
import json
import os
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "review-status")

S1 = "3f1c9a20-7b4e-4c1d-9a55-0e6f2b7c1a01"
S2 = "8d42e6b1-2c90-4f3a-b7e8-91a0c4d5e602"
S3 = "c07a5f93-6e18-4b2c-8d41-5f3e9b2a7c03"
S6 = "92d7b4e0-5f61-4a8c-b3d9-7e2a1c6f4d06"


def run(sid):
    assert os.access(TOOL, os.X_OK), "./review-status is missing or not executable"
    p = subprocess.run([TOOL, sid, "--as-of", "2026-11-16", "--json"],
                       cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def filed(report):
    return {r["user_id"]: r["filed"] for r in report["reviewers"]}


# 1. Who is involved

def test_s1_basics():
    r = run(S1)
    assert r["status"] == "REVIEW_PENDING"
    assert r["submitter"] == "sub_jammy"
    assert r["org"] == "Jammy Systems"


def test_s1_who_filed():
    assert filed(run(S1)) == {"rev_noble_1": True, "rev_focal_1": True,
                              "rev_jammy_1": True, "rev_lunar_1": False}


def test_s2_who_filed():
    assert filed(run(S2)) == {"rev_jammy_1": True, "rev_mantic_1": True}


def test_s3_nobody_filed():
    assert filed(run(S3)) == {"rev_lunar_1": False, "rev_noble_1": False}


def test_unknown_submission_fails():
    p = subprocess.run([TOOL, "00000000-0000-4000-8000-000000000000",
                        "--as-of", "2026-11-16", "--json"],
                       cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert p.returncode != 0


# 2. Where it stands

@pytest.mark.parametrize("sid, stage, peer, objection", [
    (S1, "peer_review", "2026-11-24", "2026-12-15"),
    (S2, "objection_resolution", "2026-11-03", "2026-11-24"),
    (S3, "peer_review", "2026-12-02", "2026-12-23"),
])
def test_stage_and_dates(sid, stage, peer, objection):
    r = run(sid)
    assert (r["stage"], r["peer_review_closes"], r["objection_resolution_closes"]) == (stage, peer, objection)


def test_not_in_review_has_no_stage():
    r = run(S6)
    assert r["status"] == "COMPLIANCE_CHECKING"
    assert r["stage"] is None


def test_s1_waiting_on_submitter():
    assert "submitter" in run(S1)["waiting_on"]


# 3. If you have time

def test_s1_penalty_stage():
    assert run(S1)["penalty_stage"] == 2
