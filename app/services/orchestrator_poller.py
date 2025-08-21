import os
import time
import json
import logging
import requests
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class OrchestratorPoller:
    """
    Polls the computations orchestrator for job completion and retrieves results.
    Used in distributed architecture where nodes can't accept incoming requests.
    """
    
    def __init__(self, 
                 orchestrator_url: str,
                 polling_interval: int = 10,
                 polling_timeout: int = 1200):
        """
        Initialize the orchestrator poller.
        
        Args:
            orchestrator_url: Base URL of computations orchestrator
            polling_interval: Seconds between polls (default: 10)
            polling_timeout: Max polling time in seconds (default: 1200 = 20 min)
        """
        self.orchestrator_url = orchestrator_url.rstrip("/")
        self.polling_interval = polling_interval
        self.polling_timeout = polling_timeout
        self.logger = logging.getLogger(__name__)
        
    def start_polling(self, job_id: str) -> None:
        """
        Start polling for job completion in a background thread.
        
        Args:
            job_id: Job identifier to poll for
        """
        self.logger.info(f"[OrchestratorPoller] Starting background polling for job {job_id}")
        self.logger.info(f"[OrchestratorPoller] Poll interval: {self.polling_interval}s, Timeout: {self.polling_timeout}s")
        
        # Start polling in background thread
        polling_thread = threading.Thread(
            target=self._poll_until_complete,
            args=(job_id,),
            daemon=True,
            name=f"OrchestratorPoller-{job_id}"
        )
        polling_thread.start()
        
    def _poll_until_complete(self, job_id: str) -> bool:
        """
        Poll orchestrator until job completes or timeout.
        
        Args:
            job_id: Job identifier to poll for
            
        Returns:
            True if completed successfully, False if timeout/error
        """
        start_time = time.time()
        poll_count = 0
        
        self.logger.info(f"[OrchestratorPoller] Starting polling for job {job_id}")
        
        while time.time() - start_time < self.polling_timeout:
            poll_count += 1
            elapsed = int(time.time() - start_time)
            
            try:
                status_data = self.poll_job_status(job_id)
                
                if status_data:
                    status = status_data.get("status", "UNKNOWN")
                    self.logger.info(f"[OrchestratorPoller] Poll #{poll_count} ({elapsed}s): Job {job_id} status = {status}")
                    
                    if status == "COMPLETED":
                        self.logger.info(f"[OrchestratorPoller] Job {job_id} completed! Retrieving results...")
                        
                        # Save results locally
                        success = self.save_results_locally(job_id, status_data)
                        if success:
                            self.logger.info(f"[OrchestratorPoller] Successfully saved results for job {job_id}")
                            return True
                        else:
                            self.logger.error(f"[OrchestratorPoller] Failed to save results for job {job_id}")
                            return False
                    
                    elif status in ["FAILED", "ERROR"]:
                        self.logger.error(f"[OrchestratorPoller] Job {job_id} failed with status: {status}")
                        return False
                    
                    # Continue polling for IN_PROGRESS, RUNNING, etc.
                    
                else:
                    self.logger.warning(f"[OrchestratorPoller] Poll #{poll_count}: No status data received for job {job_id}")
                
            except Exception as e:
                self.logger.error(f"[OrchestratorPoller] Poll #{poll_count} error for job {job_id}: {e}")
            
            # Wait before next poll
            time.sleep(self.polling_interval)
        
        # Timeout reached
        elapsed_min = (time.time() - start_time) / 60
        self.logger.error(f"[OrchestratorPoller] Polling timeout for job {job_id} after {elapsed_min:.1f} minutes")
        return False
    
    def poll_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Poll orchestrator for job status and results.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Status data dictionary or None if error
        """
        url = f"{self.orchestrator_url}/api/job-status/{job_id}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                self.logger.warning(f"[OrchestratorPoller] Job {job_id} not found (404)")
                return None
            else:
                self.logger.warning(f"[OrchestratorPoller] Unexpected status {response.status_code} for job {job_id}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"[OrchestratorPoller] Error polling job {job_id}: {e}")
            return None
    
    def save_results_locally(self, job_id: str, status_data: Dict[str, Any]) -> bool:
        """
        Save aggregated results to local filesystem.
        
        Args:
            job_id: Job identifier
            status_data: Complete status data from orchestrator
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Prepare results data (same format as AggregatedResultsHandler)
            results_data = {
                "jobId": job_id,
                "timestamp": datetime.now().isoformat(),
                "status": "COMPLETED",
                "aggregatedResults": status_data.get("aggregatedResults", []),
                "metadata": status_data.get("metadata", {}),
                "retrievedAt": datetime.now().isoformat(),
                "source": "orchestrator_polling"
            }
            
            # Create results directory
            results_dir = Path("/app/results")
            results_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{job_id}_results_{timestamp}.json"
            file_path = results_dir / filename
            
            # Write results
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"[OrchestratorPoller] Saved results to: {file_path}")
            self.logger.info(f"[OrchestratorPoller] Results contain {len(results_data.get('aggregatedResults', []))} features")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[OrchestratorPoller] Error saving results for job {job_id}: {e}")
            return False
