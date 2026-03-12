#!/usr/bin/env python3
"""TrustCloud API CLI client.

Self-contained client using only Python standard library.
All output is JSON.

Environment variables (auto-loaded from .env if not in environment):
    TRUSTCLOUD_API_KEY — Bearer token for TrustCloud API
"""

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid


BASE_URL = "https://api.trustcloud.ai"
API_VERSION = "1"

_env_loaded = False


def _load_env_file():
    """Load TRUSTCLOUD_* variables from .env if not already in the environment."""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True

    if os.environ.get("TRUSTCLOUD_API_KEY"):
        return

    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if key.startswith("TRUSTCLOUD_"):
                        os.environ.setdefault(key, value)
            break


def get_api_key():
    _load_env_file()
    raw = os.environ.get("TRUSTCLOUD_API_KEY")
    if not raw:
        error_exit("TRUSTCLOUD_API_KEY environment variable is not set")
    return raw


def error_exit(message):
    json.dump({"error": True, "message": message}, sys.stdout, indent=2)
    print()
    sys.exit(1)


def api_request(method, path, params=None, body=None):
    api_key = get_api_key()
    url = f"{BASE_URL}{path}"

    if params:
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            url += "?" + urllib.parse.urlencode(filtered)

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("x-trustcloud-api-version", API_VERSION)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"error": True, "message": raw.strip() or "Empty response"}
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8")
        except Exception:
            pass
        return {"error": True, "status": e.code, "message": e.reason, "body": body_text}
    except urllib.error.URLError as e:
        return {"error": True, "message": str(e.reason)}


def multipart_upload(path, file_path, fields):
    """Upload a file using multipart/form-data encoding."""
    api_key = get_api_key()
    url = f"{BASE_URL}{path}"
    boundary = uuid.uuid4().hex

    body_parts = []
    for key, value in fields.items():
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        )
        body_parts.append(f"{value}\r\n".encode())

    filename = os.path.basename(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
    )
    body_parts.append(f"Content-Type: {mime_type}\r\n\r\n".encode())
    with open(file_path, "rb") as f:
        body_parts.append(f.read())
    body_parts.append(b"\r\n")
    body_parts.append(f"--{boundary}--\r\n".encode())

    data = b"".join(body_parts)

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("x-trustcloud-api-version", API_VERSION)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"error": True, "message": raw.strip() or "Empty response"}
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8")
        except Exception:
            pass
        return {"error": True, "status": e.code, "message": e.reason, "body": body_text}
    except urllib.error.URLError as e:
        return {"error": True, "message": str(e.reason)}


def output(data):
    json.dump(data, sys.stdout, indent=2)
    print()


# -- Subcommand handlers -------------------------------------------------------


def cmd_validate(args):
    """Validate the API key."""
    output(api_request("GET", "/apikeys/me"))


def cmd_controls(args):
    """List all controls."""
    output(api_request("GET", "/controls"))


def cmd_control(args):
    """Get a single control by ID."""
    result = api_request("GET", f"/controls/{args.id}")
    if not result.get("error") and args.include_tests:
        tests = api_request("GET", f"/controls/{args.id}/tests")
        result["tests"] = tests
    output(result)


def cmd_tests(args):
    """List tests with optional filters."""
    params = {}
    if args.name:
        params["name"] = args.name
    if args.evidence_status:
        params["evidenceStatus"] = args.evidence_status
    if args.test_status:
        params["testStatus"] = args.test_status
    if args.due_by_date:
        params["evidenceDueByDate"] = args.due_by_date
    if args.due_by_days is not None:
        params["evidenceDueByDays"] = args.due_by_days
    output(api_request("GET", "/tests", params=params))


def cmd_test(args):
    """Get a single test by ID."""
    output(api_request("GET", f"/tests/{args.id}"))


def cmd_test_history(args):
    """Get test execution history."""
    output(api_request("GET", f"/tests/{args.id}/history"))


def cmd_evidence_history(args):
    """Get evidence history for a test."""
    output(api_request("GET", f"/tests/{args.id}/evidence/history"))


def cmd_submit_evidence(args):
    """Submit evidence to a test (link or file)."""
    if args.type == "link":
        if not args.url:
            error_exit("--url is required when submitting link evidence")
        body = {
            "type": "link",
            "url": args.url,
            "description": args.description or "",
            "evidenceDate": args.evidence_date or "",
        }
        output(api_request("POST", f"/tests/{args.id}/evidence", body=body))
    elif args.type == "file":
        if not args.file:
            error_exit("--file is required when submitting file evidence")
        if not os.path.isfile(args.file):
            error_exit(f"File not found: {args.file}")
        fields = {
            "type": "file",
            "description": args.description or "",
            "evidenceDate": args.evidence_date or "",
        }
        output(multipart_upload(f"/tests/{args.id}/evidence", args.file, fields))
    else:
        error_exit("--type must be 'link' or 'file'")


def cmd_execute_test(args):
    """Execute (pass/fail) a self-assessment test."""
    if args.answer not in ("yes", "no"):
        error_exit("--answer must be 'yes' (pass) or 'no' (fail)")
    body = {"answer": args.answer}
    if args.comment:
        body["comment"] = args.comment
    output(api_request("POST", f"/tests/{args.id}/execute", body=body))


def cmd_vendors(args):
    """List all vendors."""
    output(api_request("GET", "/vendors"))


def cmd_vendor(args):
    """Get a single vendor by ID."""
    result = api_request("GET", f"/vendors/{args.id}")
    if not result.get("error") and args.include_systems:
        systems = api_request("GET", f"/vendors/{args.id}/systems")
        result["systems"] = systems
    output(result)


def cmd_systems(args):
    """List all systems."""
    output(api_request("GET", "/systems"))


def cmd_system(args):
    """Get a single system by ID."""
    output(api_request("GET", f"/systems/{args.id}"))


def cmd_system_tests(args):
    """Get tests associated with a system."""
    output(api_request("GET", f"/systems/{args.id}/tests"))


def cmd_policies(args):
    """List all policies."""
    output(api_request("GET", "/policies"))


def cmd_policy(args):
    """Get a single policy by ID."""
    output(api_request("GET", f"/policies/{args.id}"))


def cmd_inventories(args):
    """List all inventories."""
    output(api_request("GET", "/inventories"))


def cmd_inventory(args):
    """Get a single inventory by ID."""
    output(api_request("GET", f"/inventories/{args.id}"))


# -- CLI setup -----------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trustcloud_api",
        description="TrustCloud API CLI client. All output is JSON.",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # validate
    sub.add_parser("validate", help="Validate API key and show key details")

    # controls
    sub.add_parser("controls", help="List all controls")

    # control
    p = sub.add_parser("control", help="Get a single control by ID")
    p.add_argument("--id", required=True, help="Control ID (UUID)")
    p.add_argument("--include-tests", action="store_true",
                   help="Also fetch tests for this control")

    # tests
    p = sub.add_parser("tests", help="List tests with optional filters")
    p.add_argument("--name", help="Filter by test name (partial match)")
    p.add_argument("--evidence-status",
                   choices=["missing", "due", "outdated", "up_to_date", "not_required"],
                   help="Filter by evidence status")
    p.add_argument("--test-status",
                   choices=["available", "in_progress", "excluded"],
                   help="Filter by test status")
    p.add_argument("--due-by-date", help="Tests with evidence due before date (YYYY-MM-DD)")
    p.add_argument("--due-by-days", type=int,
                   help="Tests with evidence due within N days")

    # test
    p = sub.add_parser("test", help="Get a single test by ID")
    p.add_argument("--id", required=True, help="Test ID (UUID)")

    # test-history
    p = sub.add_parser("test-history", help="Get test execution history")
    p.add_argument("--id", required=True, help="Test ID (UUID)")

    # evidence-history
    p = sub.add_parser("evidence-history", help="Get evidence history for a test")
    p.add_argument("--id", required=True, help="Test ID (UUID)")

    # submit-evidence
    p = sub.add_parser("submit-evidence", help="Submit evidence to a test")
    p.add_argument("--id", required=True, help="Test ID (UUID)")
    p.add_argument("--type", required=True, choices=["link", "file"],
                   help="Evidence type: 'link' or 'file'")
    p.add_argument("--url", help="URL for link evidence")
    p.add_argument("--file", help="File path for file evidence")
    p.add_argument("--description", help="Evidence description")
    p.add_argument("--evidence-date", help="Evidence date (YYYY/MM/DD)")

    # execute-test
    p = sub.add_parser("execute-test", help="Execute (pass/fail) a self-assessment test")
    p.add_argument("--id", required=True, help="Test ID (UUID)")
    p.add_argument("--answer", required=True, choices=["yes", "no"],
                   help="Test result: 'yes' (pass) or 'no' (fail)")
    p.add_argument("--comment", help="Optional assessment comment")

    # vendors
    sub.add_parser("vendors", help="List all vendors")

    # vendor
    p = sub.add_parser("vendor", help="Get a single vendor by ID")
    p.add_argument("--id", required=True, help="Vendor ID (UUID)")
    p.add_argument("--include-systems", action="store_true",
                   help="Also fetch systems for this vendor")

    # systems
    sub.add_parser("systems", help="List all systems")

    # system
    p = sub.add_parser("system", help="Get a single system by ID")
    p.add_argument("--id", required=True, help="System ID (UUID)")

    # system-tests
    p = sub.add_parser("system-tests", help="Get tests associated with a system")
    p.add_argument("--id", required=True, help="System ID (UUID)")

    # policies
    sub.add_parser("policies", help="List all policies")

    # policy
    p = sub.add_parser("policy", help="Get a single policy by ID")
    p.add_argument("--id", required=True, help="Policy ID (UUID)")

    # inventories
    sub.add_parser("inventories", help="List all inventories")

    # inventory
    p = sub.add_parser("inventory", help="Get a single inventory by ID")
    p.add_argument("--id", required=True, help="Inventory ID (UUID)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "validate": cmd_validate,
        "controls": cmd_controls,
        "control": cmd_control,
        "tests": cmd_tests,
        "test": cmd_test,
        "test-history": cmd_test_history,
        "evidence-history": cmd_evidence_history,
        "submit-evidence": cmd_submit_evidence,
        "execute-test": cmd_execute_test,
        "vendors": cmd_vendors,
        "vendor": cmd_vendor,
        "systems": cmd_systems,
        "system": cmd_system,
        "system-tests": cmd_system_tests,
        "policies": cmd_policies,
        "policy": cmd_policy,
        "inventories": cmd_inventories,
        "inventory": cmd_inventory,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
