# Repository Guidelines

## Overview

This repository contains a Claude Skill for interacting with TrustCloud compliance platform. It is a single-file Python CLI (`scripts/trustcloud_api.py`) using only the Python standard library.

## File Roles

- **SKILL.md** -- Claude Skill definition file. This is what Claude Code reads when the skill is invoked. It describes available commands, workflows, and configuration. Keep it in sync with the actual CLI capabilities.
- **scripts/trustcloud_api.py** -- The CLI implementation. All commands output JSON to stdout.
- **references/api-reference.md** -- TrustCloud API v1 documentation. Use this as the source of truth for endpoints, request/response models, and field definitions.

## Adding a New Command

1. Write a `cmd_<name>(args)` handler function in `scripts/trustcloud_api.py`.
2. Add a subparser for the command in `build_parser()`.
3. Add the command name and handler to the `commands` dict in `main()`.
4. Update `SKILL.md` to document the new command in both the Quick Start examples and the Script Reference table.

## Environment Setup

One environment variable is required:
- `TRUSTCLOUD_API_KEY` -- Bearer token from TrustCloud (Integrations > API Access). Used directly as `Authorization: Bearer <key>`.

The script also sends `x-trustcloud-api-version: 1` with every request.

## Code Style

- Python: PEP 8, 4-space indentation, `snake_case` functions and variables.
- No third-party dependencies. stdlib only.
- All CLI output must be valid JSON via `json.dump` to stdout.
- Errors must exit with `error_exit()` which outputs JSON and sets exit code 1.

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
