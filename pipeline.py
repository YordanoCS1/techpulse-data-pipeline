#!/usr/bin/env python3
"""
TechPulse Data Pipeline CLI
Executes the End-to-End ELT pipeline:
  1. API Ingestion (Bronze Layer)
  2. Data Modeling & Cleaning (Silver Layer)
  3. Analytical Marts Generation (Gold Layer)
"""

import argparse
import sys
import time
from pathlib import Path

from src.ingestion.extractor import BronzeExtractor
from src.transformation.warehouse import DataWarehouse
from src.utils.logger import setup_logger

logger = setup_logger("pipeline_runner")


def run_pipeline(category: str = None, limit: int = None, skip_extract: bool = False):
    start_time = time.time()
    logger.info("==================================================")
    logger.info("       TECHPULSE DATA PIPELINE EXECUTION          ")
    logger.info("==================================================")

    raw_path = "data/raw/jobs_latest.json"

    # Step 1: Extraction
    if not skip_extract:
        logger.info("[STEP 1/2] Ingesting raw data from Remotive API...")
        extractor = BronzeExtractor(raw_dir="data/raw")
        result = extractor.run(category=category, limit=limit)
        if result["record_count"] == 0:
            logger.error("Extraction failed or returned 0 records.")
            sys.exit(1)
        raw_path = result["latest_file"]
    else:
        logger.info("[STEP 1/2] Skipping extraction, using existing raw snapshot...")
        if not Path(raw_path).exists():
            logger.error(f"Cannot skip extraction: {raw_path} not found.")
            sys.exit(1)

    # Step 2: Warehouse Modeling (Bronze -> Silver -> Gold)
    logger.info("[STEP 2/2] Transforming and modeling in DuckDB Lakehouse...")
    warehouse = DataWarehouse(db_path="data/warehouse.duckdb")
    try:
        wh_summary = warehouse.build_all(raw_json_path=raw_path)
    finally:
        warehouse.close()

    elapsed = round(time.time() - start_time, 2)
    logger.info("==================================================")
    logger.info("              PIPELINE COMPLETED!                 ")
    logger.info(f" Execution Time : {elapsed} seconds")
    logger.info(f" Bronze Records : {wh_summary.get('bronze_records')}")
    logger.info(f" Silver Jobs    : {wh_summary.get('silver_jobs')}")
    logger.info(f" Silver Skills  : {wh_summary.get('silver_skills')}")
    logger.info(f" DuckDB File    : {wh_summary.get('db_path')}")
    logger.info("==================================================")


def main():
    parser = argparse.ArgumentParser(description="Run TechPulse Data Pipeline")
    parser.add_argument("--category", type=str, default=None, help="Filter API by category (e.g., software-dev, data)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of jobs to fetch")
    parser.add_argument("--skip-extract", action="store_true", help="Rebuild warehouse from cached raw data")
    args = parser.parse_args()

    run_pipeline(category=args.category, limit=args.limit, skip_extract=args.skip_extract)


if __name__ == "__main__":
    main()
