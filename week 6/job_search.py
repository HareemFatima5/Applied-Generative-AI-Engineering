import sys
import json
import httpx
import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def call_backend(path, params):
    """call fastapi backend with given path and params"""
    url = f"{BACKEND_URL}{path}"
    clean_params = {k: v for k, v in params.items() if v not in (None, "")}
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, params=clean_params)
        if resp.status_code != 200:
            raise Exception(
                f"Status {resp.status_code} from backend. "
                f"Response body: {resp.text[:1000]}"
            )
        return resp.json()


TOOLS = [
    {
        "name": "search_jobs",
        "description": "Search for job listings based on query and location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Job title or keywords to search for (e.g., 'software engineer', 'data scientist')"
                },
                "location": {
                    "type": "string",
                    "description": "Location filter (e.g., 'Pakistan', 'Lahore', 'Remote')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_job_details",
        "description": "Get full details for a single job listing given its job ID (returned by search_jobs)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The job_id value returned by search_jobs for the listing you want details on"
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "get_salary_estimate",
        "description": "Get estimated salary range for a job title in a given location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_title": {
                    "type": "string",
                    "description": "Job title to estimate salary for (e.g., 'software engineer')"
                },
                "location": {
                    "type": "string",
                    "description": "Location for the estimate (e.g., 'Lahore, Pakistan')"
                }
            },
            "required": ["job_title", "location"]
        }
    },
    {
        "name": "get_company_salary",
        "description": "Get estimated salary range for a job title at a specific company",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company": {
                    "type": "string",
                    "description": "Company name (e.g., 'Systems Limited')"
                },
                "job_title": {
                    "type": "string",
                    "description": "Job title to estimate salary for (e.g., 'software engineer')"
                },
                "location": {
                    "type": "string",
                    "description": "Optional location filter (e.g., 'Lahore, Pakistan')"
                }
            },
            "required": ["company", "job_title"]
        }
    }
]


def handle_search_jobs(args):
    """handle job search and format results"""
    query = args.get("query", "")
    location = args.get("location", "")
    data = call_backend("/jobs/search", {"query": query, "location": location})
    jobs = data.get("data", [])

    if jobs:
        text = f"Found {len(jobs)} jobs matching '{query}':\n\n"
        for i, job in enumerate(jobs[:10], 1):
            text += f"{i}. **{job.get('job_title', 'N/A')}**\n"
            text += f"   Job ID: {job.get('job_id', 'N/A')}\n"
            text += f"   Company: {job.get('employer_name', 'N/A')}\n"
            text += f"   Location: {job.get('job_city', 'N/A') or job.get('job_country', 'N/A')}\n"
            text += f"   Apply: {job.get('job_apply_link', 'N/A')}\n"
            text += f"   Posted: {job.get('job_posted_at_datetime_utc', 'N/A')}\n\n"
    else:
        text = f"No jobs found for '{query}' in '{location}'"
    return text


def handle_get_job_details(args):
    """get detailed info for a specific job"""
    job_id = args.get("job_id", "")
    data = call_backend(f"/jobs/{job_id}", {})
    jobs = data.get("data", [])

    if jobs:
        job = jobs[0]
        text = f"**{job.get('job_title', 'N/A')}**\n\n"
        text += f"Company: {job.get('employer_name', 'N/A')}\n"
        text += f"Location: {job.get('job_city', 'N/A') or job.get('job_country', 'N/A')}\n"
        text += f"Employment type: {job.get('job_employment_type', 'N/A')}\n"
        text += f"Posted: {job.get('job_posted_at_datetime_utc', 'N/A')}\n"
        text += f"Apply: {job.get('job_apply_link', 'N/A')}\n\n"
        description = job.get("job_description", "")
        if description:
            text += f"Description:\n{description[:2000]}\n"
    else:
        text = f"No details found for job ID '{job_id}'"
    return text


def handle_get_salary_estimate(args):
    """get salary estimates for a job title in a location"""
    job_title = args.get("job_title", "")
    location = args.get("location", "")
    data = call_backend(
        "/salary/estimate",
        {"job_title": job_title, "location": location}
    )
    estimates = data.get("data", [])

    if estimates:
        text = f"Salary estimates for '{job_title}' in '{location}':\n\n"
        for i, est in enumerate(estimates[:5], 1):
            text += f"{i}. {est.get('job_title', 'N/A')}\n"
            text += (
                f"   Range: {est.get('min_salary', 'N/A')} - "
                f"{est.get('max_salary', 'N/A')} "
                f"{est.get('salary_currency', '')} "
                f"({est.get('salary_period', 'N/A')})\n"
            )
            text += f"   Median: {est.get('median_salary', 'N/A')}\n"
            text += f"   Source: {est.get('publisher_name', 'N/A')}\n\n"
    else:
        text = f"No salary data found for '{job_title}' in '{location}'"
    return text


def handle_get_company_salary(args):
    """get salary estimates for a job at a specific company"""
    company = args.get("company", "")
    job_title = args.get("job_title", "")
    location = args.get("location", "")
    data = call_backend(
        "/salary/company",
        {"company": company, "job_title": job_title, "location": location}
    )
    estimates = data.get("data", [])

    if estimates:
        text = f"Salary estimates for '{job_title}' at '{company}':\n\n"
        for i, est in enumerate(estimates[:5], 1):
            text += f"{i}. {est.get('job_title', job_title)}\n"
            text += (
                f"   Range: {est.get('min_salary', 'N/A')} - "
                f"{est.get('max_salary', 'N/A')} "
                f"{est.get('salary_currency', '')} "
                f"({est.get('salary_period', 'N/A')})\n"
            )
            text += f"   Median: {est.get('median_salary', 'N/A')}\n\n"
    else:
        text = f"No company salary data found for '{job_title}' at '{company}'"
    return text


TOOL_HANDLERS = {
    "search_jobs": handle_search_jobs,
    "get_job_details": handle_get_job_details,
    "get_salary_estimate": handle_get_salary_estimate,
    "get_company_salary": handle_get_company_salary,
}


def main():
    """main loop handling json-rpc requests"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            if not line.strip():
                continue

            request = json.loads(line)
            method = request.get("method")
            request_id = request.get("id")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "Job Search Assistant",
                            "version": "1.2.0"
                        }
                    }
                }

            elif method == "notifications/initialized":
                continue

            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": TOOLS}
                }

            elif method == "tools/call":
                call_params = request.get("params", {})
                tool_name = call_params.get("name")
                args = call_params.get("arguments", {})

                handler = TOOL_HANDLERS.get(tool_name)
                if handler is None:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
                    }
                else:
                    try:
                        result_text = handler(args)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [{"type": "text", "text": result_text}]
                            }
                        }
                    except Exception as e:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32000, "message": f"API Error: {str(e)}"}
                        }

            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": request_id, "result": {}}

            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            try:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id if 'request_id' in locals() else None,
                    "error": {"code": -32000, "message": str(e)}
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception:
                pass


if __name__ == "__main__":
    main()
