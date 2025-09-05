# 🚀 Athina Vectorization Pipeline

This pipeline is used to vectorize the data from the Feature Extraction Tool API and send it to the SMPC client for secure multi-party computation.

## 📊 Supported Data Types

| Type | Input Fields | Output Vector | Length |
|------|--------------|---------------|--------|
| **Boolean** | `numOfNotNull`, `numOfTrue` | `[numOfNotNull, numOfTrue]` | 2 |
| **Numeric** | `numOfNotNull`, `min`, `max`, `avg`, `q1`, `q2`, `q3` | `[numOfNotNull, min, max, avg, q1, q2, q3]` | 7 |
| **Categorical** | `numOfNotNull`, `valueSet`, `cardinalityPerItem` | `[numOfNotNull]` | 1 |

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

## 🔌 API Endpoints

The vectorization service exposes REST API endpoints for pipeline execution and FEM integration.

### Primary Endpoint
```
POST /vectorize
```

### FEM Integration Endpoint
```
GET /export-data/<job_id>
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | `string` | ✅ **Yes** | URL or local file path containing JSON data to vectorize |
| `jobId` | `string` | ✅ **Yes** | Unique job identifier for SMPC and orchestrator tracking |
| `clientsList` | `array` | ✅ **Yes** | List of client IDs participating in computation (e.g., `["client1", "client2"]`) |
| `studyId` | `string` | ✅ **Yes** | Study identifier (required for production mode Feature Extraction Tool API) |

### Environment Variables Used

| Variable | Default | Description |
|----------|---------|-------------|
| `PRODUCTION_MODE` | `false` | When `true`, uses `url` as base URL for Feature Extraction Tool API |
| `ID` | - | Client identifier for orchestrator notifications |
| `SMPC_URL` | http://smpc_client:9001 | Base URL of SMPC service for secure computation |
| `ORCHESTRATOR_URL` | http://195.251.63.82:5000 | Base URL of computations orchestrator

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
