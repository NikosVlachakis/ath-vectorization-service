from typing import List, Any, Dict, Union
from abc import ABC, abstractmethod
import json

class BaseVectorizer(ABC):
    """Abstract base class for different data type vectorizers"""
    
    @abstractmethod
    def vectorize(self, statistics: Dict[str, Any]) -> List[Union[int, float]]:
        """Convert statistics to a vector representation"""
        pass
    
    @abstractmethod
    def get_vector_length(self) -> int:
        """Return the expected length of the vector"""
        pass
    
    @abstractmethod
    def get_vector_description(self) -> List[str]:
        """Return description of what each vector element represents"""
        pass

class BooleanVectorizer(BaseVectorizer):
    """Vectorizer for boolean features"""
    
    def vectorize(self, statistics: Dict[str, Any]) -> List[int]:
        """Convert boolean statistics to [numOfNotNull, numOfTrue] format"""
        num_not_null = statistics.get("numOfNotNull", 0)
        num_true = statistics.get("numOfTrue", 0)
        return [num_not_null, num_true]
    
    def get_vector_length(self) -> int:
        return 2
    
    def get_vector_description(self) -> List[str]:
        return ["numOfNotNull", "numOfTrue"]

class NumericVectorizer(BaseVectorizer):
    """Vectorizer for numeric features"""
    
    def vectorize(self, statistics: Dict[str, Any]) -> List[Union[int, float]]:
        """Convert numeric statistics to [numOfNotNull, min, max, avg, q1, q2, q3] format"""
        num_not_null = statistics.get("numOfNotNull", 0)
        
        # If no data, return zeros for all numeric stats
        if num_not_null == 0:
            return [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        min_val = statistics.get("min", 0.0)
        max_val = statistics.get("max", 0.0)
        avg_val = statistics.get("avg", 0.0)
        q1_val = statistics.get("q1", 0.0)
        q2_val = statistics.get("q2", 0.0)
        q3_val = statistics.get("q3", 0.0)
        
        return [num_not_null, min_val, max_val, avg_val, q1_val, q2_val, q3_val]
    
    def get_vector_length(self) -> int:
        return 7
    
    def get_vector_description(self) -> List[str]:
        return ["numOfNotNull", "min", "max", "avg", "q1", "q2", "q3"]

class CategoricalVectorizer(BaseVectorizer):
    """Vectorizer for categorical features"""
    
    def vectorize(self, statistics: Dict[str, Any]) -> List[int]:
        """Convert categorical statistics to [numOfNotNull, numUniqueValues, topValueCount] format"""
        num_not_null = statistics.get("numOfNotNull", 0)
        
        # If no data, return zeros
        if num_not_null == 0:
            return [0, 0, 0]
        
        value_set = statistics.get("valueSet", [])
        cardinality_per_item = statistics.get("cardinalityPerItem", [])
        
        num_unique_values = len(value_set)
        
        # Handle both list and dictionary formats for cardinalityPerItem
        if isinstance(cardinality_per_item, list):
            # cardinalityPerItem is a list: [400, 200, 200, 100, 100]
            top_value_count = max(cardinality_per_item) if cardinality_per_item else 0
        elif isinstance(cardinality_per_item, dict):
            # cardinalityPerItem is a dict: {"Engineering": 400, "Marketing": 200, ...}
            top_value_count = max(cardinality_per_item.values()) if cardinality_per_item else 0
        else:
            # Fallback for unknown format
            top_value_count = 0
        
        return [num_not_null, num_unique_values, top_value_count]
    
    def get_vector_length(self) -> int:
        return 3
    
    def get_vector_description(self) -> List[str]:
        return ["numOfNotNull", "numUniqueValues", "topValueCount"]

class Encoder:
    """
    Enhanced encoder that supports boolean, numeric, and categorical features
    """
    
    def __init__(self):
        self.vectorizers = {
            "BOOLEAN": BooleanVectorizer(),
            "NUMERIC": NumericVectorizer(),
            "NOMINAL": CategoricalVectorizer(),
            "ORDINAL": CategoricalVectorizer(),  # Treat ordinal as categorical for now
        }
    
    def encode_feature_vector(self, data_type: str, vector: List[Union[int, float]]) -> Dict[str, Any]:
        """
        Create an encoder object for a feature vector
        
        Args:
            data_type: The type of the feature (BOOLEAN, NUMERIC, NOMINAL, ORDINAL)
            vector: The vectorized data
            
        Returns:
            Encoder object with type and data
        """
        # Determine the appropriate data type for the encoder
        if data_type.upper() in ["BOOLEAN"]:
            encoder_type = "int"
        elif data_type.upper() in ["NUMERIC"]:
            encoder_type = "float"
        elif data_type.upper() in ["NOMINAL", "ORDINAL"]:
            encoder_type = "int"
        else:
            encoder_type = "int"  # Default fallback
        
        return {
            "type": encoder_type,
            "data": vector,
            "dataType": data_type.upper(),
            "vectorLength": len(vector)
        }
    
    def encode_boolean_vector(self, vector: List[int]) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility
        """
        return self.encode_feature_vector("BOOLEAN", vector)
    
    def get_vectorizer(self, data_type: str) -> BaseVectorizer:
        """
        Get the appropriate vectorizer for a data type
        
        Args:
            data_type: The type of the feature
            
        Returns:
            The corresponding vectorizer
        """
        data_type_upper = data_type.upper()
        if data_type_upper in self.vectorizers:
            return self.vectorizers[data_type_upper]
        else:
            # Default to categorical for unknown types
            return self.vectorizers["NOMINAL"]
    
    def vectorize_feature_statistics(self, data_type: str, statistics: Dict[str, Any]) -> List[Union[int, float]]:
        """
        Convert feature statistics to vector format
        
        Args:
            data_type: The type of the feature
            statistics: The statistics dictionary
            
        Returns:
            Vectorized representation of the statistics
        """
        vectorizer = self.get_vectorizer(data_type)
        return vectorizer.vectorize(statistics)
    
    def get_supported_data_types(self) -> List[str]:
        """Return list of supported data types"""
        return list(self.vectorizers.keys())
    
    def get_vector_schema(self, data_type: str) -> Dict[str, Any]:
        """
        Get schema information for a data type
        
        Args:
            data_type: The type of the feature
            
        Returns:
            Schema information including length and field descriptions
        """
        vectorizer = self.get_vectorizer(data_type)
        return {
            "dataType": data_type.upper(),
            "vectorLength": vectorizer.get_vector_length(),
            "fields": vectorizer.get_vector_description()
        }
