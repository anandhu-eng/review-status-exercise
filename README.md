# Review status checker

We'd like you to build a small tool that tells a review chair where a submission stands in peer review. Use any language you like. All the data here is made up.

Feel free to use AI tools. Please share your whole screen, including the AI chat, and talk us through what you're doing: what you ask the AI, and what you keep or throw away.

## Background

Companies run the same AI benchmark (a fixed set of models and tests that everyone follows) on their own hardware and software, and publish how fast it ran (performance) and how good the answers were (accuracy). A **submission** is one company's set of results. Before anything is published, people from other companies check it for mistakes or rule breaks, so that the published numbers can be trusted and compared fairly.

A submission moves through these statuses:

1. `COMPLIANCE_CHECKING`: an automated checker validates the files.
2. `REVIEW_PENDING`: peer review. This is the part your tool is about.
3. `FINALIZED`: a review chair signs it off.
4. `PUBLISHED`: it goes public on the next publication date.

A submitter can pull out at any point (`WITHDRAWN`). There are a few other statuses you can treat as "not under review".

## How review works

Reviewers from other companies look at each submission. Every issue a reviewer raises is a **finding**. The submitter replies, and the reviewer either replies again or marks it resolved. A reviewer who finds nothing still files a finding to say so.

Review starts at `peer_review_started_at`. Peer review closes 21 days later and objection resolution 42 days later, both at 11:59 PM US Pacific time on that day.

## Data

**Database (read-only)**

```
URL:  https://mpgyuiepgsevezlivlxp.supabase.co
Key:  sb_publishable_hBLhTOAw_B4-2Lf_Q4pQgw_TThlpjJe

curl "https://mpgyuiepgsevezlivlxp.supabase.co/rest/v1/submissions?select=*" -H "apikey: sb_publishable_hBLhTOAw_B4-2Lf_Q4pQgw_TThlpjJe"
```

| Table | Useful columns |
|---|---|
| `orgs` | `org_id`, `org_name`, `org_display_name`, `user_ids` |
| `users` | `user_id`, `email`, `org_id`, `role`, `github_id` |
| `submissions` | `id`, `user_id` (submitter), `status`, `peer_review_started_at`, `finalized_at`, `withdrawn_at`, `confirmed_reviewer_ids`, `unconfirmed_reviewer_ids`, `penalties_imposed` |

A submission belongs to its submitter's org. It is under review only while `status` is `REVIEW_PENDING`.

**`reviews.csv`**

One row per finding. The review team keeps this file by hand.

| Column | Meaning |
|---|---|
| `submission_id`, `submitter_id` | which submission, and who submitted it |
| `finding_id` | the finding |
| `reviewed_by` | reviewer who filed it |
| `opened_at` | when it was filed |
| `review_state` | `awaiting_first_response` or `needs_submitter_reply` (waiting on the submitter), `needs_reviewer_reply` (waiting on the reviewer who filed it), or `resolved` |
| `last_reply_by`, `last_reply_at` | latest reply, if there is one |
| `title` | short description |

## What to build

A command like `review-status <submission_id> [--as-of YYYY-MM-DD]` that prints a report for one submission. `--as-of` defaults to today. Pick whatever output format reads well.

1. **Who is involved:** status, submitter and their org, the assigned reviewers (confirmed and unconfirmed) and their orgs, and which reviewers have filed something and which haven't.
2. **Where it stands:** for submissions under review, whether it's in peer review, objection resolution, or past both, with the closing dates in Pacific time. Group the findings by state and say who it's waiting on.
3. **If you have time:** for findings waiting on the submitter, how many weekdays they've been waiting. 3 days means a stage 1 penalty, 6 means stage 2, 10 means stage 3. Show the highest.

Where the data or this page is unclear, make a call and write it down in `NOTES.md`: what you decided, why, and how you checked it.

## Repo and checks

Work in this repo and push to `main` as often as you like. Each push runs the checks in `tests/` (see the Actions tab). They pass when:

- the repo root has an executable `review-status` (any language; if it needs building, add a `build.sh`; the runner is `ubuntu-latest`);
- `review-status <submission_id> --as-of 2026-11-16 --json` prints JSON like this, and exits non-zero for an unknown submission:

```json
{
  "submission_id": "3f1c9a20-...",
  "status": "REVIEW_PENDING",
  "submitter": "sub_jammy",
  "org": "Jammy Systems",
  "reviewers": [{"user_id": "rev_noble_1", "org": "Noble Compute", "confirmed": true, "filed": true}],
  "stage": "peer_review",
  "peer_review_closes": "2026-11-24",
  "objection_resolution_closes": "2026-12-15",
  "waiting_on": ["submitter", "rev_focal_1"],
  "penalty_stage": 2
}
```

`stage` and the two dates are `null` when the submission isn't under review. Dates are the Pacific-time day the window closes. `waiting_on` lists `"submitter"` and/or reviewer ids. `penalty_stage` is the highest stage from item 3, or `0` if nothing is waiting on the submitter or it isn't under review.

The checks don't cover everything, so passing them doesn't mean you're done. The run already on `main` fails because there's no tool yet; that's expected. Please don't edit `tests/` or `.github/`. On Windows, mark the file executable with `git update-index --chmod=+x review-status`.
