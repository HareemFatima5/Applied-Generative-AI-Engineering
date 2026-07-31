# Job Search Assistant

An MCP (Model Context Protocol) server that exposes job search and salary tools backed by the JSearch API on RapidAPI. It communicates over stdio using JSON-RPC 2.0, following the standard MCP handshake (`initialize`, `notifications/initialized`, `tools/list`, `tools/call`).

## What it does

The server registers four tools:

- `search_jobs` — searches for job listings by query and optional location.
- `get_job_details` — looks up full details for a single job listing by its job ID.
- `get_salary_estimate` — returns estimated salary ranges for a job title in a location.
- `get_company_salary` — returns estimated salary ranges for a job title at a specific company.

## Requirements

- Python 3.8+
- `httpx`
- A RapidAPI key with access to the JSearch API

Install the dependency with:

```
pip install httpx
```

## Configuration

The server reads your RapidAPI key from the `RAPIDAPI_KEY` environment variable:

```
export RAPIDAPI_KEY="your-rapidapi-key-here"
```

The server will run without this set, but every API call will fail authentication until a valid key is provided. There is no hardcoded fallback key — always set it via the environment.

## Running the server

```
python job_search_server.py
```

The server reads JSON-RPC requests from stdin and writes responses to stdout, one JSON object per line. It's meant to be launched by an MCP-compatible client (such as Claude Desktop or another MCP host) rather than run interactively on its own.

### Client configuration

An example client config is included as `mcp_config_example.json`:

```json
{
  "mcpServers": {
    "job-search-assistant": {
      "command": "python",
      "args": ["/absolute/path/to/job_search_server.py"],
      "env": {
        "RAPIDAPI_KEY": "your-rapidapi-key-here"
      }
    }
  }
}
```

Update the `args` path to point at wherever you place `job_search_server.py` on disk, and drop in your real RapidAPI key. Most MCP hosts (Claude Desktop included) read this file to know which servers to launch and how.

## Tool reference

### search_jobs

Searches for job listings based on a query and an optional location.

**Input**

| Parameter | Type   | Required | Description                                          |
|-----------|--------|----------|--------------------------------------------------------|
| query     | string | yes      | Job title or keywords, e.g. "software engineer"       |
| location  | string | no       | Location filter, e.g. "Pakistan", "Lahore", "Remote"   |

**Output**

A text block listing up to 10 matching jobs, each with job title, job ID, employer name, city or country, application link, and posting date. The job ID returned here is what you pass into `get_job_details`.

If no jobs are found, the tool returns a message saying so instead of an empty list.

### get_job_details

Looks up full details for a single job listing.

**Input**

| Parameter | Type   | Required | Description                                               |
|-----------|--------|----------|---------------------------------------------------------------|
| job_id    | string | yes      | The job_id value returned by search_jobs for the listing you want details on |

**Output**

A text block with job title, employer name, location, employment type, posting date, application link, and the first 2000 characters of the job description.

If no details are found for the given ID, the tool returns a message saying so.

### get_salary_estimate

Returns estimated salary ranges for a job title in a given location.

**Input**

| Parameter | Type   | Required | Description                                                  |
|-----------|--------|----------|--------------------------------------------------------------|
| job_title | string | yes      | Job title to estimate salary for, e.g. "software engineer"   |
| location  | string | yes      | Location for the estimate, e.g. "Lahore, Pakistan"            |

**Output**

A text block listing up to 5 matching salary estimates, each with job title, minimum/maximum salary with currency and pay period, median salary, and data source (publisher).

If no salary data is found, the tool returns a message saying so.

### get_company_salary

Returns estimated salary ranges for a job title at a specific company.

**Input**

| Parameter | Type   | Required | Description                                                  |
|-----------|--------|----------|----------------------------------------------------------------|
| company   | string | yes      | Company name, e.g. "Systems Limited"                          |
| job_title | string | yes      | Job title to estimate salary for, e.g. "software engineer"    |
| location  | string | no       | Optional location filter, e.g. "Lahore, Pakistan"              |

**Output**

A text block listing up to 5 matching salary estimates for that company and role, each with job title, minimum/maximum salary with currency and pay period, and median salary.

If no data is found, the tool returns a message saying so.

## Error handling

- If the JSearch API returns a non-200 status code, the server raises an exception that includes the status code and the response body, and returns it to the client as a JSON-RPC error.
- Malformed JSON-RPC requests are silently skipped rather than crashing the server.
- Unexpected exceptions during request handling are caught and returned as JSON-RPC errors where possible.
- Calling an unregistered tool returns a "Tool not found" error.
- Calling an unrecognized method returns a "Method not found" error.

## Known limitations

- `search_jobs` only requests a single page of results (`num_pages: 1`), so results are capped by whatever JSearch returns on the first page, and results shown are truncated to the first 10.
- `get_salary_estimate` and `get_company_salary` results are truncated to the first 5 entries.
- `get_job_details` truncates the job description to 2000 characters.
- There is no retry or rate-limit handling for RapidAPI requests.
- The JSearch endpoint paths and parameter names used here (`/job-details`, `/estimated-salary`, `/company-job-salary`) match the current public JSearch documentation as of this writing — worth double-checking against the live API docs on RapidAPI if you hit unexpected errors, since third-party APIs do change their contracts over time.

## License

Add your preferred license here.
