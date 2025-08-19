# vectorization_bp.py

import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify
from typing import Optional, List, Dict, Any

from encoder import Encoder
from vectorization_service import VectorizationService
from services.smpc_service import SMPCService
from services.orchestrator_notifier import OrchestratorNotifier
from utils.dataset_fetcher import DatasetFetcher

# Import self-contained logging (optional)
try:
    from logging_config import get_logger
    CENTRALIZED_LOGGING = True
except ImportError:
    CENTRALIZED_LOGGING = False

vectorization_bp = Blueprint("vectorization_bp", __name__)

@vectorization_bp.route("/vectorize", methods=["POST"])
def vectorize_endpoint():
    """
    HTTP endpoint that triggers:
      1) Dataset fetch (from URL or local file)
      2) Vectorization
      3) Writes results to local outputs
      4) Posts to SMPC
      5) Notifies Orchestrator

    Request JSON body example:
    {
      "url": "<dataset_url_or_file_path>",
      "jobId": "<job_id>",
      "clientsList": ["client1", "client2"]
    }
    
    Note: orchestratorUrl is now configured via ORCHESTRATOR_URL environment variable
    
    The "url" field can be either:
    - A URL (e.g., "http://example.com/dataset.json")
    - A local file path (e.g., "metadata-test.json", "/app/data/dataset.json")
    """
    data = request.json or {}

    # 1) Parse input arguments
    url = data.get("url")
    job_id = data.get("jobId")
    clients_list = data.get("clientsList", [])
    total_clients = len(clients_list)  # Use length of clientsList

    # retrieve environment-based info
    client_id = os.getenv("ID")          # e.g. "TestAthSmpcClient"
    smpc_url  = os.getenv("SMPC_URL")    # e.g. "http://client1:9000"
    orchestrator_url = os.getenv("ORCHESTRATOR_URL")  # e.g. "http://host.docker.internal:5000"

    if not url:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    # 2) Fetch dataset (from URL or local file) using shared utility
    fetcher = DatasetFetcher()
    try:
        logging.info(f"[Vectorize] Starting dataset fetch from: {url}")
        json_data = fetcher.fetch_dataset(url)
        logging.info(f"[Vectorize] Successfully fetched dataset from: {url}")
    except FileNotFoundError as e:
        logging.error(f"[Vectorize] File not found: {e}")
        return jsonify({"error": f"File not found: {str(e)}"}), 400
    except requests.RequestException as e:
        logging.error(f"[Vectorize] Failed to fetch dataset from {url} -> {e}")
        return jsonify({"error": f"Failed to fetch dataset: {str(e)}"}), 400
    except Exception as e:
        logging.error(f"[Vectorize] Error loading dataset from {url} -> {e}")
        return jsonify({"error": f"Error loading dataset: {str(e)}"}), 400

    # 3) Vectorize
    logging.info("[Vectorize] Starting dataset vectorization process")
    encoder_obj = Encoder()
    vectorizer = VectorizationService(encoder_obj)
    enhanced_data, encoders_list, schema_list = vectorizer.enhance_dataset(json_data)
    logging.info("[Vectorize] Dataset vectorization completed successfully")

    # 4) Write outputs
    os.makedirs("/app/output", exist_ok=True)
    output_path           = "/app/output/enhanced_dataset.json"
    encoder_output_path   = "/app/output/encoders_only.json"
    schema_output_path    = "/app/output/schema.json"

    with open(output_path, "w") as f:
        json.dump(enhanced_data, f, indent=4)
    with open(encoder_output_path, "w") as f:
        json.dump(encoders_list, f, indent=4)
    with open(schema_output_path, "w") as f:
        json.dump(schema_list, f, indent=4)

    logging.info("[Vectorize] Vectorization done; outputs written to /app/output/.")

    # 5) If SMPC + jobId are provided, post first encoder
    if smpc_url and job_id:
        smpc_service = SMPCService(base_url=smpc_url)

        first_encoder = encoders_list[0] if encoders_list else {"type": "int", "data": []}
        success = smpc_service.post_first_encoder(job_id, first_encoder)

        # 6) If SMPC success, notify orchestrator if orchestratorUrl + clientId + totalClients
        if success and orchestrator_url and client_id and total_clients is not None:
            notifier = OrchestratorNotifier(orchestrator_url)
            notified = notifier.notify(job_id, client_id, total_clients, schema_list)
            if notified:
                logging.info("[Vectorize] Successfully notified computations orchestrator.")
            else:
                logging.warning("[Vectorize] Failed to notify orchestrator.")
        else:
            logging.info("[Vectorize] SMPC update failed or missing orchestrator info; no orchestrator notify.")
    else:
        logging.info("[Vectorize] No SMPC or orchestrator arguments provided; skipping those steps.")

    return jsonify({
        "message": "Vectorization completed.",
        "outputPaths": {
            "enhancedData": output_path,
            "encodersOnly": encoder_output_path,
            "schema": schema_output_path
        },
        "encodersCount": len(encoders_list),
        "schemaCount": len(schema_list)
    }), 200
