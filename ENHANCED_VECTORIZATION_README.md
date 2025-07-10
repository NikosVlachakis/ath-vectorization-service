# Enhanced Vectorization System

The Athina vectorization system has been enhanced to support **boolean**, **numeric**, and **categorical** features while maintaining full backward compatibility with existing boolean-only functionality.

## 🚀 Features

### ✅ Supported Data Types

| Data Type | Vector Length | Fields | Description |
|-----------|---------------|--------|-------------|
| **BOOLEAN** | 2 | `[numOfNotNull, numOfTrue]` | Boolean statistics for survey-like data |
| **NUMERIC** | 7 | `[numOfNotNull, min, max, avg, q1, q2, q3]` | Complete statistical summary |
| **CATEGORICAL** | 3 | `[numOfNotNull, numUniqueValues, topValueCount]` | Category distribution metrics |

### 🔄 Backward Compatibility

- **100% compatible** with existing boolean-only datasets
- **Legacy format support** for entries with `featureSet` structure
- **Direct format support** for metadata-test.json format
- **Automatic format detection** with seamless processing

### 🎯 Key Enhancements

1. **Multi-type vectorization**: Process mixed datasets with different data types
2. **Intelligent type inference**: Automatically detect data types from statistics
3. **Enhanced schema**: Rich metadata for proper result decoding
4. **Structured architecture**: Clean, extensible design with proper abstractions
5. **Comprehensive testing**: Full test coverage for all features

## 📊 Data Format Examples

### Boolean Features
```json
{
  "featureName": "hasDriverLicense",
  "dataType": "BOOLEAN",
  "statistics": {
    "numOfNotNull": 100,
    "numOfTrue": 75
  }
}
```
**Vectorized**: `[100, 75]` → 75% have driver's license

### Numeric Features
```json
{
  "featureName": "patient_age",
  "dataType": "NUMERIC",
  "statistics": {
    "numOfNotNull": 1000,
    "min": 18.5,
    "max": 89.2,
    "avg": 45.7,
    "q1": 32.0,
    "q2": 45.5,
    "q3": 58.9
  }
}
```
**Vectorized**: `[1000, 18.5, 89.2, 45.7, 32.0, 45.5, 58.9]` → Full statistical summary

### Categorical Features
```json
{
  "featureName": "patient_gender",
  "dataType": "NOMINAL",
  "statistics": {
    "numOfNotNull": 1000,
    "valueSet": ["male", "female", "other"],
    "cardinalityPerItem": {
      "male": 520,
      "female": 460,
      "other": 20
    }
  }
}
```
**Vectorized**: `[1000, 3, 520]` → 1000 records, 3 categories, top category has 520 instances

## 🔧 Usage

### Basic Usage
```python
from encoder import Encoder
from vectorization_service import VectorizationService

# Initialize
encoder = Encoder()
vectorizer = VectorizationService(encoder)

# Process data
enhanced_data, encoders_list, schema_list = vectorizer.enhance_dataset(data)

# Check supported types
print(vectorizer.get_supported_data_types())
# Output: ['BOOLEAN', 'NUMERIC', 'NOMINAL', 'ORDINAL']
```

### Data Format Support

#### Legacy Format (Backward Compatible)
```json
{
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
          }
        ]
      }
    }
  ]
}
```

#### Direct Format (New)
```json
{
  "features": [
    {"name": "hasDriverLicense", "dataType": "BOOLEAN"}
  ],
  "entries": {
    "hasDriverLicense": {
      "numOfNotNull": 100,
      "numOfTrue": 75
    }
  }
}
```

### Feature Filtering
```python
# Process only specific features
enhanced_data, encoders_list, schema_list = vectorizer.enhance_dataset(
    data, 
    query="patient_age"
)
```

## 🧪 Testing

### Run All Tests
```bash
cd vectorization-service
python run_tests.py
```

### Test Coverage
- ✅ **Boolean vectorization** (backward compatibility)
- ✅ **Numeric vectorization** (full statistical summary)
- ✅ **Categorical vectorization** (distribution metrics)
- ✅ **Mixed data types** (combined processing)
- ✅ **Legacy format support** (existing datasets)
- ✅ **Direct format support** (metadata-test.json)
- ✅ **Data type inference** (automatic detection)
- ✅ **Query filtering** (feature selection)
- ✅ **Edge cases** (empty data, malformed input)
- ✅ **Integration tests** (end-to-end pipeline)

### Demo Script
```bash
cd vectorization-service
python demo_enhanced_vectorization.py
```

## 🏗️ Architecture

### Core Components

#### 1. **Vectorizers** (`encoder.py`)
- **`BaseVectorizer`**: Abstract base class for all vectorizers
- **`BooleanVectorizer`**: Handles boolean statistics
- **`NumericVectorizer`**: Processes numeric statistics
- **`CategoricalVectorizer`**: Manages categorical statistics

#### 2. **Encoder** (`encoder.py`)
- **`Encoder`**: Main encoder class with multi-type support
- **Feature vector creation**: Generates encoder objects for each data type
- **Type management**: Maps data types to appropriate vectorizers

#### 3. **Vectorization Service** (`vectorization_service.py`)
- **`VectorizationService`**: Main service with enhanced capabilities
- **Format detection**: Automatically detects legacy vs direct formats
- **Type inference**: Infers data types from statistics structure
- **Schema generation**: Creates rich metadata for result decoding

#### 4. **Enhanced Aggregator** (`aggregator_manager.py`)
- **Multi-type decoder**: Handles mixed data types in aggregated results
- **Boolean decoding**: Percentage calculations
- **Numeric decoding**: Statistical summary
- **Categorical decoding**: Diversity metrics

## 📈 Pipeline Flow

### 1. **Data Processing**
```
Input Data → Format Detection → Type Inference → Vectorization → Schema Generation
```

### 2. **Aggregation**
```
Individual Vectors → Flattening → SMPC Aggregation → Result Decoding → Final Statistics
```

### 3. **Result Decoding**
```
Aggregated Array → Schema Lookup → Type-specific Decoding → Human-readable Results
```

## 🔍 Example: Multi-Party Aggregation

### Input (3 Hospitals)
```python
# Hospital A: 1000 patients, 75% have condition
# Hospital B: 800 patients, 68% have condition  
# Hospital C: 600 patients, 72% have condition
```

### Vectorization
```python
# Hospital A: [1000, 750]
# Hospital B: [800, 544]  
# Hospital C: [600, 432]
```

### Secure Aggregation
```python
# Aggregated: [2400, 1726]
```

### Final Result
```python
# Cross-hospital statistic: 1726/2400 = 71.9% have condition
```

## 🔧 Configuration

### Environment Variables
```bash
# SMPC endpoint
SMPC_URL=http://195.251.63.193:9000

# Client identifier
ID=TestAthSmpcClient

# Orchestrator endpoint
ORCHESTRATOR_URL=http://localhost:5000
```

### Deployment
- **Development**: `docker-compose -f docker-compose.dev.yml up --build`
- **Production**: `docker-compose -f docker-compose.prod.yml up -d`

## 🚨 Migration Guide

### From Boolean-Only to Enhanced System

#### No Changes Required
- Existing boolean datasets work unchanged
- Legacy API calls remain functional
- Output format stays consistent for boolean features

#### Optional Enhancements
- Add numeric and categorical features to datasets
- Use enhanced schema information for better result interpretation
- Leverage type inference for automatic data type detection

## 📝 API Reference

### VectorizationService Methods

#### `enhance_dataset(data, query=None)`
- **Purpose**: Main processing method for any dataset format
- **Parameters**: 
  - `data`: Dataset in legacy or direct format
  - `query`: Optional feature name filter
- **Returns**: `(enhanced_data, encoders_list, schema_list)`

#### `get_supported_data_types()`
- **Purpose**: List all supported data types
- **Returns**: `['BOOLEAN', 'NUMERIC', 'NOMINAL', 'ORDINAL']`

#### `get_vector_schema(data_type)`
- **Purpose**: Get schema information for a data type
- **Parameters**: `data_type` (e.g., 'BOOLEAN')
- **Returns**: Schema dictionary with fields and length

### Encoder Methods

#### `vectorize_feature_statistics(data_type, statistics)`
- **Purpose**: Convert statistics to vector format
- **Parameters**: Data type and statistics dictionary
- **Returns**: Vector representation

#### `encode_feature_vector(data_type, vector)`
- **Purpose**: Create encoder object for a vector
- **Parameters**: Data type and vector data
- **Returns**: Encoder object with metadata

## 🎯 Benefits

### For Researchers
- **Richer insights**: Process numeric and categorical data
- **Better statistics**: Full statistical summaries instead of just counts
- **Flexible analysis**: Support for diverse data types

### For Developers
- **Backward compatibility**: No breaking changes
- **Clean architecture**: Extensible design for new data types
- **Comprehensive testing**: High confidence in system reliability

### For Organizations
- **Seamless migration**: Gradual adoption without disruption
- **Enhanced capabilities**: Support for more complex datasets
- **Future-proof**: Extensible architecture for new requirements

## 📞 Support

- **Documentation**: See individual service READMEs
- **Testing**: Run comprehensive test suites
- **Demo**: Use provided demo scripts
- **Architecture**: Review pipeline diagrams

---

**🎉 The enhanced vectorization system maintains full backward compatibility while dramatically expanding capabilities to support diverse data types in secure multi-party computation scenarios.** 