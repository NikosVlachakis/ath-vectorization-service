# 🚀 Athina Enhanced Vectorization Pipeline

A **secure multi-party computation (SMPC)** system for privacy-preserving data analysis with support for Boolean, Numeric, and Categorical data types.

## 🎯 Quick Start

### 1. Start Services
```bash
# Start orchestrator
cd computations-orchestrator
docker-compose up -d

# Start vectorization service
cd ../vectorization-service
docker-compose up -d
```

### 2. Run Pipeline
```bash
cd trigger-vectorization-pipeline
python trigger_vectorization.py \
  --vectorizationServiceUrl http://localhost:5001 \
  --url metadata-test.json \
  --jobId my_job_001 \
  --totalClients 1 \
  --orchestratorUrl http://host.docker.internal:5000
```

### 3. Verify Results
```bash
# Check output files
docker exec -it vectorization_service_container ls -la /app/output/

# View processing logs
docker logs vectorization_service_container
```

## 🌟 Key Features

- ✅ **Multi-Type Data Processing**: Boolean, Numeric, and Categorical features
- ✅ **Flexible Input**: Local files and URL-based datasets
- ✅ **Backward Compatible**: 100% compatible with existing systems
- ✅ **Secure**: SMPC-based privacy-preserving computation
- ✅ **Scalable**: Microservice architecture with Docker
- ✅ **Real-time**: HTTP API for immediate processing

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
8. **Results** → Final aggregated results

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[PIPELINE_DOCUMENTATION.md](PIPELINE_DOCUMENTATION.md)** | 📚 Complete system documentation |
| **[TESTING_GUIDE.md](TESTING_GUIDE.md)** | 🧪 Comprehensive testing procedures |
| **[ENHANCED_VECTORIZATION_README.md](ENHANCED_VECTORIZATION_README.md)** | 🔧 Technical implementation details |

## 🛠️ Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Git

## 🚀 Installation

```bash
# Clone repository
git clone <repository-url>
cd Athina

# Start all services
./start_services.sh

# Verify installation
docker ps
```

## 💡 Usage Examples

### Basic Usage - Local File
```bash
python trigger_vectorization.py \
  --vectorizationServiceUrl http://localhost:5001 \
  --url my_dataset.json \
  --jobId job_001 \
  --totalClients 1 \
  --orchestratorUrl http://host.docker.internal:5000
```

### Multi-Client Scenario
```bash
# Client 1
python trigger_vectorization.py \
  --url client1_data.json \
  --jobId shared_job \
  --totalClients 3 \
  --vectorizationServiceUrl http://localhost:5001 \
  --orchestratorUrl http://host.docker.internal:5000

# Client 2 & 3 use same jobId with their own data
```

### URL-based Dataset
```bash
python trigger_vectorization.py \
  --vectorizationServiceUrl http://localhost:5001 \
  --url https://example.com/dataset.json \
  --jobId job_002 \
  --totalClients 1 \
  --orchestratorUrl http://host.docker.internal:5000
```

## 🔌 API Endpoints

- **Vectorization Service**: `http://localhost:5001/vectorize`
- **Orchestrator**: `http://localhost:5000/api/update`
- **SMPC Client**: `http://localhost:9001`
- **Redis**: `http://localhost:6379`

## 🧪 Testing

### Run All Tests
```bash
cd vectorization-service
python run_tests.py
```

### Test Pipeline
```bash
# Follow TESTING_GUIDE.md for comprehensive testing
```

**Expected Results**: 19/19 tests pass ✅

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Connection Error** | Use `host.docker.internal` for container-to-host communication |
| **File Not Found** | Ensure files exist in container: `docker exec -it <container> ls /app/` |
| **Port Conflicts** | Check ports 5000, 5001, 6379, 9001 are free |
| **Network Issues** | Verify all containers are running: `docker ps` |

### Debug Commands
```bash
# View logs
docker logs vectorization_service_container

# Access container
docker exec -it vectorization_service_container /bin/bash

# Check outputs
docker exec -it vectorization_service_container ls -la /app/output/
```

## 📊 Expected Output

### Successful Pipeline Run
```
INFO: Vectorization trigger request succeeded.
Response code: 200
Response body: {
  "message": "Vectorization completed.",
  "encodersCount": 1,
  "schemaCount": 6
}
```

### Generated Files
- `enhanced_dataset.json` - Original data with enhancements
- `encoders_only.json` - Encoded vectors for SMPC
- `schema.json` - Schema information for decoding

## 🌐 Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| **Vectorization Service** | 5001 | Data processing API |
| **Orchestrator** | 5000 | Coordination & aggregation |
| **SMPC Client** | 9001 | Secure computation |
| **Redis** | 6379 | Metadata storage |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add my feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit Pull Request

## 📄 License

[License information]

---

## 🎉 Ready to Get Started?

1. **📚 Read the full documentation**: [PIPELINE_DOCUMENTATION.md](PIPELINE_DOCUMENTATION.md)
2. **🧪 Run comprehensive tests**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
3. **🔧 Explore technical details**: [ENHANCED_VECTORIZATION_README.md](ENHANCED_VECTORIZATION_README.md)

**Happy vectorizing with secure multi-party computation!** 🚀 