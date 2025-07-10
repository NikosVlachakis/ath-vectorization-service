#!/usr/bin/env python3

import unittest
import json
import sys
import os

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from encoder import Encoder
from vectorization_service import VectorizationService


class TestMetadataIntegration(unittest.TestCase):
    """
    Integration test using metadata-test.json format
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.encoder = Encoder()
        self.vectorizer = VectorizationService(self.encoder)
        
        # Sample data in the metadata-test.json format
        self.sample_metadata = {
            "features": [
                {
                    "name": "patient_demographics_gender",
                    "description": "Gender of the patient",
                    "dataType": "NOMINAL",
                    "valueSet": {
                        "concept": [
                            {"code": "male", "display": "Male"},
                            {"code": "female", "display": "Female"},
                            {"code": "other", "display": "Other"}
                        ]
                    }
                },
                {
                    "name": "patient_demographics_age",
                    "description": "Age of the patient at reference point",
                    "dataType": "NUMERIC"
                },
                {
                    "name": "med_everUsedBeforeHospitalAdmission_diuretics_any",
                    "description": "Ever used diuretics before hospital admission",
                    "dataType": "BOOLEAN"
                }
            ],
            "entries": {
                "patient_demographics_gender": {
                    "numOfNotNull": 14,
                    "valueSet": ["male", "female", "other", "unknown"],
                    "cardinalityPerItem": {
                        "male": 7,
                        "female": 5,
                        "other": 1,
                        "unknown": 1
                    }
                },
                "patient_demographics_age": {
                    "numOfNotNull": 12,
                    "min": 18.5,
                    "max": 89.2,
                    "avg": 65.7,
                    "q1": 45.8,
                    "q2": 67.1,
                    "q3": 78.9,
                    "histogram": [
                        {"bin": 18.5, "count": 1},
                        {"bin": 25.0, "count": 2},
                        {"bin": 67.1, "count": 4},
                        {"bin": 89.2, "count": 5}
                    ]
                },
                "med_everUsedBeforeHospitalAdmission_diuretics_any": {
                    "numOfNotNull": 14,
                    "numOfTrue": 11
                },
                "encounters_admissionDate": {
                    "numOfNotNull": 14
                },
                "lab_results_unknown_feature": {
                    "numOfNotNull": 5,
                    "customField": "someValue"
                }
            }
        }
    
    def test_metadata_format_processing(self):
        """Test processing of metadata-test.json format"""
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(self.sample_metadata)
        
        # Should have 3 features processed (gender, age, diuretics), 
        # datetime (admissionDate) and unknown feature should be skipped
        self.assertEqual(len(encoders_list), 1)  # Flattened into single encoder
        self.assertEqual(len(schema_list), 3)
        
        # Check that the enhanced data includes vectorized statistics
        entries = enhanced_data["entries"]
        self.assertIn("vectorized_statistics", entries["patient_demographics_gender"])
        self.assertIn("vectorized_statistics", entries["patient_demographics_age"])
        self.assertIn("vectorized_statistics", entries["med_everUsedBeforeHospitalAdmission_diuretics_any"])
        
        # Check that datetime feature is preserved but not vectorized
        self.assertNotIn("vectorized_statistics", entries["encounters_admissionDate"])
        
        # Check schema information
        schema_by_name = {s["featureName"]: s for s in schema_list}
        
        # Check gender (categorical)
        gender_schema = schema_by_name["patient_demographics_gender"]
        self.assertEqual(gender_schema["dataType"], "NOMINAL")
        self.assertEqual(gender_schema["length"], 3)
        self.assertEqual(gender_schema["fields"], ["numOfNotNull", "numUniqueValues", "topValueCount"])
        
        # Check age (numeric)
        age_schema = schema_by_name["patient_demographics_age"]
        self.assertEqual(age_schema["dataType"], "NUMERIC")
        self.assertEqual(age_schema["length"], 7)
        self.assertEqual(len(age_schema["fields"]), 7)
        
        # Check diuretics (boolean)
        diuretics_schema = schema_by_name["med_everUsedBeforeHospitalAdmission_diuretics_any"]
        self.assertEqual(diuretics_schema["dataType"], "BOOLEAN")
        self.assertEqual(diuretics_schema["length"], 2)
        self.assertEqual(diuretics_schema["fields"], ["numOfNotNull", "numOfTrue"])
        
        # Check offsets are correct
        self.assertEqual(gender_schema["offset"], 0)
        self.assertEqual(age_schema["offset"], 3)     # After gender (3 values)
        self.assertEqual(diuretics_schema["offset"], 10)  # After age (7 values)
        
        # Check flattened encoder data
        aggregated_encoder = encoders_list[0]
        expected_data = (
            [14, 4, 7] +                              # Gender: [numOfNotNull, numUniqueValues, topValueCount]
            [12, 18.5, 89.2, 65.7, 45.8, 67.1, 78.9] +  # Age: [numOfNotNull, min, max, avg, q1, q2, q3]
            [14, 11]                                   # Diuretics: [numOfNotNull, numOfTrue]
        )
        self.assertEqual(aggregated_encoder["data"], expected_data)
        self.assertEqual(aggregated_encoder["totalFeatures"], 3)
    
    def test_query_filtering_metadata_format(self):
        """Test query filtering with metadata format"""
        
        # Query for specific feature
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(
            self.sample_metadata, 
            query="patient_demographics_age"
        )
        
        # Should only have age feature
        self.assertEqual(len(encoders_list), 1)
        self.assertEqual(len(schema_list), 1)
        
        # Should be numeric encoder
        self.assertEqual(encoders_list[0]["dataType"], "NUMERIC")
        self.assertEqual(encoders_list[0]["data"], [12, 18.5, 89.2, 65.7, 45.8, 67.1, 78.9])
        
        # Schema should be for age feature
        self.assertEqual(schema_list[0]["featureName"], "patient_demographics_age")
        self.assertEqual(schema_list[0]["dataType"], "NUMERIC")
        self.assertEqual(schema_list[0]["offset"], 0)  # Single feature starts at offset 0
    
    def test_data_type_inference_metadata_format(self):
        """Test data type inference without explicit metadata"""
        
        # Remove features metadata to test inference
        data_without_metadata = {
            "entries": self.sample_metadata["entries"]
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(data_without_metadata)
        
        # Should still properly infer data types
        self.assertEqual(len(schema_list), 3)  # Same 3 features should be processed
        
        schema_by_name = {s["featureName"]: s for s in schema_list}
        
        # Check inferred data types
        self.assertEqual(schema_by_name["patient_demographics_gender"]["dataType"], "NOMINAL")
        self.assertEqual(schema_by_name["patient_demographics_age"]["dataType"], "NUMERIC")
        self.assertEqual(schema_by_name["med_everUsedBeforeHospitalAdmission_diuretics_any"]["dataType"], "BOOLEAN")
    
    def test_aggregation_pipeline_simulation(self):
        """Test simulated aggregation pipeline with multiple parties"""
        
        # Simulate 3 parties with different data
        party1_data = {
            "features": self.sample_metadata["features"],
            "entries": {
                "patient_demographics_gender": {
                    "numOfNotNull": 100,
                    "valueSet": ["male", "female", "other"],
                    "cardinalityPerItem": {"male": 60, "female": 35, "other": 5}
                },
                "patient_demographics_age": {
                    "numOfNotNull": 95,
                    "min": 18.0,
                    "max": 85.0,
                    "avg": 55.2,
                    "q1": 40.0,
                    "q2": 55.0,
                    "q3": 70.0
                },
                "med_everUsedBeforeHospitalAdmission_diuretics_any": {
                    "numOfNotNull": 100,
                    "numOfTrue": 75
                }
            }
        }
        
        party2_data = {
            "features": self.sample_metadata["features"],
            "entries": {
                "patient_demographics_gender": {
                    "numOfNotNull": 80,
                    "valueSet": ["male", "female"],
                    "cardinalityPerItem": {"male": 45, "female": 35}
                },
                "patient_demographics_age": {
                    "numOfNotNull": 78,
                    "min": 25.0,
                    "max": 90.0,
                    "avg": 62.1,
                    "q1": 45.0,
                    "q2": 62.0,
                    "q3": 78.0
                },
                "med_everUsedBeforeHospitalAdmission_diuretics_any": {
                    "numOfNotNull": 80,
                    "numOfTrue": 55
                }
            }
        }
        
        party3_data = {
            "features": self.sample_metadata["features"],
            "entries": {
                "patient_demographics_gender": {
                    "numOfNotNull": 60,
                    "valueSet": ["male", "female", "other", "unknown"],
                    "cardinalityPerItem": {"male": 25, "female": 30, "other": 3, "unknown": 2}
                },
                "patient_demographics_age": {
                    "numOfNotNull": 55,
                    "min": 22.0,
                    "max": 88.0,
                    "avg": 58.7,
                    "q1": 35.0,
                    "q2": 58.0,
                    "q3": 75.0
                },
                "med_everUsedBeforeHospitalAdmission_diuretics_any": {
                    "numOfNotNull": 60,
                    "numOfTrue": 40
                }
            }
        }
        
        # Process each party's data
        party1_enhanced, party1_encoders, party1_schema = self.vectorizer.enhance_dataset(party1_data)
        party2_enhanced, party2_encoders, party2_schema = self.vectorizer.enhance_dataset(party2_data)
        party3_enhanced, party3_encoders, party3_schema = self.vectorizer.enhance_dataset(party3_data)
        
        # Simulate aggregation (sum all party data)
        party1_array = party1_encoders[0]["data"]
        party2_array = party2_encoders[0]["data"]
        party3_array = party3_encoders[0]["data"]
        
        # Aggregate by summing
        aggregated_array = [
            party1_array[i] + party2_array[i] + party3_array[i] 
            for i in range(len(party1_array))
        ]
        
        # Expected aggregated results
        expected_aggregated = [
            # Gender: [numOfNotNull, numUniqueValues, topValueCount]
            240, 9, 135,  # 100+80+60, 3+2+4, 60+45+30 (max values)
            # Age: [numOfNotNull, min, max, avg, q1, q2, q3]
            228, 65.0, 263.0, 176.0, 120.0, 175.0, 223.0,  # Sums of all numeric stats
            # Diuretics: [numOfNotNull, numOfTrue]
            240, 170  # 100+80+60, 75+55+40
        ]
        
        self.assertEqual(aggregated_array, expected_aggregated)
        
        # Check that all parties have the same schema
        self.assertEqual(party1_schema, party2_schema)
        self.assertEqual(party2_schema, party3_schema)
        
        # Verify schema consistency
        self.assertEqual(len(party1_schema), 3)
        self.assertEqual(party1_schema[0]["featureName"], "patient_demographics_gender")
        self.assertEqual(party1_schema[1]["featureName"], "patient_demographics_age")
        self.assertEqual(party1_schema[2]["featureName"], "med_everUsedBeforeHospitalAdmission_diuretics_any")
    
    def test_empty_and_edge_cases_metadata_format(self):
        """Test edge cases with metadata format"""
        
        # Test with empty entries
        empty_data = {
            "features": [],
            "entries": {}
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(empty_data)
        
        self.assertEqual(len(encoders_list), 0)
        self.assertEqual(len(schema_list), 0)
        
        # Test with features that have no data
        no_data_features = {
            "features": [
                {"name": "empty_numeric", "dataType": "NUMERIC"},
                {"name": "empty_boolean", "dataType": "BOOLEAN"}
            ],
            "entries": {
                "empty_numeric": {
                    "numOfNotNull": 0
                },
                "empty_boolean": {
                    "numOfNotNull": 0,
                    "numOfTrue": 0
                }
            }
        }
        
        enhanced_data, encoders_list, schema_list = self.vectorizer.enhance_dataset(no_data_features)
        
        # Should still process features even with zero data
        self.assertEqual(len(encoders_list), 1)
        self.assertEqual(len(schema_list), 2)
        
        # Check that empty numeric feature gets zero vector
        aggregated_encoder = encoders_list[0]
        expected_data = [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] + [0, 0]  # numeric zeros + boolean zeros
        self.assertEqual(aggregated_encoder["data"], expected_data)


if __name__ == '__main__':
    unittest.main() 