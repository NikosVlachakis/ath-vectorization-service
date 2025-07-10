#!/usr/bin/env python3

"""
Demo script showing the enhanced vectorization system with support for 
boolean, numeric, and categorical features.
"""

import json
import sys
import os
from typing import Dict, Any, List

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from encoder import Encoder
from vectorization_service import VectorizationService


def main():
    """Main demonstration function"""
    
    print("🚀 Enhanced Vectorization System Demo")
    print("=" * 50)
    
    # Initialize system
    encoder = Encoder()
    vectorizer = VectorizationService(encoder)
    
    print("📋 Supported Data Types:")
    for data_type in vectorizer.get_supported_data_types():
        schema = vectorizer.get_vector_schema(data_type)
        print(f"  - {data_type}: {schema['vectorLength']} fields -> {schema['fields']}")
    
    # Create sample data with all types
    sample_data = {
        "features": [
            {"name": "patient_gender", "dataType": "NOMINAL"},
            {"name": "patient_age", "dataType": "NUMERIC"},
            {"name": "has_diabetes", "dataType": "BOOLEAN"}
        ],
        "entries": {
            "patient_gender": {
                "numOfNotNull": 1000,
                "valueSet": ["male", "female", "other"],
                "cardinalityPerItem": {"male": 520, "female": 460, "other": 20}
            },
            "patient_age": {
                "numOfNotNull": 950,
                "min": 18.5,
                "max": 89.2,
                "avg": 45.7,
                "q1": 32.0,
                "q2": 45.5,
                "q3": 58.9
            },
            "has_diabetes": {
                "numOfNotNull": 1000,
                "numOfTrue": 150
            }
        }
    }
    
    print("\n📊 Processing Sample Data...")
    
    # Process the data
    enhanced_data, encoders_list, schema_list = vectorizer.enhance_dataset(sample_data)
    
    print(f"✅ Successfully processed {len(schema_list)} features")
    
    # Show schema details
    print(f"\n📋 Schema Details:")
    for schema in schema_list:
        print(f"  - {schema['featureName']} ({schema['dataType']}): "
              f"offset={schema['offset']}, length={schema['length']}")
    
    # Show encoded data
    aggregated_encoder = encoders_list[0]
    print(f"\n🔢 Encoded Data Array:")
    print(f"  {aggregated_encoder['data']}")
    
    print(f"\n🎯 Feature Breakdown:")
    print(f"  Gender (NOMINAL): {aggregated_encoder['data'][0:3]}")
    print(f"  Age (NUMERIC): {aggregated_encoder['data'][3:10]}")
    print(f"  Diabetes (BOOLEAN): {aggregated_encoder['data'][10:12]}")
    
    print(f"\n✅ Demo Complete!")
    

if __name__ == "__main__":
    main() 