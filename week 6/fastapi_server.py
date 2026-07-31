import os

import httpx
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
JSEARCH_HOST = "jsearch.p.rapidapi.com"

app = FastAPI(title="JSearch Backend")


async def call_jsearch(path, params):
    """call jsearch api with given path and params"""
    url = f"https://{JSEARCH_HOST}{path}"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": JSEARCH_HOST
    }
    # remove empty params to avoid sending blank query args
    clean_params = {k: v for k, v in params.items() if v not in (None, "")}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=clean_params, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"JSearch API response: {resp.text[:1000]}"
            )
        return resp.json()


@app.get("/jobs/search")
async def search_jobs(query: str, location: str = "", num_pages: str = "1"):
    """search jobs by query and location"""
    return await call_jsearch(
        "/search",
        {"query": f"{query} {location}".strip(), "num_pages": num_pages}
    )


@app.get("/jobs/{job_id}")
async def get_job_details(job_id: str):
    """get detailed job info by job id"""
    return await call_jsearch("/job-details", {"job_id": job_id})


@app.get("/salary/estimate")
async def get_salary_estimate(job_title: str, location: str):
    """get salary estimates for job title in location"""
    return await call_jsearch(
        "/estimated-salary",
        {"job_title": job_title, "location": location}
    )


@app.get("/salary/company")
async def get_company_salary(company: str, job_title: str, location: str = ""):
    """get salary estimates for job at specific company"""
    return await call_jsearch(
        "/company-job-salary",
        {"company": company, "job_title": job_title, "location": location}
    )