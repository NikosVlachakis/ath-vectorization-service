# utils/dataset_fetcher.py

import os
import json
import logging
import requests
from typing import Dict, Any
from urllib.parse import urlparse


class DatasetFetcher:
    """Utility class for fetching datasets from URLs, local files, or Feature Extraction Tool API."""
    
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
    
    def fetch_from_api(self, base_url: str, study_id: str) -> Dict[str, Any]:
        """
        Fetch dataset from Feature Extraction Tool API using base URL and studyId.
        
        Args:
            base_url: Base URL for the Feature Extraction Tool API (e.g., "https://api.example.com/api/Dataset")
            study_id: Study identifier for the API call (e.g., "study1-fs")
            
        Returns:
            Dictionary containing the dataset (same format as local/URL datasets)
            
        Raises:
            requests.RequestException: If API call fails
            Exception: If response format is invalid
        """
        # Use provided base URL (flexible for different environments)
        api_url = base_url.rstrip('/')
        
        self.logger.info(f"Fetching dataset from Feature Extraction Tool API with studyId: {study_id}")
        self.logger.info(f"API endpoint: {api_url}?featureSetId={study_id}")
        
        try:
            response = requests.get(api_url, params={"featureSetId": study_id}, timeout=30)
            response.raise_for_status()
            
            api_data = response.json()
            self.logger.info(f"Successfully fetched dataset from API for studyId: {study_id}")
            
            return api_data
            
        except requests.RequestException as e:
            self.logger.error(f"API call failed for studyId {study_id}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error processing API response for studyId {study_id}: {e}")
            raise 