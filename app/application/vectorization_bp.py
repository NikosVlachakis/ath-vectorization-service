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
from services.orchestrator_poller import OrchestratorPoller

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
      "clientsList": ["client1", "client2"],
      "studyId": "<study_id>" (required, used for production mode Feature Extraction Tool API)
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
    study_id = data.get("studyId")  # Required for Feature Extraction Tool API
    total_clients = len(clients_list)  # Use length of clientsList

    # retrieve environment-based info
    client_id = os.getenv("ID")          # e.g. "TestAthSmpcClient"
    smpc_url  = os.getenv("SMPC_URL")    # e.g. "http://client1:9000"
    orchestrator_url = os.getenv("ORCHESTRATOR_URL")  # e.g. "http://host.docker.internal:5000"
    production_mode = os.getenv("PRODUCTION_MODE", "false").lower() == "true"

    # 2) Conditional dataset fetching based on PRODUCTION_MODE
    fetcher = DatasetFetcher()
    try:
        if production_mode:
            # Production Mode: Call Feature Extraction Tool API with URL as base + studyId as parameter
            if not url:
                return jsonify({"error": "Missing 'url' in request body (required as base URL in production mode)"}), 400
            
            logging.info(f"[Vectorize] Production mode enabled - calling Feature Extraction Tool API")
            logging.info(f"[Vectorize] Base URL: {url}, StudyId: {study_id}")
            json_data = fetcher.fetch_from_api(url, study_id)
        else:
            # Development Mode: Use existing dataset fetcher (URL or local file)
            if not url:
                return jsonify({"error": "Missing 'url' in request body (required in development mode)"}), 400
            
            logging.info(f"[Vectorize] Development mode - fetching dataset from: {url} (studyId {study_id} provided but ignored)")
            json_data = fetcher.fetch_dataset(url)
            logging.info(f"[Vectorize] Successfully fetched dataset from: {url}")
            
    except FileNotFoundError as e:
        logging.error(f"[Vectorize] File not found: {e}")
        return jsonify({"error": f"File not found: {str(e)}"}), 400
    except requests.RequestException as e:
        logging.error(f"[Vectorize] Failed to fetch dataset: {e}")
        return jsonify({"error": f"Failed to fetch dataset: {str(e)}"}), 400
    except Exception as e:
        logging.error(f"[Vectorize] Error loading dataset: {e}")
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
                
                # 7) Start polling for results if enabled (distributed architecture)
                enable_polling = os.getenv("ENABLE_RESULT_POLLING", "false").lower() == "true"
                if enable_polling:
                    polling_interval = int(os.getenv("POLLING_INTERVAL", "10"))
                    polling_timeout = int(os.getenv("POLLING_TIMEOUT", "1200"))
                    
                    logging.info(f"[Vectorize] Starting result polling for job {job_id}")
                    poller = OrchestratorPoller(
                        orchestrator_url=orchestrator_url,
                        polling_interval=polling_interval,
                        polling_timeout=polling_timeout
                    )
                    poller.start_polling(job_id)
                else:
                    logging.info("[Vectorize] Result polling disabled - using current architecture")
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
