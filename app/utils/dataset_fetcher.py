# utils/dataset_fetcher.py

import os
import json
import logging
import requests
from typing import Dict, Any
from urllib.parse import urlparse


class DatasetFetcher:
    """Utility class for fetching datasets from URLs or local files."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_url(self, string: str) -> bool:
        """Check if a string is a URL or a local file path."""
        try:
            result = urlparse(string)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def fetch_dataset(self, url_or_path: str) -> Dict[str, Any]:
        """
        Fetch dataset from either URL or local file path.
        
        Args:
            url_or_path: Either a URL or a local file path
            
        Returns:
            Dictionary containing the dataset
            
        Raises:
            Exception: If unable to fetch/read the dataset
        """
        if self.is_url(url_or_path):
            return self._fetch_from_url(url_or_path)
        else:
            return self._fetch_from_file(url_or_path)
    
    def _fetch_from_url(self, url: str) -> Dict[str, Any]:
        """Fetch dataset from URL."""
        self.logger.info(f"Fetching dataset from URL: {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    
    def _fetch_from_file(self, file_path: str) -> Dict[str, Any]:
        """Fetch dataset from local file."""
        self.logger.info(f"Reading dataset from local file: {file_path}")
        
        # Check if it's an absolute path or relative to current working directory
        if not os.path.isabs(file_path):
            # Try different locations in order of preference
            search_paths = [
                file_path,                    # Current directory
                f"/app/{file_path}",          # App directory (Docker)
                f"../{file_path}",            # Parent directory
                f"./app/{file_path}",         # Local app directory
                f"vectorization-service/{file_path}"  # From project root
            ]
            
            found_path = None
            for path in search_paths:
                if os.path.exists(path):
                    found_path = path
                    break
            
            if found_path is None:
                raise FileNotFoundError(f"Local file not found in any of: {search_paths}")
            
            file_path = found_path
        else:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Local file not found: {file_path}")
        
        self.logger.info(f"Reading from resolved path: {file_path}")
        with open(file_path, 'r') as f:
            return json.load(f) 