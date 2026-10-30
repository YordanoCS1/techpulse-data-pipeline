import re
import time
from typing import Any, Dict, List, Optional
import requests
from requests.exceptions import RequestException

from src.utils.logger import setup_logger

logger = setup_logger("api_client")


class BaseAPIClient:
    """Base HTTP client with retry and error handling."""

    def __init__(self, timeout: int = 15, max_retries: int = 3, backoff_factor: float = 1.5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "TechPulse-DataPipeline/1.0 (Portfolio Project; contact: portfolio@dev.local)"
        })

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except RequestException as exc:
                logger.warning(f"Request to {url} failed on attempt {attempt}: {exc}")
                if attempt == self.max_retries:
                    logger.error(f"Max retries reached for {url}")
                    raise
                sleep_time = self.backoff_factor ** attempt
                time.sleep(sleep_time)
        return {}


class RemotiveAPIClient(BaseAPIClient):
    """Client for Remotive API (Global Remote Jobs)."""

    ENDPOINT = "https://remotive.com/api/remote-jobs"

    def fetch_jobs(self, category: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if category:
            params["category"] = category
        if limit:
            params["limit"] = limit

        logger.info("Fetching jobs from Remotive API...")
        data = self._get(self.ENDPOINT, params=params)
        raw_jobs = data.get("jobs", [])
        logger.info(f"Retrieved {len(raw_jobs)} jobs from Remotive.")

        standardized = []
        for j in raw_jobs:
            standardized.append({
                "job_id": f"remotive_{j.get('id')}",
                "source": "Remotive (Global)",
                "country_code": "GLOBAL",
                "title": j.get("title", ""),
                "company_name": j.get("company_name", "Unknown"),
                "category": j.get("category", "Software Development"),
                "tags": j.get("tags", []),
                "candidate_location": j.get("candidate_required_location", "Worldwide"),
                "url": j.get("url", ""),
                "publication_date": str(j.get("publication_date", "")),
                "job_type": j.get("job_type", "full_time"),
                "salary": j.get("salary", ""),
                "description": j.get("description", ""),
            })
        return standardized


class ArbeitnowAPIClient(BaseAPIClient):
    """Client for Arbeitnow Job Board API (European & Global Tech Hubs)."""

    ENDPOINT = "https://arbeitnow.com/api/job-board-api"

    def fetch_jobs(self, pages: int = 1) -> List[Dict[str, Any]]:
        standardized = []
        logger.info(f"Fetching jobs from Arbeitnow API (pages: {pages})...")
        for page in range(1, pages + 1):
            data = self._get(self.ENDPOINT, params={"page": page})
            raw_jobs = data.get("data", [])
            for j in raw_jobs:
                job_types = j.get("job_types", ["full_time"])
                location_str = j.get("location", "Remote" if j.get("remote") else "On-site")
                standardized.append({
                    "job_id": f"arbeitnow_{j.get('slug', j.get('created_at', ''))}",
                    "source": "Arbeitnow (Europa/Global)",
                    "country_code": "GLOBAL",
                    "title": j.get("title", ""),
                    "company_name": j.get("company_name", "Unknown"),
                    "category": (j.get("tags") or ["Tech"])[0] if j.get("tags") else "Tech",
                    "tags": j.get("tags", []),
                    "candidate_location": location_str,
                    "url": j.get("url", ""),
                    "publication_date": str(j.get("created_at", "")),
                    "job_type": job_types[0] if job_types else "full_time",
                    "salary": "",
                    "description": j.get("description", ""),
                })
        logger.info(f"Retrieved {len(standardized)} jobs from Arbeitnow.")
        return standardized


class GetOnBoardChileAPIClient(BaseAPIClient):
    """
    Client for Get on Board (Leading tech job board in Chile & Latin America).
    Fetches real tech jobs in Chile and remote positions open to Chilean candidates.
    """

    SEARCH_ENDPOINT = "https://www.getonbrd.com/api/v0/search/jobs"
    CATEGORY_ENDPOINT = "https://www.getonbrd.com/api/v0/categories/{category}/jobs"

    def _extract_company_from_url(self, public_url: str) -> str:
        """Parses company identifier from URL slug like '.../jobs/role-company-santiago'"""
        if not public_url:
            return "Empresa en Chile"
        parts = public_url.rstrip("/").split("/")[-1].split("-")
        if len(parts) >= 2:
            # Drop city if at the end (e.g. santiago)
            candidate = parts[-2] if parts[-1].lower() in ["santiago", "chile", "remoto", "remote"] else parts[-1]
            return candidate.capitalize()
        return "Empresa en Chile"

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        logger.info("Fetching Chilean tech jobs from Get on Board API...")
        standardized = []

        # 1. Search jobs explicitly tagged for Chile
        chile_data = self._get(self.SEARCH_ENDPOINT, params={"query": "chile"})
        chile_jobs = chile_data.get("data", [])

        # 2. Also fetch from data & programming categories
        prog_data = self._get(self.CATEGORY_ENDPOINT.format(category="programming"))
        prog_jobs = prog_data.get("data", [])

        all_records = chile_jobs + prog_jobs
        seen_ids = set()

        for j in all_records:
            jid = j.get("id")
            if not jid or jid in seen_ids:
                continue
            seen_ids.add(jid)

            attr = j.get("attributes", {})
            links = j.get("links", {})
            public_url = links.get("public_url", "")

            countries = attr.get("countries", [])
            is_chile = "Chile" in countries or "chile" in public_url.lower()

            # Location formatting
            if is_chile:
                location = "Chile (Santiago / Remoto)"
                country_code = "CL"
            elif attr.get("remote"):
                location = "Remoto (LATAM / Chile)"
                country_code = "LATAM"
            else:
                location = ", ".join(countries) if countries else "Chile"
                country_code = "CL" if is_chile else "LATAM"

            # Parse salary in GetOnBoard (typically monthly USD)
            min_sal = attr.get("min_salary")
            max_sal = attr.get("max_salary")
            salary_str = ""
            if min_sal and max_sal:
                # Convert monthly USD to annual USD for standardization with other global APIs
                annual_min = int(min_sal * 12)
                annual_max = int(max_sal * 12)
                salary_str = f"${annual_min:,} - ${annual_max:,} USD/año (${min_sal:,} - ${max_sal:,}/mes)"

            tags_list = attr.get("tags") or []
            if isinstance(tags_list, dict):
                tags_list = tags_list.get("data", [])

            company_name = self._extract_company_from_url(public_url)

            standardized.append({
                "job_id": f"getonboard_{jid}",
                "source": "Get on Board (Chile)",
                "country_code": country_code,
                "title": attr.get("title", ""),
                "company_name": company_name,
                "category": attr.get("category_name", "Tecnología & Software"),
                "tags": [t.get("attributes", {}).get("name", str(t)) if isinstance(t, dict) else str(t) for t in tags_list],
                "candidate_location": location,
                "url": public_url,
                "publication_date": str(attr.get("published_at", "")),
                "job_type": attr.get("modality", "full_time"),
                "salary": salary_str,
                "description": (attr.get("description", "") or "") + " " + (attr.get("functions", "") or ""),
            })

        logger.info(f"Retrieved {len(standardized)} jobs from Get on Board (Chile & LATAM).")
        return standardized
