import pytest
from src.transformation.skill_matcher import clean_html, extract_skills, parse_salary


def test_clean_html():
    raw = "<p>Looking for a <strong>Senior Engineer</strong> with expertise.</p><br/>"
    cleaned = clean_html(raw)
    assert "<p>" not in cleaned
    assert "<strong>" not in cleaned
    assert "Senior Engineer" in cleaned


def test_extract_skills_from_tags():
    tags = ["python", "docker", "aws"]
    skills = extract_skills(text="", tags=tags)
    skill_names = [s["skill_name"] for s in skills]

    assert "Python" in skill_names
    assert "Docker" in skill_names
    assert "AWS" in skill_names


def test_extract_skills_from_text():
    text = "We build data pipelines with dbt, DuckDB and Apache Airflow on GCP."
    skills = extract_skills(text=text, tags=[])
    skill_names = [s["skill_name"] for s in skills]

    assert "dbt" in skill_names
    assert "DuckDB" in skill_names
    assert "Apache Airflow" in skill_names
    assert "GCP" in skill_names


def test_parse_salary_range():
    min_sal, max_sal, avg_sal, currency = parse_salary("$120,000 - $160,000 / yr")
    assert min_sal == 120000.0
    assert max_sal == 160000.0
    assert avg_sal == 140000.0
    assert currency == "USD"


def test_parse_salary_k_format():
    min_sal, max_sal, avg_sal, currency = parse_salary("$90k - $110k")
    assert min_sal == 90000.0
    assert max_sal == 110000.0
    assert avg_sal == 100000.0
    assert currency == "USD"


def test_parse_salary_empty_or_invalid():
    min_sal, max_sal, avg_sal, currency = parse_salary("Competitive salary + benefits")
    assert min_sal is None
    assert max_sal is None
    assert avg_sal is None
