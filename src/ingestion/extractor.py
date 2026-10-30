from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ingestion.api_client import (
    ArbeitnowAPIClient,
    GetOnBoardChileAPIClient,
    RemotiveAPIClient,
)
from src.utils.logger import setup_logger

logger = setup_logger("extractor")


class BronzeExtractor:
    """Handles raw multi-source data extraction including Chilean & Global sources."""

    def __init__(self, raw_dir: str = "data/raw"):
        self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.remotive_client = RemotiveAPIClient()
        self.arbeitnow_client = ArbeitnowAPIClient()
        self.getonboard_client = GetOnBoardChileAPIClient()

    def run(self, category: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        ingested_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"Starting multi-source bronze extraction (Global + Chile) at {ingested_at}")

        all_jobs: List[Dict[str, Any]] = []

        # 1. Fetch Get on Board (Chile & LATAM)
        try:
            chile_jobs = self.getonboard_client.fetch_jobs()
            all_jobs.extend(chile_jobs)
            logger.info(f"Chile/LATAM records added: {len(chile_jobs)}")
        except Exception as exc:
            logger.error(f"Failed fetching from Get on Board (Chile): {exc}")

        # 2. Fetch Remotive (Global)
        try:
            remotive_jobs = self.remotive_client.fetch_jobs(category=category, limit=limit)
            all_jobs.extend(remotive_jobs)
        except Exception as exc:
            logger.error(f"Failed fetching from Remotive: {exc}")

        # 3. Fetch Arbeitnow (Europe & Global)
        try:
            arbeitnow_jobs = self.arbeitnow_client.fetch_jobs(pages=1)
            all_jobs.extend(arbeitnow_jobs)
        except Exception as exc:
            logger.error(f"Failed fetching from Arbeitnow: {exc}")

        if not all_jobs:
            logger.warning("No jobs returned by any provider.")
            return {"record_count": 0, "ingested_at": ingested_at, "file_path": None}

        # Add ingestion metadata to every record
        for job in all_jobs:
            job["_ingested_at"] = ingested_at

        # Save snapshot
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        snapshot_file = self.raw_dir / f"jobs_raw_{timestamp_str}.json"
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)

        # Save latest snapshot for warehouse reload
        latest_file = self.raw_dir / "jobs_latest.json"
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)

        logger.info(f"Bronze layer persisted: {len(all_jobs)} records saved.")

        return {
            "record_count": len(all_jobs),
            "ingested_at": ingested_at,
            "snapshot_file": str(snapshot_file),
            "latest_file": str(latest_file),
        }
