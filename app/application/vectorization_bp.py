# vectorization_bp.py

import os
import json
import logging
import requests
from flask import Blueprint, request, jsonify
from typing import Optional, List, Dict, Any
from datetime import datetime

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
      3) Posts to SMPC
      4) Notifies Orchestrator

    Request JSON body example:
    {
      "url": "<dataset_url_or_file_path>",
      "jobId": "<job_id>",
      "clientsList": ["client1", "client2"],
      "studyId": "<study_id>" (required, used for production mode Feature Extraction Tool API)
    }
    """
    data = request.json or {}

    # Parse input arguments
    url = data.get("url")
    job_id = data.get("jobId")
    clients_list = data.get("clientsList", [])
    study_id = data.get("studyId") 
    total_clients = len(clients_list)  

    # retrieve environment-based info
    client_id = os.getenv("ID")        
    smpc_url  = os.getenv("SMPC_URL")  
    orchestrator_url = os.getenv("ORCHESTRATOR_URL")
    production_mode = os.getenv("PRODUCTION_MODE", "false").lower() == "true"

    # Generate unique execution ID for this specific run
    execution_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    execution_id = f"{job_id}_{execution_timestamp}"

    # Function to log with execution markers for precise filtering
    def log_info(message):
        logging.info(f"[EXEC:{execution_id}] {message}")
    
    def log_error(message):
        logging.error(f"[EXEC:{execution_id}] {message}")

    # Conditional dataset fetching based on PRODUCTION_MODE
    fetcher = DatasetFetcher()
    try:
        if production_mode:
            # Production Mode: Call Feature Extraction Tool API with URL as base + studyId as parameter
            if not url:
                return jsonify({"error": "Missing 'url' in request body (required as base URL in production mode)"}), 400
            
            log_info(f"[Vectorize] Production mode enabled - calling Feature Extraction Tool API")
            log_info(f"[Vectorize] Base URL: {url}, StudyId: {study_id}")
            json_data = fetcher.fetch_from_api(url, study_id)
        else:
            # Development Mode: Use existing dataset fetcher (URL or local file)
            if not url:
                return jsonify({"error": "Missing 'url' in request body (required in development mode)"}), 400
            
            log_info(f"[Vectorize] Development mode - fetching dataset from: {url} (studyId {study_id} provided but ignored)")
            json_data = fetcher.fetch_dataset(url)
            log_info(f"[Vectorize] Successfully fetched dataset from: {url}")
            
            
    except FileNotFoundError as e:
        log_error(f"[Vectorize] File not found: {e}")
        return jsonify({"error": f"File not found: {str(e)}"}), 400
    except requests.RequestException as e:
        log_error(f"[Vectorize] Failed to fetch dataset: {e}")
        return jsonify({"error": f"Failed to fetch dataset: {str(e)}"}), 400
    except Exception as e:
        log_error(f"[Vectorize] Error loading dataset: {e}")
        return jsonify({"error": f"Error loading dataset: {str(e)}"}), 400

    # Vectorize
    log_info("[Vectorize] Starting dataset vectorization process")
    encoder_obj = Encoder()
    vectorizer = VectorizationService(encoder_obj)
    enhanced_data, encoders_list, schema_list = vectorizer.enhance_dataset(json_data)
    log_info("[Vectorize] Dataset vectorization completed successfully")

    # Vectorization complete - no intermediate files saved (production clean)

    # If SMPC + jobId are provided, post combined encoder data
    if smpc_url and job_id:
        smpc_service = SMPCService(base_url=smpc_url)

        # Combine all encoder data into one array for SMPC
        combined_data = []
        for encoder in encoders_list:
            encoder_data = encoder.get("data", [])
            combined_data.extend(encoder_data)
        
        # Create combined encoder object
        combined_encoder = {
            "type": "int",
            "data": combined_data
        }
        
        log_info(f"[Vectorize] Sending combined encoder to SMPC: {len(combined_data)} elements")
        log_info(f"[Vectorize] Combined data: {combined_data}")
        
        success = smpc_service.post_first_encoder(job_id, combined_encoder)

        # If SMPC success, notify orchestrator if orchestratorUrl + clientId + totalClients
        if success and orchestrator_url and client_id and total_clients is not None:
            notifier = OrchestratorNotifier(orchestrator_url)
            notified = notifier.notify(job_id, client_id, total_clients, schema_list)
            if notified:
                log_info("[Vectorize] Successfully notified computations orchestrator.")
                
                # 7) Start polling for results if enabled (distributed architecture)
                enable_polling = os.getenv("ENABLE_RESULT_POLLING", "false").lower() == "true"
                if enable_polling:
                    polling_interval = int(os.getenv("POLLING_INTERVAL", "10"))
                    polling_timeout = int(os.getenv("POLLING_TIMEOUT", "1200"))
                    
                    log_info(f"[Vectorize] Starting result polling for job {job_id}")
                    poller = OrchestratorPoller(
                        orchestrator_url=orchestrator_url,
                        polling_interval=polling_interval,
                        polling_timeout=polling_timeout
                    )
                    poller.start_polling(job_id)
                else:
                    log_info("[Vectorize] Result polling disabled - using current architecture")
            else:
                log_error("[Vectorize] Failed to notify orchestrator.")
        else:
            log_info("[Vectorize] SMPC update failed or missing orchestrator info; no orchestrator notify.")
    else:
        log_info("[Vectorize] No SMPC or orchestrator arguments provided; skipping those steps.")

    return jsonify({
        "message": "Vectorization completed.",
        "encodersCount": len(encoders_list),
        "schemaCount": len(schema_list),
        "dataProcessedInMemory": True
    }), 200


def get_latest_file_for_job(job_id: str, directory: str, pattern: str) -> Optional[str]:
    """
    Get the most recent file for a specific job_id based on modification time.
    
    Args:
        job_id: Job identifier to search for
        directory: Directory to search in
        pattern: Pattern that must be in filename (e.g., "_results_", "_logs_")
    
    Returns:
        Path to latest file or None if not found
    """
    if not os.path.exists(directory):
        return None
        
    matching_files = []
    for file in os.listdir(directory):
        if job_id in file and pattern in file:
            file_path = os.path.join(directory, file)
            mod_time = os.path.getmtime(file_path)
            matching_files.append((mod_time, file_path))
    
    if matching_files:
        # Return most recent file (highest timestamp)
        latest_file = max(matching_files, key=lambda x: x[0])[1]
        return latest_file
    return None


def get_job_logs(job_id: str) -> str:
    """
    Get log entries for the latest execution of a specific job_id using execution markers.
    
    Args:
        job_id: Job identifier to filter logs for
    
    Returns:
        Filtered log content for the latest execution of the job
    """
    log_content = ""
    log_path = "/app/logs/vectorization-service.log"
    
    if os.path.exists(log_path):
        try:
            with open(log_path, "r") as f:
                all_logs = f.read()
                
                # Find all execution IDs for this job_id
                execution_ids = []
                for line in all_logs.split('\n'):
                    if f"[EXEC:{job_id}_" in line:
                        # Extract execution_id from log line
                        start = line.find(f"[EXEC:{job_id}_") + 6  # Skip "[EXEC:"
                        end = line.find("]", start)
                        if end > start:
                            exec_id = line[start:end]
                            if exec_id not in execution_ids:
                                execution_ids.append(exec_id)
                
                if execution_ids:
                    # Get latest execution_id (highest timestamp)
                    latest_execution_id = max(execution_ids)
                    
                    # Filter logs for latest execution + related service logs
                    job_logs = []
                    for line in all_logs.split('\n'):
                        if (f"[EXEC:{latest_execution_id}]" in line or 
                            f"job {job_id}" in line or 
                            (job_id in line and any(keyword in line for keyword in ["SMPCService", "OrchestratorNotifier", "OrchestratorPoller"]))):
                            job_logs.append(line)
                    
                    log_content = '\n'.join(job_logs)
                else:
                    # Fallback - look for any logs with job_id
                    job_logs = [line for line in all_logs.split('\n') if job_id in line]
                    log_content = '\n'.join(job_logs)
                    
        except Exception as e:
            logging.error(f"[ExportAPI] Error reading logs for job {job_id}: {e}")
            log_content = f"Error reading logs: {e}"
    else:
        log_content = "Main log file not found"
    
    return log_content


@vectorization_bp.route("/export-data/<job_id>", methods=["GET"])
def export_job_data(job_id):
    """
    Export logs and results for specific job to FEM.
    Used by trigger-vectorization service to collect data for FEM sandbox.
    
    Args:
        job_id: Job identifier to export data for
    
    Returns:
        JSON with logs, results, and completion status
    """
    try:
        logging.info(f"[ExportAPI] Export request for job {job_id}")
        
        # 1. Check if results exist (completion indicator)
        latest_result_file = get_latest_file_for_job(job_id, "/app/results", "_results_")
        
        if not latest_result_file:
            # Pipeline still running or failed
            logging.info(f"[ExportAPI] No results found for job {job_id} - pipeline still running")
            return jsonify({
                "jobId": job_id,
                "status": "not_ready",
                "message": "Pipeline still running or failed - no results available yet"
            }), 202  # HTTP 202 = Accepted but processing
        
        # 2. Get latest results (completion confirmed)
        with open(latest_result_file, "r") as f:
            results_content = json.load(f)
        
        # 3. Get job-specific logs
        log_content = get_job_logs(job_id)
        
        logging.info(f"[ExportAPI] Successfully exported data for job {job_id}")
        logging.info(f"[ExportAPI] Result file: {os.path.basename(latest_result_file)}")
        
        return jsonify({
            "jobId": job_id,
            "logs": log_content,
            "results": results_content,
            "status": "completed",
            "resultFile": os.path.basename(latest_result_file),
            "exportTimestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"[ExportAPI] Error exporting data for job {job_id}: {e}")
        return jsonify({
            "jobId": job_id,
            "status": "error",
            "error": str(e)
        }), 500
