# TrustCloud API Reference (v1)

## Base URL

```
https://api.trustcloud.ai
```

## Authentication

All requests require two headers:

```
Authorization: Bearer <your_api_key>
x-trustcloud-api-version: 1
```

**Obtaining an API key:**

1. Navigate to the "Integrations" page in your TrustCloud program.
2. Select "API Access" from the left-side panel (requires **Compliance Admin** role).
3. Click "Begin Setup".
4. Enter an API Key Name and set an expiration period.
5. Click "Generate Key" and copy the key.
6. Set a contact email for expiration notifications.
7. Click "Finish".

Multiple API keys can be managed. Keys have expiration dates.

## Endpoints

### API Keys

#### Validate API Key

```
GET /apikeys/me
```

Returns details about the current API key.

**Response:**
```json
{
  "keyName": "My API Key",
  "expiresAt": "2026-12-31T23:59:59Z"
}
```

---

### Controls

Controls are the foundational building blocks of a compliance program — processes followed to prevent risks.

#### List Controls

```
GET /controls
```

Returns all controls in the program.

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Control ID |
| `catalogControlId` | string | Catalog control identifier |
| `category` | string | Control category |
| `controlName` | string | Control name |
| `controlText` | string | Full control description |
| `state` | string | State (e.g., "adopted") |
| `maturityLevel` | string | Maturity level |
| `groupName` | string | Group name |
| `lastStateChangeBy` | string | Who last changed state |
| `lastStateChangeOn` | string | When state was last changed |
| `evidenceDetails` | object | Evidence status and next due date |
| `compliance` | array | Framework mappings (e.g., SOC 2 CC8.1) |
| `intervalDuration` | string | Evidence interval |
| `owner` | object | Owner (id, name) |
| `_metadata` | object | Metadata |

#### Get Control

```
GET /controls/{id}
```

Returns a single control by ID.

#### Get Control Tests

```
GET /controls/{id}/tests
```

Returns all tests associated with a control.

---

### Tests

Tests are the means of validating a control. Can be automated (via integrations) or manual ("self_assessment"). Self-assessment tests can be completed via the API.

#### List Tests

```
GET /tests
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Filter by test name (partial match) |
| `evidenceStatus` | string | One of: `missing`, `due`, `outdated`, `up_to_date`, `not_required` |
| `testStatus` | string | One of: `available`, `in_progress`, `excluded` |
| `evidenceDueByDate` | string | Tests with evidence due before date (YYYY-MM-DD) |
| `evidenceDueByDays` | integer | Tests with evidence due within N days |

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Test ID |
| `testId` | string | Test identifier |
| `type` | string | Test type (e.g., "self_assessment") |
| `name` | string | Test name |
| `level` | string | Test level |
| `question` | string | Assessment question |
| `recommendation` | string | Recommendation |
| `evidenceCount` | integer | Number of evidence items |
| `evidenceDescription` | string | Evidence description |
| `evidenceStatus` | string | Evidence status |
| `executionOutcome` | string | Last execution outcome |
| `executionStatus` | string | Execution status |
| `nextEvidenceDueDate` | string | Next evidence due date |
| `owner` | object | Owner (id, name) |
| `control` | object | Associated control (id, controlId, name, category) |
| `system` | object | Associated system |
| `metadata` | object | Metadata |

#### Get Test

```
GET /tests/{id}
```

Returns a single test by ID.

#### Get Test History

```
GET /tests/{id}/history
```

Returns the execution history of a test.

#### Get Evidence History

```
GET /tests/{id}/evidence/history
```

Returns the evidence submission history of a test.

#### Submit Evidence

```
POST /tests/{id}/evidence
```

Submit evidence to a test. Two types are supported:

**Link evidence (JSON body):**
```json
{
  "type": "link",
  "url": "https://example.com/evidence",
  "description": "Description of the evidence",
  "evidenceDate": "2026/03/12"
}
```

**File evidence (multipart/form-data):**

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Must be "file" |
| `description` | string | Evidence description |
| `evidenceDate` | string | Evidence date (YYYY/MM/DD) |
| `file` | file | The file to upload |

#### Execute Test

```
POST /tests/{id}/execute
```

Complete a self-assessment test with a pass/fail result.

**Request body:**
```json
{
  "answer": "yes",
  "comment": "Optional assessment details"
}
```

The `answer` field accepts `yes` (pass) or `no` (fail).

---

### Vendors

Vendors are companies from whom software or services are purchased.

#### List Vendors

```
GET /vendors
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Vendor ID |
| `name` | string | Vendor name |
| `catalogVendorId` | string | Catalog vendor ID |
| `purpose` | string | Vendor purpose |
| `vendorLocations` | array | Vendor locations |
| `classification` | string | Classification |
| `logoUrl` | string | Vendor logo URL |
| `tags` | array | Tags |
| `isSubprocessor` | boolean | Whether vendor is a subprocessor |
| `vendorPrivacyPolicyUrl` | string | Privacy policy URL |
| `vendorSecurityPageUrl` | string | Security page URL |
| `vendorTosUrl` | string | Terms of service URL |
| `groupId` | string | Group ID |
| `groupName` | string | Group name |
| `owner` | object | Owner (id, name) |
| `_metadata` | object | Metadata |

#### Get Vendor

```
GET /vendors/{id}
```

Returns a single vendor by ID.

#### Get Vendor Systems

```
GET /vendors/{id}/systems
```

Returns all systems associated with a vendor.

---

### Systems

Systems are software used by the organization — either built in-house or purchased from vendors.

#### List Systems

```
GET /systems
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | System ID |
| `name` | string | System name |
| `systemId` | string | System identifier |
| `purpose` | string | System purpose |
| `riskScore` | number | Risk score |
| `_metadata` | object | Metadata |
| `owner` | object | Owner |
| `group` | object | Group (id, name) |
| `provider` | object | Provider (id, name) |

#### Get System

```
GET /systems/{id}
```

Returns a single system by ID.

#### Get System Tests

```
GET /systems/{id}/tests
```

Returns all tests associated with a system.

---

### Policies

Policies are documents describing organizational intentions, expectations, and approaches for maintaining processes.

#### List Policies

```
GET /policies
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Policy ID |
| `catalogPolicyId` | string | Catalog policy ID |
| `title` | string | Policy title |
| `policyId` | string | Policy identifier |
| `approvalStatus` | string | Approval status (e.g., "approved") |
| `policyVersionId` | string | Version ID |
| `policyLastApprovedDate` | string | Last approved date |
| `version` | string | Version number |
| `highlights` | string | Policy highlights |
| `description` | string | Policy description |
| `securityGroup` | string | Security group |
| `policyState` | string | Policy state (e.g., "Unconfigured") |
| `policyPdfUrl` | string | URL to policy PDF |
| `programGroupId` | string | Program group ID |
| `owner` | object | Owner |
| `_metaData` | object | Metadata |

#### Get Policy

```
GET /policies/{id}
```

Returns a single policy by ID.

---

### Inventories

Inventories are specific lists of data gathered about parts of the business (users, systems, security incidents, devices, servers, databases, logs, etc.).

#### List Inventories

```
GET /inventories
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Inventory ID |
| `inventoryId` | string | Inventory identifier |
| `name` | string | Inventory name |
| `properties` | object | Dynamic schema of property definitions |
| `_metaData` | object | Metadata |
| `resources` | array | Inventory entries with `id`, `systemId`, `propertyValues` |

#### Get Inventory

```
GET /inventories/{id}
```

Returns a single inventory by ID.

---

## Common Patterns

### Object IDs

All object IDs use UUID v4 format (e.g., `550e8400-e29b-41d4-a716-446655440000`).

### Timestamps

Timestamps use ISO-like format with timezone: `"2023-02-20 16:16:07.316+00"`.

### Error Responses

The API returns standard HTTP error codes. Common ones:

| Code | Meaning |
|------|---------|
| 401 | Invalid or expired API key |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 429 | Rate limit exceeded |

### Evidence Status Values

| Status | Meaning |
|--------|---------|
| `missing` | No evidence has been submitted |
| `due` | Evidence is due soon |
| `outdated` | Evidence has expired |
| `up_to_date` | Evidence is current |
| `not_required` | Evidence is not required |

### Test Status Values

| Status | Meaning |
|--------|---------|
| `available` | Test is available to execute |
| `in_progress` | Test is currently in progress |
| `excluded` | Test has been excluded |
