from typing import Any, Dict, Optional, List, Union, Tuple
from encoder import Encoder
import logging

class VectorizationService:
    """
    Class that performs vectorization of BOOLEAN, NUMERIC, and CATEGORICAL features.
    """

    def __init__(self, encoder: Encoder):
        self._encoder = encoder
        self._logger = logging.getLogger(__name__)

    def _vectorize_boolean_stats(self, statistics: Dict[str, Any]) -> List[int]:
        """
        Internal method to convert boolean statistics into a numeric vector:
        [numOfNotNull, numOfTrue].
        """
        num_not_null = statistics.get("numOfNotNull", 0)
        num_true = statistics.get("numOfTrue", 0)
        return [num_not_null, num_true]

    def _create_encoder_for_feature(self, feature_name: str, data_type: str, statistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to generate vectorization/encoder info for any feature type.
        
        Args:
            feature_name: Name of the feature
            data_type: Type of the feature (BOOLEAN, NUMERIC, NOMINAL, ORDINAL)
            statistics: Statistics dictionary for the feature
            
        Returns:
            Encoder object for the feature
        """
        try:
            # Use the encoder to vectorize the statistics
            vector_data = self._encoder.vectorize_feature_statistics(data_type, statistics)
            
            # Create encoder object
            encoder_obj = self._encoder.encode_feature_vector(data_type, vector_data)
            
            self._logger.info(f"Vectorized {data_type} feature '{feature_name}': {vector_data}")
            return encoder_obj
            
        except Exception as e:
            self._logger.error(f"Error vectorizing feature '{feature_name}' of type '{data_type}': {e}")
            # Return a fallback encoder
            return self._encoder.encode_feature_vector(data_type, [0])

    def _create_encoder_for_boolean_feature(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal method to generate vectorization/encoder info for a single BOOLEAN feature.
        """
        stats = feature.get("statistics", {})
        vector_data = self._vectorize_boolean_stats(stats)

        # Update the feature with the newly computed stats
        feature["vectorized_statistics"] = {
            "vectorized": vector_data,
            "encoder": self._encoder.encode_boolean_vector(vector_data)
        }
        # Return the encoder portion (for possible aggregation)
        return feature["vectorized_statistics"]["encoder"]

    def _detect_data_format(self, data: Dict[str, Any]) -> str:
        """
        Detect the data format to decide processing strategy.
        
        Args:
            data: The input data dictionary
            
        Returns:
            'direct' for supported format, 'unknown' for unsupported
        """
        if "entries" in data and isinstance(data["entries"], dict):
            return "direct"
        else:
            return "unknown"

    def _get_feature_data_type(self, feature_name: str, feature_data: Dict[str, Any], features_metadata: List[Dict[str, Any]] = None) -> str:
        """
        Determine the data type of a feature based on its statistics and metadata.
        
        Args:
            feature_name: Name of the feature
            feature_data: Statistics data for the feature
            features_metadata: Optional metadata about features
            
        Returns:
            The inferred data type
        """
        # Check if we have explicit metadata
        if features_metadata:
            for feature_meta in features_metadata:
                if feature_meta.get("name") == feature_name:
                    return feature_meta.get("dataType", "UNKNOWN")
        
        # Infer from statistics structure
        if "numOfTrue" in feature_data:
            return "BOOLEAN"
        elif "valueSet" in feature_data and "cardinalityPerItem" in feature_data:
            return "NOMINAL"
        elif "min" in feature_data and "max" in feature_data and "avg" in feature_data:
            return "NUMERIC"
        else:
            return "UNKNOWN"

    def _process_direct_format(self, data: Dict[str, Any], query: Optional[str] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process data in direct format (statistics directly under entries).
        
        Args:
            data: The input data dictionary
            query: Optional feature name filter
            
        Returns:
            Tuple of (enhanced_data, encoders_list, schema_list)
        """
        entries = data.get("entries", {})
        features_metadata = data.get("features", [])
        
        feature_encoders: List[Dict[str, Any]] = []
        schema_list: List[Dict[str, Any]] = []
        current_offset = 0
        
        processed_entries = {}
        
        for feature_name, feature_stats in entries.items():
            # Apply query filter if provided
            if query and feature_name != query:
                processed_entries[feature_name] = feature_stats
                continue
                
            # Determine data type
            data_type = self._get_feature_data_type(feature_name, feature_stats, features_metadata)
            
            # Skip unknown types with warning
            if data_type == "UNKNOWN":
                self._logger.warning(f"Unknown data type for feature '{feature_name}', skipping")
                processed_entries[feature_name] = feature_stats
                continue
            
            # Create encoder
            encoder_obj = self._create_encoder_for_feature(feature_name, data_type, feature_stats)
            feature_encoders.append(encoder_obj)
            
            # Update the feature with vectorized stats
            processed_entries[feature_name] = {
                **feature_stats,
                "vectorized_statistics": {
                    "vectorized": encoder_obj["data"],
                    "encoder": encoder_obj,
                    "dataType": data_type
                }
            }
            
            # Add schema info
            vectorizer = self._encoder.get_vectorizer(data_type)
            schema_list.append({
                "featureName": feature_name,
                "dataType": data_type,
                "offset": current_offset,
                "length": vectorizer.get_vector_length(),
                "fields": vectorizer.get_vector_description()
            })
            current_offset += vectorizer.get_vector_length()
        
        # Create enhanced data
        enhanced_data = {
            **data,
            "entries": processed_entries
        }
        
        return enhanced_data, feature_encoders, schema_list


    def enhance_dataset(
        self,
        data: Dict[str, Any],
        query: Optional[str] = None
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process dataset in direct format (entries as dictionary).
        Supports BOOLEAN, NUMERIC, and CATEGORICAL features.
        
        Args:
            data: The input dataset with "entries" as dictionary
            query: Optional feature name filter
            
        Returns:
            Tuple of (enhanced_data, encoders_list, schema_list):
                - enhanced_data: the updated dataset (with vectorized_statistics fields)
                - encoders_list: either multiple encoders (if query) OR one flattened encoder
                - schema_list: describes the offset/length for each feature in the flattened array
        """
        # Validate data format
        if not ("entries" in data and isinstance(data["entries"], dict)):
            self._logger.error("Invalid data format. Expected 'entries' as dictionary.")
            return data, [], []
        
        self._logger.info("Processing direct format data")
        enhanced_data, feature_encoders, schema_list = self._process_direct_format(data, query)

        # If user gave a query or no features found, return them as-is
        if query or not feature_encoders:
            return enhanced_data, feature_encoders, schema_list

        # Otherwise, flatten all the 'data' arrays of each encoder into one single encoder object
        flattened_values: List[Union[int, float]] = []
        for enc in feature_encoders:
            # enc is e.g. {"type": "int", "data": [numNotNull, numTrue]}
            flattened_values.extend(enc["data"])

        # Create one aggregated encoder
        aggregated_encoder = {
            "type": "mixed",  # Mixed type since we have int and float
            "data": flattened_values,
            "totalFeatures": len(feature_encoders),
            "supportedDataTypes": self._encoder.get_supported_data_types()
        }

        # Return a single item in encoders_list
        return enhanced_data, [aggregated_encoder], schema_list

    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types"""
        return self._encoder.get_supported_data_types()

    def get_vector_schema(self, data_type: str) -> Dict[str, Any]:
        """Get schema information for a data type"""
        return self._encoder.get_vector_schema(data_type)
