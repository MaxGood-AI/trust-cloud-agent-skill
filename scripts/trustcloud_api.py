#!/usr/bin/env python3
"""TrustCloud API CLI client.

Self-contained client using only Python standard library.
Output is JSON by default; use --format text for human-readable output.

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


def api_request_paginated(path, params=None, max_limit=50):
    """GET a list endpoint with automatic pagination. Returns all items."""
    all_items = []
    page = 1
    base_params = dict(params) if params else {}
    base_params["limit"] = max_limit

    while True:
        base_params["page"] = page
        result = api_request("GET", path, params=base_params)
        if is_error(result):
            return result
        batch = safe_list(result)
        if not batch:
            break
        all_items.extend(batch)
        if len(batch) < max_limit:
            break
        page += 1

    return all_items


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


def output_text(text):
    print(text)


def is_error(data):
    return isinstance(data, dict) and data.get("error")


def safe_list(data):
    return data if isinstance(data, list) else []


def count_by(items, field):
    counts = {}
    for item in items:
        val = item.get(field, "unknown") if isinstance(item, dict) else "unknown"
        counts[val] = counts.get(val, 0) + 1
    return counts


def read_json_input(args):
    """Read JSON from --file or stdin (--stdin flag)."""
    if hasattr(args, "file") and args.file:
        with open(args.file) as f:
            return json.load(f)
    if hasattr(args, "stdin") and args.stdin:
        return json.load(sys.stdin)
    return None


# -- Text formatters -----------------------------------------------------------


def fmt_dashboard(data):
    lines = ["=== TrustCloud Compliance Dashboard ===", ""]

    c = data.get("controls", {})
    lines.append(f"CONTROLS: {c.get('total', 0)} total")
    for state, count in sorted(c.get("by_state", {}).items()):
        lines.append(f"  {state}: {count}")
    lines.append("")

    e = data.get("evidence", {})
    total_gaps = e.get("missing", 0) + e.get("due", 0) + e.get("outdated", 0)
    lines.append("EVIDENCE GAPS:")
    lines.append(f"  Missing:  {e.get('missing', 0)} tests")
    lines.append(f"  Due soon: {e.get('due', 0)} tests")
    lines.append(f"  Outdated: {e.get('outdated', 0)} tests")
    lines.append(f"  Total:    {total_gaps} tests need attention")
    lines.append("")

    p = data.get("policies", {})
    p_total = p.get("total", 0)
    lines.append(f"POLICIES: {p_total} total")
    if p_total == 0:
        lines.append("  (API returned no policies — check TrustCloud web UI for authoritative count)")
    else:
        for status, count in sorted(p.get("by_approval_status", {}).items()):
            lines.append(f"  {status}: {count}")
    lines.append("")

    attn = data.get("tests_needing_attention", [])
    if attn:
        lines.append(f"TESTS NEEDING ATTENTION ({len(attn)}):")
        for t in attn:
            name = t.get("name", "?")
            status = t.get("evidenceStatus", "?")
            due = t.get("nextEvidenceDueDate", "")
            tid = t.get("id", "?")
            ctrl = t.get("control", {})
            ctrl_name = ctrl.get("name", "") if isinstance(ctrl, dict) else ""
            due_str = f", due: {due}" if due else ""
            ctrl_str = f" (Control: {ctrl_name})" if ctrl_name else ""
            lines.append(f"  [{status}] {name}{ctrl_str}{due_str}")
            lines.append(f"           id: {tid}")

    return "\n".join(lines)


def fmt_gap_analysis(data):
    lines = ["=== Evidence Gap Analysis ===", ""]

    for category, label in [("missing", "MISSING EVIDENCE"), ("due", "DUE SOON"), ("outdated", "OUTDATED")]:
        items = data.get(category, [])
        lines.append(f"{label} ({len(items)} tests):")
        if not items:
            lines.append("  (none)")
        for i, t in enumerate(items, 1):
            name = t.get("name", "?")
            tid = t.get("id", "?")
            question = t.get("question", "")
            recommendation = t.get("recommendation", "")
            due = t.get("nextEvidenceDueDate", "")
            ctrl = t.get("control", {})
            ctrl_name = ctrl.get("name", "") if isinstance(ctrl, dict) else ""
            lines.append(f"  {i}. {name}")
            if ctrl_name:
                lines.append(f"     Control: {ctrl_name}")
            if due:
                lines.append(f"     Due: {due}")
            if question:
                lines.append(f"     Question: {question}")
            if recommendation:
                lines.append(f"     Recommendation: {recommendation}")
            lines.append(f"     ID: {tid}")
        lines.append("")

    lines.append(f"TOTAL: {data.get('total_gaps', 0)} evidence gaps")
    return "\n".join(lines)


def fmt_verify(data):
    lines = ["=== Verification Report ===", ""]

    for v in data.get("verifications", []):
        test = v.get("test", {})
        name = test.get("name", "?")
        tid = test.get("id", "?")
        ev_status = test.get("evidenceStatus", "?")
        lines.append(f"Test: {name}")
        lines.append(f"  ID: {tid}")
        lines.append(f"  Evidence status: {ev_status}")

        ev_hist = v.get("evidence_history", [])
        if isinstance(ev_hist, list) and ev_hist:
            latest = ev_hist[0]
            lines.append(f"  Latest evidence: {latest.get('type', '?')} — {latest.get('description', '')}")
        else:
            lines.append("  No evidence submitted")

        ex_hist = v.get("execution_history", [])
        if isinstance(ex_hist, list) and ex_hist:
            latest = ex_hist[0]
            lines.append(f"  Latest execution: {latest.get('executionOutcome', '?')}")
        else:
            lines.append("  No execution history")

        ok = ev_status in ("up_to_date", "not_required")
        lines.append(f"  {'VERIFIED' if ok else 'NEEDS ATTENTION'}")
        lines.append("")

    return "\n".join(lines)


def fmt_batch_results(data):
    lines = ["=== Batch Operation Results ===", ""]
    results = data.get("results", [])
    succeeded = sum(1 for r in results if not is_error(r.get("result", {})))
    failed = len(results) - succeeded
    lines.append(f"Total: {len(results)}, Succeeded: {succeeded}, Failed: {failed}")
    lines.append("")
    for r in results:
        tid = r.get("id", "?")
        result = r.get("result", {})
        if is_error(result):
            lines.append(f"  FAILED  {tid}: {result.get('message', '?')}")
        else:
            lines.append(f"  OK      {tid}")
    return "\n".join(lines)


def fmt_tests(data):
    items = safe_list(data)
    lines = [f"=== Tests ({len(items)}) ===", ""]
    for t in items:
        name = t.get("name", "?")
        tid = t.get("id", "?")
        ev_status = t.get("evidenceStatus", "?")
        test_type = t.get("type", "?")
        due = t.get("nextEvidenceDueDate", "")
        ctrl = t.get("control", {})
        ctrl_name = ctrl.get("name", "") if isinstance(ctrl, dict) else ""
        due_str = f"  due: {due}" if due else ""
        lines.append(f"  [{ev_status}] {name} ({test_type})")
        if ctrl_name:
            lines.append(f"           Control: {ctrl_name}")
        if due_str:
            lines.append(f"          {due_str}")
        lines.append(f"           ID: {tid}")
    return "\n".join(lines)


def fmt_controls(data):
    items = safe_list(data)
    lines = [f"=== Controls ({len(items)}) ===", ""]
    for c in items:
        name = c.get("controlName", "?")
        state = c.get("state", "?")
        cat = c.get("category", "")
        cid = c.get("id", "?")
        lines.append(f"  [{state}] {name}")
        if cat:
            lines.append(f"           Category: {cat}")
        lines.append(f"           ID: {cid}")
    return "\n".join(lines)


def fmt_policies(data):
    items = safe_list(data)
    lines = [f"=== Policies ({len(items)}) ===", ""]
    for p in items:
        title = p.get("title", "?")
        status = p.get("approvalStatus", "?")
        state = p.get("policyState", "?")
        pid = p.get("id", "?")
        lines.append(f"  [{status}] {title} (state: {state})")
        lines.append(f"           ID: {pid}")
    return "\n".join(lines)


# -- Subcommand handlers -------------------------------------------------------


def cmd_validate(args):
    """Validate the API key."""
    output(api_request("GET", "/apikeys/me"))


def cmd_controls(args):
    """List all controls."""
    data = api_request_paginated("/controls")
    if args.format == "text" and not is_error(data):
        output_text(fmt_controls(data))
    else:
        output(data)


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
    data = api_request_paginated("/tests", params=params)
    if args.format == "text" and not is_error(data):
        output_text(fmt_tests(data))
    else:
        output(data)


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
    """Submit evidence to a test (link or file). Supports --stdin for JSON input."""
    if hasattr(args, "stdin") and args.stdin:
        data = json.load(sys.stdin)
        test_id = data.get("id")
        ev_type = data.get("type")
        if not test_id:
            error_exit("JSON input must include 'id' (test ID)")
        if not ev_type:
            error_exit("JSON input must include 'type' ('link' or 'file')")
        if ev_type == "link":
            body = {
                "type": "link",
                "url": data.get("url", ""),
                "description": data.get("description", ""),
                "evidenceDate": data.get("evidenceDate", ""),
            }
            output(api_request("POST", f"/tests/{test_id}/evidence", body=body))
        elif ev_type == "file":
            file_path = data.get("file", "")
            if not file_path or not os.path.isfile(file_path):
                error_exit(f"File not found: {file_path}")
            fields = {
                "type": "file",
                "description": data.get("description", ""),
                "evidenceDate": data.get("evidenceDate", ""),
            }
            output(multipart_upload(f"/tests/{test_id}/evidence", file_path, fields))
        else:
            error_exit("'type' must be 'link' or 'file'")
        return

    if not args.id:
        error_exit("--id is required (or use --stdin)")
    if not args.type:
        error_exit("--type is required (or use --stdin)")
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
    """Execute (pass/fail) a self-assessment test. Supports --stdin for JSON input."""
    if hasattr(args, "stdin") and args.stdin:
        data = json.load(sys.stdin)
        test_id = data.get("id")
        answer = data.get("answer")
        if not test_id:
            error_exit("JSON input must include 'id' (test ID)")
        if answer not in ("yes", "no"):
            error_exit("JSON input 'answer' must be 'yes' or 'no'")
        body = {"answer": answer}
        if data.get("comment"):
            body["comment"] = data["comment"]
        output(api_request("POST", f"/tests/{test_id}/execute", body=body))
        return

    if not args.id:
        error_exit("--id is required (or use --stdin)")
    if not args.answer:
        error_exit("--answer is required (or use --stdin)")
    if args.answer not in ("yes", "no"):
        error_exit("--answer must be 'yes' (pass) or 'no' (fail)")
    body = {"answer": args.answer}
    if args.comment:
        body["comment"] = args.comment
    output(api_request("POST", f"/tests/{args.id}/execute", body=body))


def cmd_vendors(args):
    """List all vendors."""
    output(api_request_paginated("/vendors"))


def cmd_vendor(args):
    """Get a single vendor by ID."""
    result = api_request("GET", f"/vendors/{args.id}")
    if not result.get("error") and args.include_systems:
        systems = api_request("GET", f"/vendors/{args.id}/systems")
        result["systems"] = systems
    output(result)


def cmd_systems(args):
    """List all systems."""
    output(api_request_paginated("/systems"))


def cmd_system(args):
    """Get a single system by ID."""
    output(api_request("GET", f"/systems/{args.id}"))


def cmd_system_tests(args):
    """Get tests associated with a system."""
    output(api_request("GET", f"/systems/{args.id}/tests"))


def cmd_policies(args):
    """List all policies.

    NOTE: The TrustCloud API v1 /policies endpoint currently returns empty
    results even when policies exist in the web UI. This appears to be an
    API limitation. Policies visible in the TrustCloud web interface may
    not be accessible through the API.
    """
    data = api_request_paginated("/policies")
    if args.format == "text" and not is_error(data):
        if isinstance(data, list) and len(data) == 0:
            output_text("=== Policies (0) ===\n\nNo policies returned by the API.\n"
                        "NOTE: The TrustCloud API v1 may not return policies that are\n"
                        "visible in the web UI. Check your TrustCloud web dashboard\n"
                        "for the authoritative policy list.")
        else:
            output_text(fmt_policies(data))
    else:
        output(data)


def cmd_policy(args):
    """Get a single policy by ID."""
    output(api_request("GET", f"/policies/{args.id}"))


def cmd_inventories(args):
    """List all inventories."""
    output(api_request_paginated("/inventories"))


def cmd_inventory(args):
    """Get a single inventory by ID."""
    output(api_request("GET", f"/inventories/{args.id}"))


# -- Composite commands --------------------------------------------------------


def cmd_dashboard(args):
    """Full compliance posture overview in a single call."""
    controls = api_request_paginated("/controls")
    tests_missing = api_request_paginated("/tests", params={"evidenceStatus": "missing"})
    tests_due = api_request_paginated("/tests", params={"evidenceStatus": "due"})
    tests_outdated = api_request_paginated("/tests", params={"evidenceStatus": "outdated"})
    policies = api_request_paginated("/policies")

    c_list = safe_list(controls)
    m_list = safe_list(tests_missing)
    d_list = safe_list(tests_due)
    o_list = safe_list(tests_outdated)
    p_list = safe_list(policies)

    data = {
        "controls": {
            "total": len(c_list),
            "by_state": count_by(c_list, "state"),
        },
        "evidence": {
            "missing": len(m_list),
            "due": len(d_list),
            "outdated": len(o_list),
        },
        "policies": {
            "total": len(p_list),
            "by_approval_status": count_by(p_list, "approvalStatus"),
        },
        "tests_needing_attention": m_list + d_list + o_list,
    }

    if args.format == "text":
        output_text(fmt_dashboard(data))
    else:
        output(data)


def cmd_gap_analysis(args):
    """Detailed evidence gap report across all tests."""
    missing = api_request_paginated("/tests", params={"evidenceStatus": "missing"})
    due = api_request_paginated("/tests", params={"evidenceStatus": "due"})
    outdated = api_request_paginated("/tests", params={"evidenceStatus": "outdated"})

    m_list = safe_list(missing)
    d_list = safe_list(due)
    o_list = safe_list(outdated)

    data = {
        "missing": m_list,
        "due": d_list,
        "outdated": o_list,
        "total_gaps": len(m_list) + len(d_list) + len(o_list),
    }

    if args.format == "text":
        output_text(fmt_gap_analysis(data))
    else:
        output(data)


def cmd_verify(args):
    """Verify evidence and execution status for given test IDs."""
    ids = []
    if args.ids:
        ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    elif args.stdin:
        data = json.load(sys.stdin)
        ids = data if isinstance(data, list) else data.get("ids", [])

    if not ids:
        error_exit("Provide test IDs via --ids (comma-separated) or --stdin (JSON array or {ids: [...]})")

    results = []
    for test_id in ids:
        test = api_request("GET", f"/tests/{test_id}")
        evidence = api_request("GET", f"/tests/{test_id}/evidence/history")
        history = api_request("GET", f"/tests/{test_id}/history")
        results.append({
            "test": test,
            "evidence_history": evidence,
            "execution_history": history,
        })

    data = {"verifications": results}
    if args.format == "text":
        output_text(fmt_verify(data))
    else:
        output(data)


def cmd_batch_submit(args):
    """Submit evidence to multiple tests from JSON file or stdin."""
    source = read_json_input(args)
    if source is None:
        error_exit("Provide submissions via --file (JSON file) or --stdin")

    submissions = source if isinstance(source, list) else source.get("submissions", [])
    results = []
    for sub in submissions:
        test_id = sub.get("id")
        ev_type = sub.get("type")
        if not test_id or not ev_type:
            results.append({"id": test_id, "result": {"error": True, "message": "Missing 'id' or 'type'"}})
            continue

        if ev_type == "link":
            body = {
                "type": "link",
                "url": sub.get("url", ""),
                "description": sub.get("description", ""),
                "evidenceDate": sub.get("evidenceDate", ""),
            }
            result = api_request("POST", f"/tests/{test_id}/evidence", body=body)
        elif ev_type == "file":
            file_path = sub.get("file", "")
            if not file_path or not os.path.isfile(file_path):
                results.append({"id": test_id, "result": {"error": True, "message": f"File not found: {file_path}"}})
                continue
            fields = {
                "type": "file",
                "description": sub.get("description", ""),
                "evidenceDate": sub.get("evidenceDate", ""),
            }
            result = multipart_upload(f"/tests/{test_id}/evidence", file_path, fields)
        else:
            results.append({"id": test_id, "result": {"error": True, "message": f"Invalid type: {ev_type}"}})
            continue

        results.append({"id": test_id, "result": result})

    data = {"results": results}
    if args.format == "text":
        output_text(fmt_batch_results(data))
    else:
        output(data)


def cmd_batch_execute(args):
    """Execute multiple self-assessment tests from JSON file or stdin."""
    source = read_json_input(args)
    if source is None:
        error_exit("Provide executions via --file (JSON file) or --stdin")

    executions = source if isinstance(source, list) else source.get("executions", [])
    results = []
    for ex in executions:
        test_id = ex.get("id")
        answer = ex.get("answer")
        if not test_id:
            results.append({"id": test_id, "result": {"error": True, "message": "Missing 'id'"}})
            continue
        if answer not in ("yes", "no"):
            results.append({"id": test_id, "result": {"error": True, "message": "Invalid 'answer'"}})
            continue
        body = {"answer": answer}
        if ex.get("comment"):
            body["comment"] = ex["comment"]
        result = api_request("POST", f"/tests/{test_id}/execute", body=body)
        results.append({"id": test_id, "result": result})

    data = {"results": results}
    if args.format == "text":
        output_text(fmt_batch_results(data))
    else:
        output(data)


# -- CLI setup -----------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trustcloud_api",
        description="TrustCloud API CLI client. Output is JSON by default.",
    )
    parser.add_argument(
        "--format", choices=["json", "text"], default="json",
        help="Output format: json (default) or text (human-readable)",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # -- Composite commands --

    # dashboard
    sub.add_parser("dashboard", help="Full compliance posture overview (single call)")

    # gap-analysis
    sub.add_parser("gap-analysis", help="Detailed evidence gap report")

    # verify
    p = sub.add_parser("verify", help="Verify evidence/execution status for tests")
    p.add_argument("--ids", help="Comma-separated test IDs to verify")
    p.add_argument("--stdin", action="store_true",
                   help="Read test IDs from stdin (JSON array or {ids: [...]})")

    # batch-submit
    p = sub.add_parser("batch-submit", help="Submit evidence to multiple tests")
    p.add_argument("--file", help="JSON file with submissions")
    p.add_argument("--stdin", action="store_true",
                   help="Read submissions from stdin")

    # batch-execute
    p = sub.add_parser("batch-execute", help="Execute multiple self-assessment tests")
    p.add_argument("--file", help="JSON file with executions")
    p.add_argument("--stdin", action="store_true",
                   help="Read executions from stdin")

    # -- Resource commands --

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
    p.add_argument("--id", help="Test ID (UUID) — required unless using --stdin")
    p.add_argument("--type", choices=["link", "file"],
                   help="Evidence type — required unless using --stdin")
    p.add_argument("--url", help="URL for link evidence")
    p.add_argument("--file", help="File path for file evidence")
    p.add_argument("--description", help="Evidence description")
    p.add_argument("--evidence-date", help="Evidence date (YYYY/MM/DD)")
    p.add_argument("--stdin", action="store_true",
                   help="Read evidence JSON from stdin")

    # execute-test
    p = sub.add_parser("execute-test", help="Execute (pass/fail) a self-assessment test")
    p.add_argument("--id", help="Test ID (UUID) — required unless using --stdin")
    p.add_argument("--answer", choices=["yes", "no"],
                   help="Test result — required unless using --stdin")
    p.add_argument("--comment", help="Optional assessment comment")
    p.add_argument("--stdin", action="store_true",
                   help="Read execution JSON from stdin")

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
        # Composite commands
        "dashboard": cmd_dashboard,
        "gap-analysis": cmd_gap_analysis,
        "verify": cmd_verify,
        "batch-submit": cmd_batch_submit,
        "batch-execute": cmd_batch_execute,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
