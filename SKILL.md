---
name: trust-cloud
description: Interact with TrustCloud compliance platform via the TrustCloud API. Use when the user wants to manage compliance controls, view or submit evidence, execute tests, review vendors/systems/policies/inventories, or check compliance status. Supports listing controls, tests, vendors, systems, policies, and inventories, submitting evidence (links or files), executing self-assessment tests, and reviewing compliance posture. Even if the user just says "check compliance", "what evidence is due", "run the compliance check", or mentions TrustCloud, controls, or evidence, use this skill.
license: MIT
compatibility: Requires python3 and environment variable TRUSTCLOUD_API_KEY
metadata:
  version: "3.0.0"
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

Manage compliance controls, evidence, tests, vendors, systems, policies, and inventories through the TrustCloud API (v1). Optionally access policies, frameworks, certifications, and documents via the TrustShare backend.

## Environment Setup

The CLI script reads the `TRUSTCLOUD_API_KEY` environment variable.

The script **automatically loads** this from a `.env` file if it is not already in the environment. It searches for `.env` in the current working directory and in the skill's parent directory. No shell export is needed — just run the Python command directly.

**Get your API key:** Go to the "Integrations" page in your TrustCloud program > "API Access" (requires Compliance Admin role) > "Begin Setup" > Generate Key.
Direct: `https://app.trustcloud.ai` > Integrations > API Access

### TrustShare Integration (Optional)

Set `TRUSTCLOUD_TRUST_PAGE` to your TrustShare URL to enable `ts-*` commands that access policies, frameworks, certifications, and documents via the TrustShare backend. This is particularly valuable because the standard TrustCloud API `GET /policies` endpoint has a known bug that returns empty results.

```bash
# In .env
TRUSTCLOUD_TRUST_PAGE=https://your-org.trustshare.com
```

When `TRUSTCLOUD_TRUST_PAGE` is set:
- `ts-*` commands become available (policies, frameworks, certifications, documents, search)
- The `dashboard` command automatically substitutes TrustShare policy data when the standard API returns empty

## Quick Start

All examples below assume a `.env` file with `TRUSTCLOUD_API_KEY` exists in the workspace root.

```bash
# Full compliance posture overview (single call)
python3 scripts/trustcloud_api.py dashboard

# Same, but human-readable output
python3 scripts/trustcloud_api.py --format text dashboard

# Detailed evidence gap report
python3 scripts/trustcloud_api.py --format text gap-analysis

# Submit evidence via stdin (short, predictable command)
echo '{"id":"<uuid>","type":"link","url":"https://...","description":"..."}' | python3 scripts/trustcloud_api.py submit-evidence --stdin

# Execute a test via stdin
echo '{"id":"<uuid>","answer":"yes","comment":"Verified"}' | python3 scripts/trustcloud_api.py execute-test --stdin

# Batch submit evidence from a JSON file
python3 scripts/trustcloud_api.py batch-submit --file evidence.json

# Batch execute tests from a JSON file
python3 scripts/trustcloud_api.py batch-execute --file executions.json

# Verify evidence was submitted for specific tests
python3 scripts/trustcloud_api.py --format text verify --ids "<uuid1>,<uuid2>"

# Validate API key
python3 scripts/trustcloud_api.py validate

# --- TrustShare commands (require TRUSTCLOUD_TRUST_PAGE) ---

# List all policies (works even when standard API returns empty)
python3 scripts/trustcloud_api.py --format text ts-policies

# Combined overview: policies + frameworks + certifications + documents
python3 scripts/trustcloud_api.py --format text ts-overview

# List compliance frameworks
python3 scripts/trustcloud_api.py --format text ts-frameworks

# Get policy detail with compliance mappings
python3 scripts/trustcloud_api.py --format text ts-policy --id <uuid>

# Search across all compliance data
python3 scripts/trustcloud_api.py ts-search --query "encryption"
```

## Output Format

All commands output JSON by default. Add `--format text` before the command for human-readable output:

```bash
python3 scripts/trustcloud_api.py --format text dashboard
python3 scripts/trustcloud_api.py --format text gap-analysis
python3 scripts/trustcloud_api.py --format text tests --evidence-status missing
python3 scripts/trustcloud_api.py --format text controls
python3 scripts/trustcloud_api.py --format text policies
python3 scripts/trustcloud_api.py --format text verify --ids "<uuid1>,<uuid2>"
```

## Core Workflows

### 1. Compliance Assessment (single command)

Run `dashboard` to get a complete posture overview — control counts by state, evidence gaps (missing/due/outdated), and policy approval statuses — all in one call.

```bash
python3 scripts/trustcloud_api.py --format text dashboard
```

### 2. Evidence Gap Analysis (single command)

Run `gap-analysis` to get every test with missing, due, or outdated evidence — including test questions, recommendations, control mappings, and due dates.

```bash
python3 scripts/trustcloud_api.py --format text gap-analysis
```

### 3. Evidence Submission

**Single submission via stdin:**
```bash
echo '{"id":"<test-uuid>","type":"link","url":"https://...","description":"Quarterly review","evidenceDate":"2026/03/12"}' | python3 scripts/trustcloud_api.py submit-evidence --stdin
```

**File evidence via stdin:**
```bash
echo '{"id":"<test-uuid>","type":"file","file":"/path/to/report.pdf","description":"Audit report"}' | python3 scripts/trustcloud_api.py submit-evidence --stdin
```

**Batch submission from a JSON file:**
```bash
python3 scripts/trustcloud_api.py batch-submit --file evidence.json
```

The JSON file format:
```json
{
  "submissions": [
    {"id": "<test-uuid>", "type": "link", "url": "https://...", "description": "..."},
    {"id": "<test-uuid>", "type": "file", "file": "/path/to/file.pdf", "description": "..."}
  ]
}
```

**Batch submission from stdin:**
```bash
echo '[{"id":"...","type":"link","url":"...","description":"..."}]' | python3 scripts/trustcloud_api.py batch-submit --stdin
```

### 4. Test Execution

**Single test via stdin:**
```bash
echo '{"id":"<test-uuid>","answer":"yes","comment":"Controls verified in place"}' | python3 scripts/trustcloud_api.py execute-test --stdin
```

**Batch execution from a JSON file:**
```bash
python3 scripts/trustcloud_api.py batch-execute --file executions.json
```

The JSON file format:
```json
{
  "executions": [
    {"id": "<test-uuid>", "answer": "yes", "comment": "Verified"},
    {"id": "<test-uuid>", "answer": "no", "comment": "Needs remediation"}
  ]
}
```

**Batch execution from stdin:**
```bash
echo '[{"id":"...","answer":"yes","comment":"..."}]' | python3 scripts/trustcloud_api.py batch-execute --stdin
```

### 5. Verification

After submitting evidence or executing tests, verify everything was recorded:

```bash
python3 scripts/trustcloud_api.py --format text verify --ids "<uuid1>,<uuid2>,<uuid3>"
```

Or verify from a list on stdin:
```bash
echo '["<uuid1>","<uuid2>"]' | python3 scripts/trustcloud_api.py --format text verify --stdin
```

### 6. Complete Compliance Program Cycle

A full compliance maintenance session follows this sequence:

1. **Assess**: `dashboard` — understand current posture
2. **Identify gaps**: `gap-analysis` — find all evidence gaps with details
3. **Plan**: review gap-analysis output, determine what evidence to submit and which tests to execute
4. **Submit evidence**: `batch-submit` or `submit-evidence --stdin` for each piece of evidence
5. **Execute tests**: `batch-execute` or `execute-test --stdin` for self-assessment tests
6. **Verify**: `verify --ids <submitted-test-ids>` — confirm everything was recorded
7. **Re-assess**: `dashboard` — confirm posture improvement

### 7. Vendor & System Review

```bash
python3 scripts/trustcloud_api.py vendors
python3 scripts/trustcloud_api.py vendor --id <uuid> --include-systems
python3 scripts/trustcloud_api.py system-tests --id <uuid>
```

### 8. Policy Status Review

```bash
python3 scripts/trustcloud_api.py --format text policies
python3 scripts/trustcloud_api.py policy --id <uuid>
```

## Low-Level Commands

These remain available for targeted lookups. Most workflows should use the composite commands above.

```bash
# List/filter tests
python3 scripts/trustcloud_api.py tests --evidence-status missing
python3 scripts/trustcloud_api.py tests --due-by-days 30
python3 scripts/trustcloud_api.py tests --test-status available

# Get single resources
python3 scripts/trustcloud_api.py test --id <uuid>
python3 scripts/trustcloud_api.py control --id <uuid> --include-tests
python3 scripts/trustcloud_api.py test-history --id <uuid>
python3 scripts/trustcloud_api.py evidence-history --id <uuid>

# Submit evidence (flag-based, for simple cases)
python3 scripts/trustcloud_api.py submit-evidence --id <uuid> --type link --url "https://..." --description "..."

# Execute test (flag-based, for simple cases)
python3 scripts/trustcloud_api.py execute-test --id <uuid> --answer yes --comment "..."
```

## Script Reference

All commands output JSON by default. Add `--format text` for human-readable output where supported.

| Command | Description |
|---------|-------------|
| **Composite commands** | |
| `dashboard` | Full compliance posture overview (controls + evidence gaps + policies) |
| `gap-analysis` | Detailed evidence gap report (missing + due + outdated tests with details) |
| `verify` | Verify evidence/execution status for given test IDs |
| `batch-submit` | Submit evidence to multiple tests from JSON file or stdin |
| `batch-execute` | Execute multiple self-assessment tests from JSON file or stdin |
| **Resource commands** | |
| `validate` | Validate API key and show key details |
| `controls` | List all controls |
| `control` | Get a single control by ID (optionally include tests) |
| `tests` | List tests with optional filters |
| `test` | Get a single test by ID |
| `test-history` | Get test execution history |
| `evidence-history` | Get evidence history for a test |
| `submit-evidence` | Submit link or file evidence to a test (flags or --stdin) |
| `execute-test` | Execute (pass/fail) a self-assessment test (flags or --stdin) |
| `vendors` | List all vendors |
| `vendor` | Get a single vendor by ID (optionally include systems) |
| `systems` | List all systems |
| `system` | Get a single system by ID |
| `system-tests` | Get tests associated with a system |
| `policies` | List all policies |
| `policy` | Get a single policy by ID |
| `inventories` | List all inventories |
| `inventory` | Get a single inventory by ID |
| **TrustShare commands** (require `TRUSTCLOUD_TRUST_PAGE`) | |
| `ts-policies` | List all policies via TrustShare (solves empty standard API) |
| `ts-policy` | Get a policy with compliance mappings via TrustShare |
| `ts-frameworks` | List all compliance frameworks (SOC 2, GDPR, HIPAA, etc.) |
| `ts-framework` | Get framework sections with controls |
| `ts-certifications` | List certifications (SOC 2 reports) |
| `ts-documents` | List shared compliance documents |
| `ts-subprocessors` | List subprocessors (vendors) |
| `ts-controls` | List controls with compliance mappings |
| `ts-search` | Search across all TrustShare compliance data |
| `ts-overview` | Combined view: policies + frameworks + certs + docs |

## API Reference

See [references/api-reference.md](./references/api-reference.md) for complete endpoint documentation, data models, and response schemas.
