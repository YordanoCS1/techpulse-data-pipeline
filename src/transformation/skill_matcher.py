import re
from typing import Dict, List, Optional, Set, Tuple


TECH_TAXONOMY: Dict[str, List[str]] = {
    # Data & AI
    "SQL": [r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b"],
    "Python": [r"\bpython\b"],
    "dbt": [r"\bdbt\b"],
    "DuckDB": [r"\bduckdb\b"],
    "Pandas": [r"\bpandas\b"],
    "Apache Spark": [r"\bspark\b", r"\bpyspark\b"],
    "Apache Airflow": [r"\bairflow\b"],
    "Apache Kafka": [r"\bkafka\b"],
    "Snowflake": [r"\bsnowflake\b"],
    "BigQuery": [r"\bbigquery\b"],
    "Databricks": [r"\bdatabricks\b"],
    "Tableau": [r"\btableau\b"],
    "Power BI": [r"\bpower\s*bi\b"],
    "Machine Learning": [r"\bmachine\s*learning\b", r"\bml\b"],
    "PyTorch": [r"\bpytorch\b"],
    "TensorFlow": [r"\btensorflow\b"],

    # Cloud & DevOps
    "AWS": [r"\baws\b", r"\bamazon\s*web\s*services\b"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle\s*cloud\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "Terraform": [r"\bterraform\b"],
    "CI/CD": [r"\bci\/cd\b", r"\bci-cd\b", r"\bgithub\s*actions\b"],
    "Linux": [r"\blinux\b"],

    # Software Engineering & Languages
    "JavaScript": [r"\bjavascript\b"],
    "TypeScript": [r"\btypescript\b"],
    "React": [r"\breact\b", r"\breactjs\b"],
    "Node.js": [r"\bnode\.?js\b", r"\bnode\b"],
    "Next.js": [r"\bnext\.?js\b"],
    "Go": [r"\bgolang\b", r"\bgo\s+developer\b", r"\bexperience\s+with\s+go\b"],
    "Java": [r"\bjava\b"],
    "C#": [r"\bc#\b", r"\bcsharp\b"],
    "Rust": [r"\brust\b"],
    "FastAPI": [r"\bfastapi\b"],
    "Django": [r"\bdjango\b"],
    "GraphQL": [r"\bgraphql\b"],
}

SKILL_CATEGORY: Dict[str, str] = {
    "SQL": "Data Engineering",
    "Python": "Data Engineering",
    "dbt": "Data Engineering",
    "DuckDB": "Data Engineering",
    "Pandas": "Data Engineering",
    "Apache Spark": "Data Engineering",
    "Apache Airflow": "Data Engineering",
    "Apache Kafka": "Data Engineering",
    "Snowflake": "Data Engineering",
    "BigQuery": "Data Engineering",
    "Databricks": "Data Engineering",
    "Tableau": "Data Analytics",
    "Power BI": "Data Analytics",
    "Machine Learning": "AI & ML",
    "PyTorch": "AI & ML",
    "TensorFlow": "AI & ML",
    "AWS": "Cloud & DevOps",
    "Azure": "Cloud & DevOps",
    "GCP": "Cloud & DevOps",
    "Docker": "Cloud & DevOps",
    "Kubernetes": "Cloud & DevOps",
    "Terraform": "Cloud & DevOps",
    "CI/CD": "Cloud & DevOps",
    "Linux": "Cloud & DevOps",
    "JavaScript": "Web Development",
    "TypeScript": "Web Development",
    "React": "Web Development",
    "Node.js": "Web Development",
    "Next.js": "Web Development",
    "Go": "Backend",
    "Java": "Backend",
    "C#": "Backend",
    "Rust": "Backend",
    "FastAPI": "Backend",
    "Django": "Backend",
    "GraphQL": "Web Development",
}


def clean_html(raw_html: str) -> str:
    """Removes HTML tags and normalizes whitespace."""
    if not raw_html:
        return ""
    clean_text = re.sub(r"<[^>]+>", " ", raw_html)
    clean_text = re.sub(r"\s+", " ", clean_text)
    return clean_text.strip()


def extract_skills(text: str, tags: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Extracts standardized tech skills from job text and tags.
    
    Returns:
        List of dicts with keys: {'skill_name': str, 'skill_category': str}
    """
    found_skills: Set[str] = set()

    # 1. Match from explicit tags
    if tags:
        for tag in tags:
            tag_clean = tag.lower().strip()
            for skill, patterns in TECH_TAXONOMY.items():
                if any(re.search(pat, tag_clean, re.IGNORECASE) for pat in patterns):
                    found_skills.add(skill)

    # 2. Match from text (title + description)
    text_lower = text.lower() if text else ""
    for skill, patterns in TECH_TAXONOMY.items():
        if skill in found_skills:
            continue
        if any(re.search(pat, text_lower, re.IGNORECASE) for pat in patterns):
            found_skills.add(skill)

    return [
        {
            "skill_name": skill,
            "skill_category": SKILL_CATEGORY.get(skill, "General Tech"),
        }
        for skill in sorted(found_skills)
    ]


def parse_salary(salary_raw: Optional[str]) -> Tuple[Optional[float], Optional[float], Optional[float], str]:
    """
    Parses a salary string into min, max, avg and currency.
    Examples:
        "$120,000 - $150,000" -> (120000.0, 150000.0, 135000.0, "USD")
        "$100k - $130k / year" -> (100000.0, 130000.0, 115000.0, "USD")
        "€70,000 - €90,000" -> (70000.0, 90000.0, 80000.0, "EUR")
    """
    if not salary_raw or not isinstance(salary_raw, str):
        return None, None, None, "UNKNOWN"

    currency = "USD"
    if "€" in salary_raw or "eur" in salary_raw.lower():
        currency = "EUR"
    elif "£" in salary_raw or "gbp" in salary_raw.lower():
        currency = "GBP"

    # Normalize 'k' or 'K' to thousands (e.g., 120k -> 120000)
    cleaned = salary_raw.replace(",", "")
    cleaned = re.sub(r"(\d+)\s*[kK]\b", lambda m: str(int(m.group(1)) * 1000), cleaned)

    numbers = [float(n) for n in re.findall(r"\b\d{4,7}\b", cleaned)]

    if not numbers:
        return None, None, None, currency

    if len(numbers) == 1:
        val = numbers[0]
        # Filter unreasonable hourly/monthly or out of bound values for annual salary
        if 20000 <= val <= 600000:
            return val, val, val, currency
        return None, None, None, currency

    min_sal = min(numbers)
    max_sal = max(numbers)

    # Discard non-realistic ranges
    if min_sal >= 20000 and max_sal <= 600000 and min_sal <= max_sal:
        avg_sal = round((min_sal + max_sal) / 2.0, 2)
        return min_sal, max_sal, avg_sal, currency

    return None, None, None, currency
