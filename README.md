# 🚀 Athina Vectorization Pipeline

This pipeline is used to vectorize the data from the Feature Extraction Tool API and send it to the SMPC client for secure multi-party computation.

## 📊 Supported Data Types

| Type | Input Fields | Output Vector | Length |
|------|--------------|---------------|--------|
| **Boolean** | `numOfNotNull`, `numOfTrue` | `[numOfNotNull, numOfTrue]` | 2 |
| **Numeric** | `numOfNotNull`, `min`, `max`, `avg`, `q1`, `q2`, `q3` | `[numOfNotNull, min, max, avg, q1, q2, q3]` | 7 |
| **Categorical** | `numOfNotNull`, `valueSet`, `cardinalityPerItem` | `[numOfNotNull, numUniqueValues, topValueCount]` | 3 |

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Trigger       │    │ Vectorization   │    │ Computations    │
│   Script        │───▶│   Service       │───▶│ Orchestrator    │
│  (Python CLI)   │    │  (Flask API)    │    │  (Flask API)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                     ┌─────────────────┐    ┌─────────────────┐
                     │   SMPC Client   │    │   Redis Store   │
                     │   (Privacy)     │    │   (Metadata)    │
                     └─────────────────┘    └─────────────────┘
```

## 🔄 Pipeline Flow

1. **Trigger** → User runs script with dataset location
2. **Fetch** → Service fetches from URL or local file
3. **Analyze** → Automatic data type detection
4. **Vectorize** → Convert statistics to numerical vectors
5. **SMPC** → Send to secure computation client
6. **Orchestrate** → Notify orchestrator of completion
7. **Aggregate** → Secure multi-party aggregation
8. **Results** → Final aggregated results after polling the orchestrator


## 🛠️ Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Git

## 🧪 Testing

### Run All Tests
```bash
# Run all tests
cd vectorization-service
python run_tests.py
python test_centralized_logging.py
```
