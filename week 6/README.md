# Job Search Assistant

An MCP server that exposes job search and salary tools backed by the JSearch API on RapidAPI. It communicates over stdio using JSON-RPC 2.0 following the standard MCP handshake (`initialize`, `notifications/initialized`, `tools/list`, `tools/call`).

The project is split into two parts:

- `fastapi_server.py`: a FastAPI backend that talks to the JSearch API directly and exposes clean HTTP endpoints.
- `job_search.py`: the MCP server that Claude talks to. It calls the FastAPI backend.

```
Claude -> job_search.py (MCP) -> fastapi_server.py (FastAPI) -> JSearch API
```

## What it does

The MCP server registers four tools:

- `search_jobs`: searches for job listings by query and optional location.
- `get_job_details`: looks up full details for a single job listing by its job ID.
- `get_salary_estimate`: returns estimated salary ranges for a job title in a location.
- `get_company_salary`: returns estimated salary ranges for a job title at a specific company.

Each tool maps to a corresponding endpoint on the FastAPI backend:

| MCP tool              | FastAPI endpoint         |
|-----------------------|--------------------------|
| search_jobs            | GET /jobs/search         |
| get_job_details         | GET /jobs/{job_id}       |
| get_salary_estimate      | GET /salary/estimate     |
| get_company_salary       | GET /salary/company      |

## Requirements

- Python 3.8+
- `httpx`
- `fastapi`
- `uvicorn`
- `python-dotenv`
- A RapidAPI key with access to the JSearch API

Install everything with:

```
pip install -r requirements.txt
```

## Configuration

The FastAPI backend reads your RapidAPI key from the `RAPIDAPI_KEY` environment variable. Create a `.env` file next to `fastapi_server.py`:

```
RAPIDAPI_KEY=your-rapidapi-key-here
```

The MCP server reads the backend's URL from `BACKEND_URL`, defaulting to `http://localhost:8000` if not set.

## Running the server

Two processes need to run.

**1. Start the FastAPI backend first:**

```
uvicorn fastapi_server:app --port 8000
```


**2. The MCP server (`job_search.py`) is launched by the MCP client itself** (Claude Desktop or another MCP host) rather than run interactively. It reads JSON-RPC requests from stdin and writes responses to stdout, one JSON object per line and forwards tool calls to the FastAPI backend over HTTP.

### Client configuration

Example client config, `mcp_config_example.json`:

```json
{
  "mcpServers": {
    "job-search-assistant": {
      "command": "python",
      "args": ["/absolute/path/to/job_search.py"],
      "env": {
        "BACKEND_URL": "http://localhost:8000"
      }
    }
  }
}
```

The `RAPIDAPI_KEY` does not go in this config since `job_search.py` never touches JSearch directly; it only lives in the FastAPI backend's `.env` file.

## Tool reference

### search_jobs

Searches for job listings based on a query and an optional location.

**Input**

| Parameter | Type   | Required | Description                                          |
|-----------|--------|----------|--------------------------------------------------------|
| query     | string | yes      | Job title or keywords, e.g. "software engineer"       |
| location  | string | no       | Location filter, e.g. "Pakistan", "Lahore", "Remote"   |

**Output**

A text block listing up to 10 matching jobs each with job title, job ID, employer name, city or country, application link and posting date. The job ID returned here is what you pass into `get_job_details`.

If no jobs are found, the tool returns a message saying so instead of an empty list.

### get_job_details

Looks up full details for a single job listing.

**Input**

| Parameter | Type   | Required | Description                                               |
|-----------|--------|----------|---------------------------------------------------------------|
| job_id    | string | yes      | The job_id value returned by search_jobs for the listing you want details on |

**Output**

A text block with job title, employer name, location, employment type, posting date, application link and the first 2000 characters of the job description.

If no details are found for the given ID, the tool returns a message saying so.

### get_salary_estimate

Returns estimated salary ranges for a job title in a given location.

**Input**

| Parameter | Type   | Required | Description                                                  |
|-----------|--------|----------|--------------------------------------------------------------|
| job_title | string | yes      | Job title to estimate salary for, e.g. "software engineer"   |
| location  | string | yes      | Location for the estimate, e.g. "Lahore, Pakistan"            |

**Output**

A text block listing up to 5 matching salary estimates, each with job title, minimum/maximum salary with currency and pay period, median salary and data source (publisher).

If no salary data is found, the tool returns a message saying so.

### get_company_salary

Returns estimated salary ranges for a job title at a specific company.

**Input**

| Parameter | Type   | Required | Description                                                  |
|-----------|--------|----------|------------------------------------------------------------------|
| company   | string | yes      | Company name, e.g. "Systems Limited"                          |
| job_title | string | yes      | Job title to estimate salary for, e.g. "software engineer"    |
| location  | string | no       | Optional location filter, e.g. "Lahore, Pakistan"              |

**Output**

A text block listing up to 5 matching salary estimates for that company and role, each with job title, minimum/maximum salary with currency and pay period and median salary.

If no data is found, the tool returns a message saying so.

## Error handling

- If the JSearch API returns a non-200 status code, the FastAPI backend raises an HTTP error including the status code and response body.
- If the FastAPI backend returns a non-200 status code, the MCP server raises an exception with the status code and response body and returns it to the client as a JSON-RPC error.
- Malformed JSON-RPC requests are silently skipped rather than crashing the server.
- Unexpected exceptions during request handling are caught and returned as JSON-RPC errors where possible.
- Calling an unregistered tool returns a "Tool not found" error.
- Calling an unrecognized method returns a "Method not found" error.
