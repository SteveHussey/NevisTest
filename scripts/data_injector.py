"""Data Injector Script for Nevis

This script reads a compressed JSON sample data file and injects the data into the
Nevis FastAPI service via its REST API.

Base code generate using Claude running against local gpt-oss:120b.

Usage:
  python data_injector.py [--dry-run]

Options:
  --dry-run   Parse the JSON file and print actions without making HTTP requests.
"""

import argparse
import gzip
import json
import logging
import sys
from logging import getLogger
from os import PathLike
from pathlib import Path
from time import perf_counter_ns

import requests

logger = getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inject sample data into Nevis API")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the file and print actions without sending requests",
    )
    return parser.parse_args()


def load_records(data_file: PathLike) -> list:
    if not data_file.is_file():
        logger.warning("Data file not found: %s", data_file)
        sys.exit(1)
    with gzip.open(data_file, "rt", encoding="utf-8") as f:
        return json.load(f)


def create_client(base_url: str, client_data: dict) -> str:
    resp = requests.post(f"{base_url}/clients", json=client_data)
    if resp.status_code != 201:
        raise RuntimeError(f"Failed to create client: {resp.status_code} {resp.text}")
    return resp.json()["id"]


def create_document(base_url: str, client_id: str, doc: dict) -> None:
    payload = {"title": doc.get("title"), "content": doc.get("content")}
    resp = requests.post(f"{base_url}/clients/{client_id}/documents", json=payload)
    if resp.status_code != 201:
        raise RuntimeError(
            f"Failed to create document for client {client_id}: {resp.status_code} {resp.text}"
        )


def main(data_file: PathLike, base_url: str) -> None:
    args = parse_args()
    records = load_records(data_file)
    start_time_ns = perf_counter_ns()
    clients_inserted = 0
    docs_inserted = 0
    for entry in records:
        client = entry.get("client")
        docs = entry.get("documents", [])
        if args.dry_run:
            logger.info("[DRY RUN] Would create client: %s", client)
            clients_inserted += 1
            for doc in docs:
                logger.info("[DRY RUN]   Would create client document: %s", doc.get('title'))
                docs_inserted += 1
            continue
        try:
            client_id = create_client(base_url, client)
            logger.info("Created client %s", client_id)
            clients_inserted += 1
            for doc in docs:
                create_document(base_url, client_id, doc)
                logger.info("  Created document '%s'", doc.get('title'))
                docs_inserted += 1
        except Exception:
            logger.exception(f"Error processing entry")

    elapsed_secs = (perf_counter_ns() - start_time_ns) / 1e9
    logger.info('Inserted %s clients and %s docs in %.2fss', clients_inserted, docs_inserted, elapsed_secs)


if __name__ == "__main__":
    fmt = f'%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s'
    logging.basicConfig(format=fmt, level=logging.INFO, stream=sys.stdout)
    logging.captureWarnings(True)

    # TODO: Allow passing these via command line arguments
    base_url = "http://127.0.0.1:8000"
    data_file = Path(__file__).resolve().parents[1] / "data" / "sample_data.json.gz"

    main(data_file, base_url)
