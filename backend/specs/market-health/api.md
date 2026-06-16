---
id: market-health
experience: market-health
directive: low
status: draft
created: 2026-06-13
---

# Market Health — Backend Architecture Spec

## Experience this implements
See: `design/market-health/experience.md`

---

## Data Models

No database in v1. All market data is mocked in-memory in Python. These models describe
the shape of the data the API returns — implement them as Python dataclasses or TypedDicts.
When a real data source is added, these become the DB schema.

### MarketHealthSignal
| Field | Type | Description |
|---|---|---|
| `verdict` | `"Healthy" \| "Cautious" \| "Contracting"` | The aggregate market verdict |
| `explanation` | `str` | One-sentence plain-language explanation of the verdict |
| `trend_direction` | `"improving" \| "stable" \| "worsening"` | Direction of change over the selected period |
| `as_of` | `date` | The date the signal was last computed |
| `source` | `str` | Description of the data source (for Data Freshness label) |

### SearchImplication
| Field | Type | Description |
|---|---|---|
| `text` | `str` | Plain-language statement of what the current signal means for the user's job search |
| `signal_verdict` | `str` | The verdict this implication corresponds to |

### DemandSignal
| Field | Type | Description |
|---|---|---|
| `role_family` | `str` | e.g. "UX Design", "Product Management" |
| `seniority` | `str` | e.g. "Senior", "Lead", "Mid" |
| `location` | `str` | Market / city |
| `posting_trend` | `list[{ period: str, count: int }]` | Time-series of job posting counts |
| `trend_direction` | `"rising" \| "stable" \| "declining"` | Summary direction |
| `as_of` | `date` | |
| `source` | `str` | |

### CompensationSignal
| Field | Type | Description |
|---|---|---|
| `role_family` | `str` | |
| `seniority` | `str` | |
| `location` | `str` | |
| `salary_min` | `int` | Annual, local currency |
| `salary_max` | `int` | |
| `salary_median` | `int` | |
| `trend_direction` | `"rising" \| "stable" \| "declining"` | |
| `as_of` | `date` | |
| `source` | `str` | |

### LayoffSignal
| Field | Type | Description |
|---|---|---|
| `company` | `str` | |
| `sector` | `str` | |
| `event_date` | `date` | |
| `headcount_affected` | `int \| None` | Null if unconfirmed |
| `source` | `str` | |

---

## API Endpoints

### GET /api/market-health/summary

**Purpose**: Returns the current Market Health Signal and Search Implication, filtered by role and location if provided.

**Auth required**: no (v1)

**Query params**:
| Param | Type | Default |
|---|---|---|
| `role` | `str` | `"all"` |
| `seniority` | `str` | `"all"` |
| `location` | `str` | `"all"` |

**Response**:
```json
{
  "signal": {
    "verdict": "Cautious",
    "explanation": "Demand is stable but layoff activity has increased in large tech companies.",
    "trendDirection": "worsening",
    "asOf": "2026-06-01",
    "source": "Aggregated from job board postings and public layoff announcements"
  },
  "implication": {
    "text": "The market is soft but not closed. Targeting smaller companies and contract roles will increase your hit rate."
  }
}
```

**Errors**:
| Code | Reason |
|---|---|
| 400 | Invalid filter values |
| 503 | Data source unavailable (not applicable in v1 — mocked data always available) |

---

### GET /api/market-health/trends

**Purpose**: Returns time-series Demand, Compensation, and Layoff Signals for the trend grid.

**Auth required**: no (v1)

**Query params**:
| Param | Type | Default |
|---|---|---|
| `role` | `str` | `"all"` |
| `seniority` | `str` | `"all"` |
| `location` | `str` | `"all"` |
| `period` | `"3m" \| "6m" \| "12m"` | `"6m"` |

**Response**:
```json
{
  "demand": [
    {
      "role_family": "UX Design",
      "seniority": "Senior",
      "location": "London",
      "trend_direction": "declining",
      "posting_trend": [
        { "period": "2026-01", "count": 340 },
        { "period": "2026-02", "count": 310 }
      ],
      "as_of": "2026-06-01",
      "source": "LinkedIn job postings"
    }
  ],
  "compensation": [
    {
      "role_family": "UX Design",
      "seniority": "Senior",
      "location": "London",
      "salary_min": 70000,
      "salary_max": 110000,
      "salary_median": 88000,
      "trend_direction": "stable",
      "as_of": "2026-06-01",
      "source": "Glassdoor salary reports"
    }
  ],
  "layoffs": [
    {
      "company": "Acme Corp",
      "sector": "FinTech",
      "event_date": "2026-05-15",
      "headcount_affected": 200,
      "source": "Layoffs.fyi"
    }
  ]
}
```

**Errors**:
| Code | Reason |
|---|---|
| 400 | Invalid `period` value |

---

### GET /api/alerts/exceptions

**Purpose**: Returns unresolved Exceptions for the current user. Used to show the returning-user banner.

**Auth required**: no (v1 — returns empty array)

**Response**:
```json
{
  "exceptions": []
}
```

---

### POST /api/chat

**Purpose**: Accepts the user's conversation history and streams a Claude response, with current market data injected as context.

**Auth required**: no (v1)

**Request**:
```json
{
  "messages": [
    { "role": "user", "content": "Is now a good time to look for a senior UX role in London?" }
  ],
  "context": {
    "role": "UX Design",
    "seniority": "Senior",
    "location": "London"
  }
}
```

**Response**: Server-Sent Events stream (text/event-stream). Each event is a token chunk in Vercel AI SDK wire format.

**Errors**:
| Code | Reason |
|---|---|
| 400 | Malformed messages array |
| 502 | Anthropic API unreachable |

---

## Business Logic

**Market Health Signal verdict (v1 mock rule)**
The verdict is pre-set in the mock data. When a real data source is connected, the rule is:
- `Healthy`: demand trend is rising AND layoff activity is low
- `Cautious`: demand is stable OR layoff activity is moderate
- `Contracting`: demand is declining OR layoff activity is high

**Search Implication generation**
In v1, implications are static strings keyed to verdict + filter combination, stored in the mock data layer. When real data is connected, implications may be generated by Claude with the signal as input.

**Conversational context injection**
Before calling the Anthropic API, the server fetches the current summary and trends for the context filters and prepends them as a system message. Claude is instructed to answer from this data and flag when a question cannot be answered from it.

**Insufficient data handling**
If filters produce an empty dataset, the summary endpoint returns `verdict: null` and an explanation stating that no data is available for that combination. The frontend must handle a null verdict without crashing.

---

## External Dependencies

| Dependency | Purpose |
|---|---|
| Anthropic Python SDK | Streaming Claude responses for `/api/chat` |

No database in v1. No queues, storage, or other external services.

---

## Tech Decisions

- **FastAPI** with `StreamingResponse` for the `/api/chat` endpoint. Use `text/event-stream` content type to match Vercel AI SDK expectations on the frontend.
- All mock data lives in a single `backend/src/mock_data.py` module. When a real data source is added, replace that module — endpoints do not change.
- Use Python dataclasses (not Pydantic for v1 simplicity, but Pydantic is fine if preferred). FastAPI will serialize them automatically.
- No auth middleware in v1. Add it as a separate layer when needed.
