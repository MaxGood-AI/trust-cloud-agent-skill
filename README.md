# TrustCloud CLI Skill for Claude Code, Codex & OpenClaw

Manage your entire [TrustCloud](https://trustcloud.ai) compliance program — controls, evidence, tests, vendors, policies, and more — directly from your AI coding agent or terminal. One self-contained Python script, zero dependencies beyond the standard library.

## Why This Exists

SOC 2, GDPR, HIPAA, and other compliance frameworks require continuous evidence collection, test execution, and posture monitoring. Traditionally this means context-switching to a web dashboard, clicking through forms, and manually uploading screenshots. This skill brings the full TrustCloud API (and TrustShare) into your development workflow so your AI agent can assess compliance posture, identify evidence gaps, submit evidence, and execute tests — all without leaving the terminal.

## Key Features

- **Full compliance dashboard in one command** — control counts, evidence gaps, policy statuses, and actionable recommendations
- **Evidence gap analysis** — instantly find every test with missing, due, or outdated evidence, grouped by control
- **Submit evidence** (links or files) and **execute self-assessment tests** individually or in batch
- **TrustShare integration** — access your public trust page data: policies with compliance mappings, frameworks (SOC 2, GDPR, HIPAA, etc.), certifications, shared documents, subprocessors, and full-text search across all compliance data
- **Vendor, system, and inventory management** — review vendor risk, system-level test coverage, and asset inventories
- **JSON and human-readable output** — structured JSON by default for programmatic use, `--format text` for readable reports
- **Zero dependencies** — single-file Python 3 script using only the standard library (`urllib`, `json`, `argparse`, `base64`)
- **Works everywhere** — compatible with Claude Code (Anthropic), OpenAI Codex, OpenClaw, or any CLI environment

## Quick Start

### 1. Get Your API Key

Go to [TrustCloud](https://app.trustcloud.ai) > **Integrations** > **API Access** (requires Compliance Admin role) > **Begin Setup** > Generate Key.

### 2. Configure Environment

Create a `.env` file in your project root (or export the variables):

```bash
TRUSTCLOUD_API_KEY=your-api-key-here

# Optional: enable TrustShare commands (policies, frameworks, certifications, search)
TRUSTCLOUD_TRUST_PAGE=https://your-org.trustshare.com
```

The script auto-loads `.env` from the current working directory or the skill's parent directory — no shell export needed.

### 3. Validate

```bash
python3 scripts/trustcloud_api.py validate
```

## Usage

### Compliance Posture Overview

```bash
# Full dashboard: controls, evidence gaps, and policy statuses
python3 scripts/trustcloud_api.py --format text dashboard

# Detailed evidence gap report with test questions and recommendations
python3 scripts/trustcloud_api.py --format text gap-analysis
```

### Evidence & Test Management

```bash
# Find tests with missing evidence
python3 scripts/trustcloud_api.py --format text tests --evidence-status missing

# Find evidence due within 30 days
python3 scripts/trustcloud_api.py --format text tests --due-by-days 30

# Submit link evidence
python3 scripts/trustcloud_api.py submit-evidence --id <test-uuid> --type link \
  --url "https://..." --description "Quarterly access review"

# Submit file evidence
echo '{"id":"<test-uuid>","type":"file","file":"/path/to/report.pdf","description":"Audit report"}' \
  | python3 scripts/trustcloud_api.py submit-evidence --stdin

# Execute a self-assessment test
python3 scripts/trustcloud_api.py execute-test --id <test-uuid> --answer yes \
  --comment "Controls verified in place"

# Batch submit evidence from a JSON file
python3 scripts/trustcloud_api.py batch-submit --file evidence.json

# Batch execute tests from a JSON file
python3 scripts/trustcloud_api.py batch-execute --file executions.json

# Verify submissions were recorded
python3 scripts/trustcloud_api.py --format text verify --ids "<uuid1>,<uuid2>"
```

### TrustShare (Public Trust Page)

Requires `TRUSTCLOUD_TRUST_PAGE` in your environment. These commands access the same data your customers see on your public trust page, plus compliance mappings.

```bash
# Combined overview: policies, frameworks, certifications, documents
python3 scripts/trustcloud_api.py --format text ts-overview

# List all policies (works even when the standard API has issues)
python3 scripts/trustcloud_api.py --format text ts-policies

# Get a policy with its compliance framework mappings
python3 scripts/trustcloud_api.py --format text ts-policy --id <uuid>

# List compliance frameworks (SOC 2, GDPR, HIPAA, etc.)
python3 scripts/trustcloud_api.py --format text ts-frameworks

# List certifications (e.g. SOC 2 Type 2 reports)
python3 scripts/trustcloud_api.py --format text ts-certifications

# Search across all compliance data
python3 scripts/trustcloud_api.py ts-search --query "encryption"
```

### Vendors, Systems & Inventories

```bash
python3 scripts/trustcloud_api.py --format text vendors
python3 scripts/trustcloud_api.py vendor --id <uuid> --include-systems
python3 scripts/trustcloud_api.py system-tests --id <uuid>
python3 scripts/trustcloud_api.py --format text inventories
```

## Complete Command Reference

| Command | Description |
|---------|-------------|
| **Composite** | |
| `dashboard` | Full compliance posture overview |
| `gap-analysis` | Detailed evidence gap report |
| `verify` | Verify evidence/execution status for test IDs |
| `batch-submit` | Submit evidence to multiple tests (JSON file or stdin) |
| `batch-execute` | Execute multiple self-assessment tests (JSON file or stdin) |
| **Controls & Tests** | |
| `controls` | List all controls |
| `control` | Get a control by ID (optionally include tests) |
| `tests` | List tests with filters (`--evidence-status`, `--due-by-days`, `--test-status`) |
| `test` | Get a single test by ID |
| `test-history` | Get test execution history |
| `evidence-history` | Get evidence history for a test |
| `submit-evidence` | Submit link or file evidence (flags or `--stdin`) |
| `execute-test` | Execute a self-assessment test (flags or `--stdin`) |
| **Vendors & Systems** | |
| `vendors` | List all vendors |
| `vendor` | Get a vendor by ID (optionally include systems) |
| `systems` | List all systems |
| `system` | Get a system by ID |
| `system-tests` | Get tests for a system |
| **Policies & Inventories** | |
| `policies` | List all policies |
| `policy` | Get a policy by ID |
| `inventories` | List all inventories |
| `inventory` | Get an inventory by ID |
| `validate` | Validate API key |
| **TrustShare** (require `TRUSTCLOUD_TRUST_PAGE`) | |
| `ts-overview` | Combined view: policies + frameworks + certs + docs |
| `ts-policies` | List all policies via TrustShare |
| `ts-policy` | Get a policy with compliance mappings |
| `ts-frameworks` | List compliance frameworks |
| `ts-framework` | Get framework sections with controls |
| `ts-certifications` | List certifications |
| `ts-documents` | List shared compliance documents |
| `ts-subprocessors` | List subprocessors (vendors) |
| `ts-controls` | List controls with compliance mappings |
| `ts-search` | Full-text search across all TrustShare data |

All commands output JSON by default. Add `--format text` for human-readable output.

## Typical Compliance Maintenance Workflow

1. **Assess** — `dashboard` to understand current posture
2. **Identify gaps** — `gap-analysis` to find all evidence gaps with details
3. **Plan** — review the output, determine what evidence to gather
4. **Submit evidence** — `batch-submit` or `submit-evidence` for each item
5. **Execute tests** — `batch-execute` or `execute-test` for self-assessments
6. **Verify** — `verify --ids <ids>` to confirm everything was recorded
7. **Re-assess** — `dashboard` to confirm posture improvement

## License

MIT
