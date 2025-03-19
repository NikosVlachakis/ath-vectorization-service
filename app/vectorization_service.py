from typing import Any, Dict, Optional, List
from encoder import Encoder

class VectorizationService:
    """
    A service class that performs vectorization of BOOLEAN features
    and uses an Encoder to embed the results into the dataset.
    """

    def __init__(self, encoder: Encoder):
        self._encoder = encoder

    def _vectorize_boolean_stats(self, statistics: Dict[str, Any]) -> List[int]:
        """
        Internal method to convert boolean statistics into a numeric vector:
        [numOfNotNull, numOfTrue].
        """
        num_not_null = statistics.get("numOfNotNull", 0)
        num_true = statistics.get("numOfTrue", 0)
        return [num_not_null, num_true]

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

    def enhance_dataset(
        self,
        data: Dict[str, Any],
        query: Optional[str] = None
    ) -> (Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]):
        """
        Enhance the input dataset by adding 'vectorized_statistics' to each BOOLEAN feature.
        If 'query' is provided, only features with name == query are processed.

        Returns:
          (enhanced_data, encoders_list, schema_list):
            - enhanced_data: the updated dataset (with vectorized_statistics fields)
            - encoders_list: either multiple encoders (if query) OR one flattened encoder
            - schema_list: describes the offset/length for each boolean feature in the flattened array
        """
        entries = data.get("entries", [])
        feature_encoders: List[Dict[str, Any]] = []

        # We track schema info so we can decode aggregator output later
        schema_list: List[Dict[str, Any]] = []
        current_offset = 0

        for entry in entries:
            features = entry.get("featureSet", {}).get("features", [])
            for feature in features:
                # If query is set, skip features that don't match
                if query and feature.get("name") != query:
                    continue

                if feature.get("dataType", "").upper() == "BOOLEAN":
                    encoder_obj = self._create_encoder_for_boolean_feature(feature)
                    feature_encoders.append(encoder_obj)

                    # We assume length=2 for each boolean vector ([numNotNull, numTrue])
                    schema_list.append({
                        "featureName": feature.get("name"),
                        "offset": current_offset,
                        "length": 2
                    })
                    current_offset += 2

        # If user gave a query or no boolean features found, return them as-is
        if query or not feature_encoders:
            return data, feature_encoders, schema_list

        # Otherwise, flatten all the 'data' arrays of each encoder into one single encoder object
        flattened_values: List[int] = []
        for enc in feature_encoders:
            # enc is e.g. {"type": "int", "data": [numNotNull, numTrue]}
            flattened_values.extend(enc["data"])

        # Create one aggregated encoder
        aggregated_encoder = {
            "type": "int",
            "data": flattened_values
        }

        # Return a single item in encoders_list
        return data, [aggregated_encoder], schema_list
