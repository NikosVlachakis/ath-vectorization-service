#!/usr/bin/env python3

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from encoder import Encoder, BooleanVectorizer, NumericVectorizer, CategoricalVectorizer
from vectorization_service import VectorizationService


class TestEnhancedVectorization(unittest.TestCase):
    """
    Comprehensive test suite for the enhanced vectorization system
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.encoder = Encoder()
        self.vectorizer = VectorizationService(self.encoder)
    
    def test_boolean_vectorizer(self):
        """Test boolean vectorizer functionality"""
        vectorizer = BooleanVectorizer()
        
        # Test normal boolean statistics
        stats = {"numOfNotNull": 100, "numOfTrue": 75}
        result = vectorizer.vectorize(stats)
        
        self.assertEqual(result, [100, 75])
        self.assertEqual(vectorizer.get_vector_length(), 2)
        self.assertEqual(vectorizer.get_vector_description(), ["numOfNotNull", "numOfTrue"])
    
    def test_numeric_vectorizer(self):
        """Test numeric vectorizer functionality"""
        vectorizer = NumericVectorizer()
        
        # Test normal numeric statistics
        stats = {
            "numOfNotNull": 10,
            "min": 1.5,
            "max": 98.7,
            "avg": 45.2,
            "q1": 25.0,
            "q2": 44.5,
            "q3": 65.8
        }
        result = vectorizer.vectorize(stats)
        
        expected = [10, 1.5, 98.7, 45.2, 25.0, 44.5, 65.8]
        self.assertEqual(result, expected)
        self.assertEqual(vectorizer.get_vector_length(), 7)
        self.assertEqual(len(vectorizer.get_vector_description()), 7)
        
        # Test empty numeric statistics
        empty_stats = {"numOfNotNull": 0}
        result = vectorizer.vectorize(empty_stats)
        expected = [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.assertEqual(result, expected)
    
    def test_categorical_vectorizer(self):
        """Test categorical vectorizer functionality"""
        vectorizer = CategoricalVectorizer()
        
        # Test normal categorical statistics
        stats = {
            "numOfNotNull": 14,
            "valueSet": ["2014", "2020", "2024", "2022"],
            "cardinalityPerItem": {"2014": 1, "2020": 1, "2024": 5, "2022": 7}
        }
        result = vectorizer.vectorize(stats)
        
        expected = [14, 4, 7]  # [numOfNotNull, numUniqueValues, topValueCount]
        self.assertEqual(result, expected)
        self.assertEqual(vectorizer.get_vector_length(), 3)
        self.assertEqual(vectorizer.get_vector_description(), ["numOfNotNull", "numUniqueValues", "topValueCount"])
        
        # Test empty categorical statistics
        empty_stats = {"numOfNotNull": 0}
        result = vectorizer.vectorize(empty_stats)
        expected = [0, 0, 0]
        self.assertEqual(result, expected)
    
    def test_encoder_feature_vector_creation(self):
        """Test encoder feature vector creation for different data types"""
        
        # Test boolean encoder
        bool_vector = [100, 75]
        bool_encoder = self.encoder.encode_feature_vector("BOOLEAN", bool_vector)
        
        self.assertEqual(bool_encoder["type"], "int")
        self.assertEqual(bool_encoder["data"], [100, 75])
        self.assertEqual(bool_encoder["dataType"], "BOOLEAN")
        self.assertEqual(bool_encoder["vectorLength"], 2)
        
        # Test numeric encoder
        num_vector = [10, 1.5, 98.7, 45.2, 25.0, 44.5, 65.8]
        num_encoder = self.encoder.encode_feature_vector("NUMERIC", num_vector)
        
        self.assertEqual(num_encoder["type"], "float")
        self.assertEqual(num_encoder["data"], num_vector)
        self.assertEqual(num_encoder["dataType"], "NUMERIC")
        self.assertEqual(num_encoder["vectorLength"], 7)
        
        # Test categorical encoder
        cat_vector = [14, 4, 7]
        cat_encoder = self.encoder.encode_feature_vector("NOMINAL", cat_vector)
        
        self.assertEqual(cat_encoder["type"], "int")
        self.assertEqual(cat_encoder["data"], cat_vector)
        self.assertEqual(cat_encoder["dataType"], "NOMINAL")
        self.assertEqual(cat_encoder["vectorLength"], 3)
    
    def test_vectorize_feature_statistics(self):
        """Test the main vectorization method for different feature types"""
        
        # Test boolean
        bool_stats = {"numOfNotNull": 100, "numOfTrue": 75}
        bool_result = self.encoder.vectorize_feature_statistics("BOOLEAN", bool_stats)
        self.assertEqual(bool_result, [100, 75])
        
        # Test numeric
        num_stats = {
            "numOfNotNull": 10,
            "min": 1.5,
            "max": 98.7,
            "avg": 45.2,
            "q1": 25.0,
            "q2": 44.5,
            "q3": 65.8
        }
        num_result = self.encoder.vectorize_feature_statistics("NUMERIC", num_stats)
        expected = [10, 1.5, 98.7, 45.2, 25.0, 44.5, 65.8]
        self.assertEqual(num_result, expected)
        
        # Test categorical
        cat_stats = {
            "numOfNotNull": 14,
            "valueSet": ["2014", "2020", "2024"],
            "cardinalityPerItem": {"2014": 1, "2020": 1, "2024": 12}
        }
        cat_result = self.encoder.vectorize_feature_statistics("NOMINAL", cat_stats)
        expected = [14, 3, 12]
        self.assertEqual(cat_result, expected)
    
    def test_legacy_format_processing(self):
        """Test processing of legacy format data (backward compatibility)"""
        
        # Create legacy format data
        legacy_data = {
            "entries": [
                {
                    "featureSet": {
                        "features": [
                            {
                                "name": "hasDriverLicense",
                                "dataType": "BOOLEAN",
                                "statistics": {
                                    "numOfNotNull": 100,
                                    "numOfTrue": 75
                                }
                            },
                            {
                                "name": "age",
                                "dataType": "NUMERIC",
                                "statistics": {
                                    "numOfNotNull": 10,
                                    "min": 18.0,
                                    "max": 65.0,
                                    "avg": 35.5,
                                    "q1": 25.0,
                                    "q2": 35.0,
                                    "q3": 45.0
                                }
                            },
                            {
                                "name": "gender",
                                "dataType": "NOMINAL",
                                "statistics": {
                                    "numOfNotNull": 14,
                                    "valueSet": ["male", "female", "other"],
                                    "cardinalityPerItem": {"male": 7, "female": 5, "other": 2}
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(legacy_data)
        
        # Check that we have encoders for all features
        self.assertEqual(len(encoders_list), 1)  # Flattened into single encoder
        self.assertEqual(len(schema_list), 3)    # 3 features
        
        # Check schema structure
        self.assertEqual(schema_list[0]["featureName"], "hasDriverLicense")
        self.assertEqual(schema_list[0]["dataType"], "BOOLEAN")
        self.assertEqual(schema_list[0]["length"], 2)
        
        self.assertEqual(schema_list[1]["featureName"], "age")
        self.assertEqual(schema_list[1]["dataType"], "NUMERIC")
        self.assertEqual(schema_list[1]["length"], 7)
        
        self.assertEqual(schema_list[2]["featureName"], "gender")
        self.assertEqual(schema_list[2]["dataType"], "NOMINAL")
        self.assertEqual(schema_list[2]["length"], 3)
        
        # Check aggregated encoder
        aggregated_encoder = encoders_list[0]
        self.assertEqual(aggregated_encoder["type"], "mixed")
        self.assertEqual(aggregated_encoder["totalFeatures"], 3)
        
        # Check flattened data (boolean + numeric + categorical)
        expected_data = [100, 75] + [10, 18.0, 65.0, 35.5, 25.0, 35.0, 45.0] + [14, 3, 7]
        self.assertEqual(aggregated_encoder["data"], expected_data)
    
    def test_direct_format_processing(self):
        """Test processing of direct format data"""
        
        # Create direct format data (like metadata-test.json)
        direct_data = {
            "features": [
                {"name": "hasDriverLicense", "dataType": "BOOLEAN"},
                {"name": "age", "dataType": "NUMERIC"},
                {"name": "gender", "dataType": "NOMINAL"}
            ],
            "entries": {
                "hasDriverLicense": {
                    "numOfNotNull": 100,
                    "numOfTrue": 75
                },
                "age": {
                    "numOfNotNull": 10,
                    "min": 18.0,
                    "max": 65.0,
                    "avg": 35.5,
                    "q1": 25.0,
                    "q2": 35.0,
                    "q3": 45.0
                },
                "gender": {
                    "numOfNotNull": 14,
                    "valueSet": ["male", "female", "other"],
                    "cardinalityPerItem": {"male": 7, "female": 5, "other": 2}
                }
            }
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(direct_data)
        
        # Check that we have encoders for all features
        self.assertEqual(len(encoders_list), 1)  # Flattened into single encoder
        self.assertEqual(len(schema_list), 3)    # 3 features
        
        # Check that features have vectorized statistics
        entries = enhanced_data["entries"]
        self.assertIn("vectorized_statistics", entries["hasDriverLicense"])
        self.assertIn("vectorized_statistics", entries["age"])
        self.assertIn("vectorized_statistics", entries["gender"])
        
        # Check flattened data
        aggregated_encoder = encoders_list[0]
        expected_data = [100, 75] + [10, 18.0, 65.0, 35.5, 25.0, 35.0, 45.0] + [14, 3, 7]
        self.assertEqual(aggregated_encoder["data"], expected_data)
    
    def test_query_filtering(self):
        """Test that query filtering works correctly"""
        
        direct_data = {
            "features": [
                {"name": "hasDriverLicense", "dataType": "BOOLEAN"},
                {"name": "age", "dataType": "NUMERIC"}
            ],
            "entries": {
                "hasDriverLicense": {
                    "numOfNotNull": 100,
                    "numOfTrue": 75
                },
                "age": {
                    "numOfNotNull": 10,
                    "min": 18.0,
                    "max": 65.0,
                    "avg": 35.5,
                    "q1": 25.0,
                    "q2": 35.0,
                    "q3": 45.0
                }
            }
        }
        
        # Query for specific feature
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(direct_data, query="hasDriverLicense")
        
        # Should only have one encoder and schema
        self.assertEqual(len(encoders_list), 1)
        self.assertEqual(len(schema_list), 1)
        
        # Should be boolean encoder
        self.assertEqual(encoders_list[0]["dataType"], "BOOLEAN")
        self.assertEqual(encoders_list[0]["data"], [100, 75])
        
        # Schema should be for boolean feature
        self.assertEqual(schema_list[0]["featureName"], "hasDriverLicense")
        self.assertEqual(schema_list[0]["dataType"], "BOOLEAN")
    
    def test_data_type_inference(self):
        """Test automatic data type inference"""
        
        # Test data without explicit feature metadata
        data_no_metadata = {
            "entries": {
                "boolean_feature": {
                    "numOfNotNull": 100,
                    "numOfTrue": 75
                },
                "numeric_feature": {
                    "numOfNotNull": 10,
                    "min": 18.0,
                    "max": 65.0,
                    "avg": 35.5,
                    "q1": 25.0,
                    "q2": 35.0,
                    "q3": 45.0
                },
                "categorical_feature": {
                    "numOfNotNull": 14,
                    "valueSet": ["A", "B", "C"],
                    "cardinalityPerItem": {"A": 7, "B": 5, "C": 2}
                },
                "datetime_feature": {
                    "numOfNotNull": 14
                }
            }
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(data_no_metadata)
        
        # Should have 3 encoders (boolean, numeric, categorical) - datetime should be skipped
        self.assertEqual(len(encoders_list), 1)  # Flattened
        self.assertEqual(len(schema_list), 3)
        
        # Check inferred data types
        schema_by_name = {s["featureName"]: s for s in schema_list}
        self.assertEqual(schema_by_name["boolean_feature"]["dataType"], "BOOLEAN")
        self.assertEqual(schema_by_name["numeric_feature"]["dataType"], "NUMERIC")
        self.assertEqual(schema_by_name["categorical_feature"]["dataType"], "NOMINAL")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        
        # Test empty data
        empty_data = {"entries": {}}
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(empty_data)
        
        self.assertEqual(len(encoders_list), 0)
        self.assertEqual(len(schema_list), 0)
        
        # Test unknown format
        unknown_data = {"unknown": "format"}
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(unknown_data)
        
        self.assertEqual(len(encoders_list), 0)
        self.assertEqual(len(schema_list), 0)
        
        # Test feature with missing statistics
        incomplete_data = {
            "entries": {
                "incomplete_feature": {
                    "numOfNotNull": 10
                    # Missing other required statistics
                }
            }
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(incomplete_data)
        
        # Should still process but with inferred datetime type (skipped)
        self.assertEqual(len(encoders_list), 0)
        self.assertEqual(len(schema_list), 0)
    
    def test_backward_compatibility(self):
        """Test that existing boolean-only functionality still works"""
        
        # Test the old boolean-only format
        old_boolean_data = {
            "entries": [
                {
                    "featureSet": {
                        "features": [
                            {
                                "name": "hasDriverLicense",
                                "dataType": "BOOLEAN",
                                "statistics": {
                                    "numOfNotNull": 100,
                                    "numOfTrue": 75
                                }
                            },
                            {
                                "name": "isMarried",
                                "dataType": "BOOLEAN",
                                "statistics": {
                                    "numOfNotNull": 95,
                                    "numOfTrue": 60
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(old_boolean_data)
        
        # Should work exactly like before
        self.assertEqual(len(encoders_list), 1)  # Flattened
        self.assertEqual(len(schema_list), 2)
        
        # Check aggregated encoder data
        aggregated_encoder = encoders_list[0]
        expected_data = [100, 75, 95, 60]
        self.assertEqual(aggregated_encoder["data"], expected_data)
        
        # Check schema
        self.assertEqual(schema_list[0]["featureName"], "hasDriverLicense")
        self.assertEqual(schema_list[0]["length"], 2)
        self.assertEqual(schema_list[1]["featureName"], "isMarried")
        self.assertEqual(schema_list[1]["length"], 2)
    
    def test_mixed_types_aggregation(self):
        """Test aggregation of mixed data types"""
        
        mixed_data = {
            "features": [
                {"name": "boolFeature", "dataType": "BOOLEAN"},
                {"name": "numFeature", "dataType": "NUMERIC"},
                {"name": "catFeature", "dataType": "NOMINAL"}
            ],
            "entries": {
                "boolFeature": {
                    "numOfNotNull": 100,
                    "numOfTrue": 75
                },
                "numFeature": {
                    "numOfNotNull": 10,
                    "min": 1.0,
                    "max": 10.0,
                    "avg": 5.5,
                    "q1": 3.0,
                    "q2": 5.0,
                    "q3": 8.0
                },
                "catFeature": {
                    "numOfNotNull": 5,
                    "valueSet": ["A", "B"],
                    "cardinalityPerItem": {"A": 3, "B": 2}
                }
            }
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(mixed_data)
        
        # Check aggregated result
        aggregated_encoder = encoders_list[0]
        expected_data = [100, 75] + [10, 1.0, 10.0, 5.5, 3.0, 5.0, 8.0] + [5, 2, 3]
        self.assertEqual(aggregated_encoder["data"], expected_data)
        
        # Check schema offsets
        self.assertEqual(schema_list[0]["offset"], 0)  # Boolean starts at 0
        self.assertEqual(schema_list[1]["offset"], 2)  # Numeric starts at 2
        self.assertEqual(schema_list[2]["offset"], 9)  # Categorical starts at 9
    
    def test_get_supported_data_types(self):
        """Test getting supported data types"""
        
        supported_types = self.vectorizer.get_supported_data_types()
        
        self.assertIn("BOOLEAN", supported_types)
        self.assertIn("NUMERIC", supported_types)
        self.assertIn("NOMINAL", supported_types)
        self.assertIn("ORDINAL", supported_types)
    
    def test_get_vector_schema(self):
        """Test getting vector schema for data types"""
        
        # Test boolean schema
        bool_schema = self.vectorizer.get_vector_schema("BOOLEAN")
        self.assertEqual(bool_schema["dataType"], "BOOLEAN")
        self.assertEqual(bool_schema["vectorLength"], 2)
        self.assertEqual(bool_schema["fields"], ["numOfNotNull", "numOfTrue"])
        
        # Test numeric schema
        num_schema = self.vectorizer.get_vector_schema("NUMERIC")
        self.assertEqual(num_schema["dataType"], "NUMERIC")
        self.assertEqual(num_schema["vectorLength"], 7)
        self.assertEqual(len(num_schema["fields"]), 7)
        
        # Test categorical schema
        cat_schema = self.vectorizer.get_vector_schema("NOMINAL")
        self.assertEqual(cat_schema["dataType"], "NOMINAL")
        self.assertEqual(cat_schema["vectorLength"], 3)
        self.assertEqual(cat_schema["fields"], ["numOfNotNull", "numUniqueValues", "topValueCount"])


if __name__ == '__main__':
    unittest.main() 