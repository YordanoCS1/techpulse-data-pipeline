from unittest.mock import MagicMock, patch
import pytest
from requests.exceptions import Timeout
from src.ingestion.api_client import ArbeitnowAPIClient, GetOnBoardChileAPIClient, RemotiveAPIClient


def test_api_client_init():
    client = RemotiveAPIClient(timeout=10, max_retries=2)
    assert client.timeout == 10
    assert client.max_retries == 2


@patch("requests.Session.get")
def test_remotive_fetch_jobs_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "job-count": 2,
        "jobs": [
            {"id": 1, "title": "Data Engineer", "company_name": "Tech Corp", "tags": ["python"]},
            {"id": 2, "title": "Backend Developer", "company_name": "Devs Ltd", "tags": ["docker"]},
        ],
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    client = RemotiveAPIClient()
    jobs = client.fetch_jobs(limit=2)

    assert len(jobs) == 2
    assert jobs[0]["title"] == "Data Engineer"
    assert jobs[0]["source"] == "Remotive (Global)"
    assert mock_get.call_count == 1


@patch("requests.Session.get")
def test_getonboard_chile_fetch_jobs(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "id": 999,
                "attributes": {
                    "title": "Ingeniero de Datos Senior",
                    "countries": ["Chile"],
                    "min_salary": 3000,
                    "max_salary": 4500,
                    "published_at": "2026-10-25",
                    "category_name": "Data Science / Analytics",
                },
                "links": {"public_url": "https://www.getonbrd.com/jobs/data-engineer-falabella-santiago"},
            }
        ]
    }
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    client = GetOnBoardChileAPIClient()
    jobs = client.fetch_jobs()

    assert len(jobs) >= 1
    assert jobs[0]["title"] == "Ingeniero de Datos Senior"
    assert jobs[0]["country_code"] == "CL"
    assert "Falabella" in jobs[0]["company_name"]
