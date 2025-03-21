import requests
import logging
from typing import List, Dict, Any

class OrchestratorNotifier:
    """
    Notifies the computations orchestrator that this client is done updating SMPC.
    """

    def __init__(self, orchestrator_url: str):
        self.orchestrator_url = orchestrator_url.rstrip("/")

    def notify(self, job_id: str, client_id: str, total_clients: int,
               schema_list: List[Dict[str, Any]]) -> bool:
        """
        POST {orchestratorUrl}/api/update
        Body:
          {
            "jobId": job_id,
            "clientId": client_id,
            "totalClients": total_clients,
            "schema": schema_list
          }
        Returns True if HTTP 200, else False.
        """
        url = f"{self.orchestrator_url}/api/update"
        body = {
            "jobId": job_id,
            "clientId": client_id,
            "totalClients": total_clients,
            "schema": schema_list
        }
        logging.info(f"[OrchestratorNotifier] Notifying orchestrator at: {url}")

        try:
            resp = requests.post(url, json=body, timeout=100)
            logging.info(f"[OrchestratorNotifier] Orchestrator response: {resp.status_code} - {resp.text}")
            return (resp.status_code == 200)
        except requests.RequestException as e:
            logging.warning(f"[OrchestratorNotifier] Error notifying orchestrator: {e}")
            return False
