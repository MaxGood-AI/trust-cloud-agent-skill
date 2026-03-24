# Repository Guidelines

## Overview

This repository contains a Claude Skill for interacting with TrustCloud compliance platform. It is a single-file Python CLI (`scripts/trustcloud_api.py`) using only the Python standard library.

The CLI provides two levels of commands:
- **Composite commands** (`dashboard`, `gap-analysis`, `verify`, `batch-submit`, `batch-execute`) — high-level operations that combine multiple API calls into a single invocation, designed for complete compliance program workflows.
- **Resource commands** (`controls`, `tests`, `submit-evidence`, etc.) — low-level CRUD operations for individual resources.

## File Roles

- **SKILL.md** -- Claude Skill definition file. This is what Claude Code reads when the skill is invoked. It describes available commands, workflows, and configuration. Keep it in sync with the actual CLI capabilities.
- **scripts/trustcloud_api.py** -- The CLI implementation. All commands output JSON to stdout.
- **references/api-reference.md** -- TrustCloud API v1 documentation. Use this as the source of truth for endpoints, request/response models, and field definitions.

## Adding a New Command

1. Write a `cmd_<name>(args)` handler function in `scripts/trustcloud_api.py`.
2. Add a subparser for the command in `build_parser()`.
3. Add the command name and handler to the `commands` dict in `main()`.
4. Update `SKILL.md` to document the new command in both the Quick Start examples and the Script Reference table.
5. If the command supports `--format text`, add a `fmt_<name>(data)` formatter function.
6. For write operations, consider adding `--stdin` support to keep command lines short and predictable.

## Environment Setup

One environment variable is required:
- `TRUSTCLOUD_API_KEY` -- Bearer token from TrustCloud (Integrations > API Access). Used directly as `Authorization: Bearer <key>`.

One environment variable is optional:
- `TRUSTCLOUD_TRUST_PAGE` -- TrustShare URL (e.g. `https://my-org.trustshare.com`). Enables `ts-*` commands that access the TrustShare backend at `backend.trustcloud.ai`. The TrustShare backend uses public client credentials embedded in the TrustShare SPA (not user secrets) and authenticates via `X-Kintent-Auth` header with the `Origin` header set to the trust page URL.

The script also sends `x-trustcloud-api-version: 1` with every request to the standard API.

## Code Style

- Python: PEP 8, 4-space indentation, `snake_case` functions and variables.
- No third-party dependencies. stdlib only.
- Default output is JSON via `json.dump` to stdout. When `--format text` is specified, output human-readable text via `output_text()`.
- Errors must exit with `error_exit()` which outputs JSON and sets exit code 1.
- Write operations (`submit-evidence`, `execute-test`) support `--stdin` for JSON input to keep command lines short.
- Composite commands (`dashboard`, `gap-analysis`, `verify`, `batch-submit`, `batch-execute`) combine multiple API calls into one invocation.

## Testing

There is no test suite. To verify changes, run commands against a real TrustCloud instance with valid credentials:
```bash
export TRUSTCLOUD_API_KEY="your-key"
python3 scripts/trustcloud_api.py validate
python3 scripts/trustcloud_api.py controls
python3 scripts/trustcloud_api.py tests --evidence-status missing
```

## Commit Style

- **Subject line**: short imperative verb phrase under ~72 chars (e.g., `Add evidence submission command`). Start with a verb: `Add`, `Fix`, `Update`.
- **Body** (for non-trivial changes): use markdown formatting with `## Problem`, `## Solution`, and `## Verified` sections to explain *why* the change was made, *what* was done, and *how* it was validated. If the change adds or modifies environment variables, note the impact in the body.
- **Trivial changes**: only typo corrections are considered trivial and may omit the body. All other changes deserve the full message format.
- **KanbanZone**: append the relevant Roadmap board card URL (e.g., `https://kanbanzone.io/b/QJxJGohF/c/455`) as the last line before `Co-Authored-By`.
- **Co-authorship**: when AI-assisted, end with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` (or the model used).

## API Notes

- Base URL: `https://api.trustcloud.ai`
- Auth: `Authorization: Bearer <api-key>` plus `x-trustcloud-api-version: 1`
- All object IDs are UUID v4 format.
- The API is read-heavy with limited write operations (evidence submission and test execution only).
- Self-assessment tests can be executed via API; automated tests are managed via TrustCloud integrations.

### TrustShare Backend

- Base URL: `https://backend.trustcloud.ai`
- Auth: Public client credentials via `X-Kintent-Auth` header. Two-step flow:
  1. `POST /auth/public/login` with `X-Kintent-Auth: Basic <base64(client_id:client_secret)>` and `Origin: https://<subdomain>.trustshare.com` — returns `{token, teamId}`
  2. Subsequent requests use `X-Kintent-Auth: Bearer <token>` with same `Origin` header
- The public client ID and secret are embedded in the TrustShare SPA JavaScript bundle (not user secrets).
- The `GET /policies` endpoint on this backend returns full policy data, unlike the standard API which has a known bug returning empty.
- TrustShare-specific endpoints: `/frameworks`, `/teams/{teamId}/certifications`, `/teams/{teamId}/documents`, `/v2/search`

## Synchronization Rule

If both `AGENTS.md` and `CLAUDE.md` exist in this directory, they must be identical in content and updated together in the same commit. Do not allow them to drift.
