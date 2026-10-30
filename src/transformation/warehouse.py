from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import duckdb

from src.transformation.skill_matcher import clean_html, extract_skills, parse_salary
from src.utils.logger import setup_logger

logger = setup_logger("warehouse")


class DataWarehouse:
    """Manages the DuckDB Analytical Lakehouse/Warehouse following Medallion architecture."""

    def __init__(self, db_path: str = "data/warehouse.duckdb"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.con = duckdb.connect(str(self.db_path))

    def close(self):
        self.con.close()

    def build_all(self, raw_json_path: str = "data/raw/jobs_latest.json") -> Dict[str, Any]:
        """Builds the entire Medallion Architecture: Bronze -> Silver -> Gold."""
        logger.info(f"Loading raw data from {raw_json_path}")
        with open(raw_json_path, "r", encoding="utf-8") as f:
            raw_jobs: List[Dict[str, Any]] = json.load(f)

        if not raw_jobs:
            logger.warning("Empty raw data. Skipping warehouse build.")
            return {"status": "empty"}

        bronze_count = self._build_bronze(raw_jobs)
        silver_jobs_count, silver_skills_count = self._build_silver(raw_jobs)
        self._build_gold()

        logger.info("Data Warehouse build completed successfully!")
        return {
            "status": "success",
            "bronze_records": bronze_count,
            "silver_jobs": silver_jobs_count,
            "silver_skills": silver_skills_count,
            "db_path": str(self.db_path),
        }

    def _build_bronze(self, raw_jobs: List[Dict[str, Any]]) -> int:
        """Stores raw records into bronze.raw_jobs table."""
        logger.info("Building Bronze layer (bronze.raw_jobs)...")
        self.con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")
        self.con.execute("""
            CREATE OR REPLACE TABLE bronze.raw_jobs (
                job_id VARCHAR,
                source VARCHAR,
                payload JSON,
                ingested_at TIMESTAMP
            );
        """)

        records = [
            (
                str(job.get("job_id", "")),
                job.get("source", "Unknown"),
                json.dumps(job, ensure_ascii=False),
                job.get("_ingested_at", datetime.now(timezone.utc).isoformat()),
            )
            for job in raw_jobs if job.get("job_id")
        ]

        self.con.executemany("INSERT INTO bronze.raw_jobs VALUES (?, ?, ?, ?)", records)
        count = self.con.execute("SELECT count(*) FROM bronze.raw_jobs").fetchone()[0]
        logger.info(f"Bronze layer populated with {count} records.")
        return count

    def _build_silver(self, raw_jobs: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Transforms and normalizes into silver.jobs and silver.job_skills."""
        logger.info("Building Silver layer (silver.jobs and silver.job_skills)...")
        self.con.execute("CREATE SCHEMA IF NOT EXISTS silver;")

        cleaned_jobs = []
        skills_records = []
        seen_ids = set()

        for job in raw_jobs:
            job_id = str(job.get("job_id", "")).strip()
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            source = job.get("source", "Unknown")
            country_code = job.get("country_code", "GLOBAL")
            title = (job.get("title") or "").strip()
            company = (job.get("company_name") or "Unknown").strip()
            category = (job.get("category") or "General Tech").strip()
            raw_desc = job.get("description") or ""
            clean_desc = clean_html(raw_desc)
            tags = job.get("tags") or []
            location = (job.get("candidate_location") or "Worldwide").strip()
            url = job.get("url") or ""
            pub_date = str(job.get("publication_date") or "")
            job_type = job.get("job_type") or "full_time"
            salary_raw = job.get("salary") or ""

            min_sal, max_sal, avg_sal, currency = parse_salary(salary_raw)

            cleaned_jobs.append((
                job_id,
                source,
                country_code,
                title,
                company,
                category,
                clean_desc[:3000],
                location,
                url,
                pub_date,
                job_type,
                salary_raw,
                min_sal,
                max_sal,
                avg_sal,
                currency,
            ))

            extracted = extract_skills(title + " " + clean_desc, tags)
            for sk in extracted:
                skills_records.append((job_id, sk["skill_name"], sk["skill_category"]))

        self.con.execute("""
            CREATE OR REPLACE TABLE silver.jobs (
                job_id VARCHAR PRIMARY KEY,
                source VARCHAR,
                country_code VARCHAR,
                title VARCHAR,
                company_name VARCHAR,
                category VARCHAR,
                clean_description VARCHAR,
                candidate_location VARCHAR,
                url VARCHAR,
                publication_date VARCHAR,
                job_type VARCHAR,
                salary_raw VARCHAR,
                salary_min DOUBLE,
                salary_max DOUBLE,
                salary_avg DOUBLE,
                salary_currency VARCHAR
            );
        """)

        self.con.executemany("""
            INSERT INTO silver.jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, cleaned_jobs)

        self.con.execute("""
            CREATE OR REPLACE TABLE silver.job_skills (
                job_id VARCHAR,
                skill_name VARCHAR,
                skill_category VARCHAR
            );
        """)

        self.con.executemany("""
            INSERT INTO silver.job_skills VALUES (?, ?, ?)
        """, skills_records)

        jobs_count = len(cleaned_jobs)
        skills_count = len(skills_records)
        logger.info(f"Silver layer ready: {jobs_count} unique jobs, {skills_count} skill associations.")
        return jobs_count, skills_count

    def _build_gold(self):
        """Builds analytical marts for the BI dashboard."""
        logger.info("Building Gold analytical marts (gold schema)...")
        self.con.execute("CREATE SCHEMA IF NOT EXISTS gold;")

        # Mart 1: Top in-demand skills
        self.con.execute("""
            CREATE OR REPLACE VIEW gold.mart_skills_demand AS
            WITH total_jobs AS (
                SELECT COUNT(DISTINCT job_id) as total_count FROM silver.jobs
            ),
            skill_stats AS (
                SELECT 
                    s.skill_name,
                    s.skill_category,
                    COUNT(DISTINCT s.job_id) AS job_count,
                    ROUND(AVG(j.salary_avg), 0) AS avg_salary_usd
                FROM silver.job_skills s
                JOIN silver.jobs j ON s.job_id = j.job_id
                GROUP BY s.skill_name, s.skill_category
            )
            SELECT 
                st.skill_name,
                st.skill_category,
                st.job_count,
                ROUND((st.job_count * 100.0) / t.total_count, 1) AS percent_of_jobs,
                st.avg_salary_usd
            FROM skill_stats st
            CROSS JOIN total_jobs t
            ORDER BY st.job_count DESC;
        """)

        # Mart 2: Job categories & sources overview
        self.con.execute("""
            CREATE OR REPLACE VIEW gold.mart_category_insights AS
            SELECT 
                category,
                source,
                COUNT(*) AS total_jobs,
                COUNT(salary_avg) AS jobs_with_salary,
                ROUND(AVG(salary_avg), 0) AS avg_salary_usd
            FROM silver.jobs
            GROUP BY category, source
            ORDER BY total_jobs DESC;
        """)

        # Mart 3: Top candidate locations
        self.con.execute("""
            CREATE OR REPLACE VIEW gold.mart_location_distribution AS
            SELECT 
                candidate_location,
                COUNT(*) AS job_count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM silver.jobs), 1) as percentage
            FROM silver.jobs
            GROUP BY candidate_location
            ORDER BY job_count DESC
            LIMIT 25;
        """)

        # Mart 4: Dashboard searchable view with country_code
        self.con.execute("""
            CREATE OR REPLACE VIEW gold.mart_job_search AS
            SELECT 
                j.job_id,
                j.source,
                j.country_code,
                j.title,
                j.company_name,
                j.category,
                j.candidate_location,
                j.salary_raw,
                j.salary_avg,
                j.url,
                j.publication_date,
                COALESCE(STRING_AGG(s.skill_name, ', '), '') AS skills_list
            FROM silver.jobs j
            LEFT JOIN silver.job_skills s ON j.job_id = s.job_id
            GROUP BY 
                j.job_id, j.source, j.country_code, j.title, j.company_name, 
                j.category, j.candidate_location, j.salary_raw, j.salary_avg, 
                j.url, j.publication_date
            ORDER BY j.publication_date DESC;
        """)

        logger.info("Gold marts created successfully.")
