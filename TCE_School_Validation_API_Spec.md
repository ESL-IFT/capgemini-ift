Hi,

Thank you for the confirmation. Please find the API specification details below.

---

**Use Case:**
When a school registers on the IFT portal, we will call the TCE Validation API with the school's details to verify whether it is a Tata ClassEdge partner school. Based on the response, the payment flow for students of that school will be determined accordingly.

**Endpoint (Suggested):**
`POST /api/v1/school/validate`

**Authentication:**
Bearer token via `Authorization` header. Kindly provision an API key for IFT (staging + production).

---

**Request Payload:**

```json
{
  "school_name": "Delhi Public School, Vasant Kunj",
  "address": "Sector B-6, Vasant Kunj, New Delhi, Delhi 110070",
  "city": "New Delhi",
  "state": "Delhi",
  "pin_code": "110070",
  "contact_email": "coordinator@dpsvasantkunj.com",
  "contact_phone": "9876543210"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `school_name` | string | Yes | Full school name (sourced via Google Places Autocomplete) |
| `address` | string | Yes | Full school address |
| `city` | string | Yes | City of the school |
| `state` | string | Yes | State of the school |
| `pin_code` | string | Yes | PIN code of the school |
| `contact_email` | string | Yes | School coordinator's email |
| `contact_phone` | string | Yes | School coordinator's phone number |

---

**Expected Response:**

```json
// School found (TCE partner)
{
  "is_tce_school": true,
  "tce_school_id": "TCE-DL-04521",
  "message": "School is a verified Tata ClassEdge partner."
}
```

```json
// School not found
{
  "is_tce_school": false,
  "tce_school_id": null,
  "message": "School not found in Tata ClassEdge records."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `is_tce_school` | boolean | `true` if school exists in TCE database, `false` otherwise |
| `tce_school_id` | string / null | TCE's internal school ID (null if not found) |
| `message` | string | Human-readable status message |

---

**Error Handling:**

| HTTP Code | Scenario |
|-----------|----------|
| 400 | Missing required fields |
| 401 | Invalid API key |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

In case of API downtime or timeout (>5 seconds), we will allow registration to proceed and mark the school as "pending verification" for manual or retry-based validation later.

---

**Next Steps:**
1. Please review and confirm the payload/response format.
2. Share the base URL and API key (staging + production).
3. We will integrate and coordinate joint testing.

Looking forward to your confirmation.


