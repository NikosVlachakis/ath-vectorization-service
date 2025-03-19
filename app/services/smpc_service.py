import requests
import logging
from typing import Dict, Any

class SMPCService:
    """
    Handles posting an encoder object to the SMPC client.
    E.g. POST {base_url}/api/update-dataset/{jobId}
    """

    def __init__(self, base_url: str):
        """
        :param base_url: The base URL for SMPC (e.g. "http://195.251.63.193:9000")
        """
        self.base_url = base_url.rstrip("/")

    def post_first_encoder(self, job_id: str, encoder_data: Dict[str, Any]) -> bool:
        """
        Posts a single encoder object to SMPC:
          {base_url}/api/update-dataset/{jobId}

        Returns True if HTTP 200, else False.
        """
        url = f"{self.base_url}/api/update-dataset/{job_id}"
        logging.info(f"[SMPCService] Posting encoder to SMPC at: {url}")

        try:
            resp = requests.post(url, json=encoder_data, timeout=30)
            logging.info(f"[SMPCService] SMPC response: {resp.status_code} - {resp.text}")
            if resp.status_code == 200:
                logging.info("[SMPCService] Successfully posted encoder to SMPC.")
                return True
            else:
                logging.warning("[SMPCService] SMPC did not return 200. No further action.")
                return False
        except requests.RequestException as e:
            logging.warning(f"[SMPCService] Error posting encoder to SMPC: {e}")
            return False
