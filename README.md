# trust-cloud

A Claude Skill (also compatible with OpenClaw and Codex) for managing compliance via the [TrustCloud](https://trustcloud.ai) API v1.

Single-file Python CLI using only the standard library. All output is JSON.

## Setup

```bash
export TRUSTCLOUD_API_KEY="your-api-key"   # Integrations > API Access (requires Compliance Admin)
```

## Usage

```bash
python3 scripts/trustcloud_api.py validate                          # Validate API key
python3 scripts/trustcloud_api.py controls                          # List all controls
python3 scripts/trustcloud_api.py tests --evidence-status missing   # Find missing evidence
python3 scripts/trustcloud_api.py tests --due-by-days 30            # Evidence due within 30 days
python3 scripts/trustcloud_api.py submit-evidence --id <uuid> --type link --url "https://..."  # Submit evidence
python3 scripts/trustcloud_api.py execute-test --id <uuid> --answer yes   # Pass a test
python3 scripts/trustcloud_api.py vendors                           # List vendors
python3 scripts/trustcloud_api.py policies                          # List policies
```

Run `python3 scripts/trustcloud_api.py --help` for all commands and options.

## License

MIT
