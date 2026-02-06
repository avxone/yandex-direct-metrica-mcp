# Session 2026-02-06 (1) — Dashboard multi-account: empty datasets

## Completed
- Reproduced `dashboard.generate_option1` multi-account issue where `all_accounts=true` could produce empty per-account datasets.
- Identified root cause: Direct Reports API `ReportName` collisions across accounts (same `ReportName` reused for different `Client-Login`).
- Implemented fix: `dashboard.generate_option1` now sets a per-account unique `report_name` (includes `account_id`/`direct_client_login` + date range).
- Added regression test: `tests/test_dashboard_multi_account.py`.

## To Do
- Verify end-to-end in Docker with `all_accounts=true` and `output_dir=/data/...` (so the server can write files inside the container).
- If stable, publish a patch release `v2.0.4` (public + pro images).

