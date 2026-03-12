---
name: trust-cloud
description: Interact with TrustCloud compliance platform via the TrustCloud API. Use when the user wants to manage compliance controls, view or submit evidence, execute tests, review vendors/systems/policies/inventories, or check compliance status. Supports listing controls, tests, vendors, systems, policies, and inventories, submitting evidence (links or files), executing self-assessment tests, and reviewing compliance posture. Even if the user just says "check compliance", "what evidence is due", "run the compliance check", or mentions TrustCloud, controls, or evidence, use this skill.
license: MIT
compatibility: Requires python3 and environment variable TRUSTCLOUD_API_KEY
metadata:
  version: "1.0.0"
  openclaw:
    requires:
      env:
        - TRUSTCLOUD_API_KEY
      bins:
        - python3
    primaryEnv: TRUSTCLOUD_API_KEY
    homepage: https://community.trustcloud.ai/docs/trustcloud-api/
---

# TrustCloud

Manage compliance controls, evidence, tests, vendors, systems, policies, and inventories through the TrustCloud API (v1).

## Environment Setup

The CLI script reads the `TRUSTCLOUD_API_KEY` environment variable.

The script **automatically loads** this from a `.env` file if it is not already in the environment. It searches for `.env` in the current working directory and in the skill's parent directory. No shell export is needed — just run the Python command directly.

**Get your API key:** Go to the "Integrations" page in your TrustCloud program > "API Access" (requires Compliance Admin role) > "Begin Setup" > Generate Key.
Direct: `https://app.trustcloud.ai` > Integrations > API Access

## Quick Start

All examples below assume a `.env` file with `TRUSTCLOUD_API_KEY` exists in the workspace root.

```bash
# Validate API key
python3 scripts/trustcloud_api.py validate

# List all controls
python3 scripts/trustcloud_api.py controls

# Get a specific control with its tests
python3 scripts/trustcloud_api.py control --id <uuid> --include-tests

# List tests with missing evidence
python3 scripts/trustcloud_api.py tests --evidence-status missing

# List tests with evidence due within 30 days
python3 scripts/trustcloud_api.py tests --due-by-days 30

# Get a specific test
python3 scripts/trustcloud_api.py test --id <uuid>

# View test execution history
python3 scripts/trustcloud_api.py test-history --id <uuid>

# View evidence history
python3 scripts/trustcloud_api.py evidence-history --id <uuid>

# Submit link evidence
python3 scripts/trustcloud_api.py submit-evidence --id <uuid> --type link \
  --url "https://example.com/evidence" --description "Quarterly review" \
  --evidence-date "2026/03/12"

# Submit file evidence
python3 scripts/trustcloud_api.py submit-evidence --id <uuid> --type file \
  --file /path/to/evidence.pdf --description "Audit report"

# Execute a self-assessment test (pass)
python3 scripts/trustcloud_api.py execute-test --id <uuid> --answer yes \
  --comment "Verified controls are in place"

# List vendors
python3 scripts/trustcloud_api.py vendors

# Get a vendor with its systems
python3 scripts/trustcloud_api.py vendor --id <uuid> --include-systems

# List systems
python3 scripts/trustcloud_api.py systems

# Get tests for a system
python3 scripts/trustcloud_api.py system-tests --id <uuid>

# List policies
python3 scripts/trustcloud_api.py policies

# Get a specific policy
python3 scripts/trustcloud_api.py policy --id <uuid>

# List inventories
python3 scripts/trustcloud_api.py inventories

# Get a specific inventory
python3 scripts/trustcloud_api.py inventory --id <uuid>
```

## Core Workflows

### Compliance Dashboard
1. Run `controls` to list all controls and their states.
2. Run `tests --evidence-status missing` to find tests needing evidence.
3. Run `tests --due-by-days 30` to find tests with upcoming deadlines.
4. Run `policies` to check policy approval statuses.

### Evidence Gap Analysis
1. Run `tests --evidence-status missing` to find all tests with missing evidence.
2. Run `tests --evidence-status due` to find tests with evidence coming due.
3. Run `tests --evidence-status outdated` to find tests with expired evidence.
4. For each test, run `test --id <uuid>` to get details including the question and recommendation.

### Evidence Submission
1. Identify the test that needs evidence using `tests` with filters.
2. Get test details with `test --id <uuid>` to understand what evidence is needed.
3. Submit link evidence: `submit-evidence --id <uuid> --type link --url "..." --description "..."`
4. Or submit file evidence: `submit-evidence --id <uuid> --type file --file /path/to/file --description "..."`
5. Verify with `evidence-history --id <uuid>` to confirm submission.

### Test Execution
1. Find available self-assessment tests: `tests --test-status available`
2. Review the test question: `test --id <uuid>`
3. Execute with pass/fail: `execute-test --id <uuid> --answer yes --comment "..."`
4. Verify with `test-history --id <uuid>` to confirm execution.

### Vendor & System Review
1. Run `vendors` to list all vendors.
2. For each vendor of interest, run `vendor --id <uuid> --include-systems` to see associated systems.
3. For each system, run `system-tests --id <uuid>` to review compliance tests.

### Policy Status Review
1. Run `policies` to list all policies and their approval statuses.
2. For each policy, run `policy --id <uuid>` to get full details.
3. Check `approvalStatus` and `policyState` fields to identify policies needing attention.

## Script Reference

All commands output JSON. Run `python3 scripts/trustcloud_api.py --help` for full usage.

| Command | Description |
|---------|-------------|
| `validate` | Validate API key and show key details |
| `controls` | List all controls |
| `control` | Get a single control by ID (optionally include tests) |
| `tests` | List tests with optional filters |
| `test` | Get a single test by ID |
| `test-history` | Get test execution history |
| `evidence-history` | Get evidence history for a test |
| `submit-evidence` | Submit link or file evidence to a test |
| `execute-test` | Execute (pass/fail) a self-assessment test |
| `vendors` | List all vendors |
| `vendor` | Get a single vendor by ID (optionally include systems) |
| `systems` | List all systems |
| `system` | Get a single system by ID |
| `system-tests` | Get tests associated with a system |
| `policies` | List all policies |
| `policy` | Get a single policy by ID |
| `inventories` | List all inventories |
| `inventory` | Get a single inventory by ID |

## API Reference

See [references/api-reference.md](./references/api-reference.md) for complete endpoint documentation, data models, and response schemas.
