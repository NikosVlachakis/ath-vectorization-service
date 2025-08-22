#!/usr/bin/env python
import os
import json
import argparse
import logging
import requests

from typing import Optional, List, Dict, Any

from encoder import Encoder
from vectorization_service import VectorizationService
from services.smpc_service import SMPCService
from services.orchestrator_notifier import OrchestratorNotifier
from utils.dataset_fetcher import DatasetFetcher

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    parser = argparse.ArgumentParser(description="Vectorize JSON data, update SMPC, and notify orchestrator.")
    parser.add_argument("--url", type=str, required=True,
                        help="The URL or local file path that contains the JSON to be vectorized.")
    parser.add_argument("--query", type=str, default=None,
                        help="Optional: only vectorize features with this exact name.")
    parser.add_argument("--jobId", type=str, default=None,
                        help="Job ID for SMPC + orchestrator calls.")
    parser.add_argument("--clientId", type=str, default=None,
                        help="Unique client ID for orchestrator notify.")
    parser.add_argument("--totalClients", type=int, default=None,
                        help="Number of total clients for orchestrator.")
    parser.add_argument("--smpcUrl", type=str, default="http://195.251.63.193:9000",
                        help="Base URL of SMPC")
    # orchestratorUrl is now configured via ORCHESTRATOR_URL environment variable

    args = parser.parse_args()

    logging.info(f"Fetching JSON from: {args.url}")
    if args.query:
        logging.info(f"Only vectorizing features where name == {args.query}")

    # Fetch the dataset using shared utility (supports both URLs and local files)
    fetcher = DatasetFetcher()
    try:
        json_data = fetcher.fetch_dataset(args.url)
    except FileNotFoundError as e:
        logging.error(f"[Main] File not found: {e}")
        return
    except requests.RequestException as e:
        logging.error(f"[Main] Failed to fetch dataset from {args.url} -> {e}")
        return
    except Exception as e:
        logging.error(f"[Main] Error loading dataset from {args.url} -> {e}")
        return

    # Vectorize
    encoder_obj = Encoder()
    vectorizer = VectorizationService(encoder_obj)
    enhanced_data, encoders_list, schema_list = vectorizer.enhance_dataset(json_data, query=args.query)

    # If smpcUrl and jobId are provided, post first encoder to SMPC
    if args.smpcUrl and args.jobId:
        smpc_service = SMPCService(base_url=args.smpcUrl)

        first_encoder = encoders_list[0] if encoders_list else {"type": "int", "data": []}
        success = smpc_service.post_first_encoder(args.jobId, first_encoder)

        # If SMPC success, notify orchestrator if orchestratorUrl + clientId + totalClients given
        #    also pass schema_list to orchestrator
        orchestrator_url = os.getenv("ORCHESTRATOR_URL")
        if success and orchestrator_url and args.clientId and args.totalClients is not None:
            notifier = OrchestratorNotifier(orchestrator_url)
            notified = notifier.notify(args.jobId, args.clientId, args.totalClients, schema_list)
            if notified:
                logging.info("[Main] Successfully notified computations orchestrator.")
            else:
                logging.warning("[Main] Failed to notify orchestrator.")
        else:
            logging.info("[Main] SMPC update not successful or missing orchestrator info; no orchestrator notify.")
    else:
        logging.info("[Main] No SMPC or orchestrator arguments provided, skipping those steps.")

if __name__ == "__main__":
    main()
