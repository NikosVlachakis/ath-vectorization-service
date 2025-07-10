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
    parser.add_argument("--orchestratorUrl", type=str, default=None,
                        help="Base URL of the computations orchestrator (e.g. http://localhost:5000)")

    args = parser.parse_args()

    logging.info(f"Fetching JSON from: {args.url}")
    if args.query:
        logging.info(f"Only vectorizing features where name == {args.query}")

    # 1) Fetch the dataset using shared utility (supports both URLs and local files)
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

    # 2) Vectorize
    encoder_obj = Encoder()
    vectorizer = VectorizationService(encoder_obj)
    enhanced_data, encoders_list, schema_list = vectorizer.enhance_dataset(json_data, query=args.query)

    # 3) Write outputs
    os.makedirs("/app/output", exist_ok=True)
    output_path = "/app/output/enhanced_dataset.json"
    encoder_output_path = "/app/output/encoders_only.json"
    schema_output_path = "/app/output/schema.json"

    with open(output_path, "w") as f:
        json.dump(enhanced_data, f, indent=4)
    logging.info(f"Full enhanced JSON saved to: {output_path}")

    with open(encoder_output_path, "w") as f:
        json.dump(encoders_list, f, indent=4)
    logging.info(f"Encoders-only JSON saved to: {encoder_output_path}")

    with open(schema_output_path, "w") as f:
        json.dump(schema_list, f, indent=4)
    logging.info(f"Schema info saved to: {schema_output_path}")

    # 4) If smpcUrl and jobId are provided, post first encoder to SMPC
    if args.smpcUrl and args.jobId:
        smpc_service = SMPCService(base_url=args.smpcUrl)

        first_encoder = encoders_list[0] if encoders_list else {"type": "int", "data": []}
        success = smpc_service.post_first_encoder(args.jobId, first_encoder)

        # 5) If SMPC success, notify orchestrator if orchestratorUrl + clientId + totalClients given
        #    also pass schema_list to orchestrator
        if success and args.orchestratorUrl and args.clientId and args.totalClients is not None:
            notifier = OrchestratorNotifier(args.orchestratorUrl)
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
