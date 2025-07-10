# Athina Enhanced Vectorization System - Testing Guide

This guide provides comprehensive testing procedures for the enhanced vectorization system that supports boolean, numeric, and categorical data types.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ installed
- All services running (orchestrator, vectorization service, Redis, SMPC)

## 1. Service Startup

### Start All Services

```bash
# Start orchestrator service
cd computations-orchestrator
docker-compose up -d

# Start vectorization service
cd ../vectorization-service
docker-compose up -d

# Verify services are running
docker ps
```

Expected output should show:
- `computations_orchestrator_container` on port 5000
- `vectorization_service_container` on port 5001
- `computations_redis` on port 6379
- `smpc_client` on port 9001

## 2. Unit Tests

### Run All Unit Tests

```bash
cd vectorization-service
python run_tests.py
```

Expected output:
```
Running enhanced vectorization tests...
....................
----------------------------------------------------------------------
Ran 19 tests in 0.004s

OK

✅ All tests passed!
```

### Individual Test Categories

```bash
# Test enhanced vectorization only
python -m pytest tests/test_enhanced_vectorization.py -v

# Test metadata integration
python -m pytest tests/test_metadata_integration.py -v
```

## 3. Pipeline Integration Tests

### Test with Local File (Recommended)

```bash
cd trigger-vectorization-pipeline
python trigger_vectorization.py \
  --vectorizationServiceUrl http://localhost:5001 \
  --url metadata-test.json \
  --jobId test_job_metadata \
  --totalClients 1 \
  --orchestratorUrl http://host.docker.internal:5000
```

### Test with URL-based Dataset

First, start an HTTP server for the dataset:

```bash
cd vectorization-service
python -m http.server 8080
```

Then in another terminal:

```bash
cd trigger-vectorization-pipeline
python trigger_vectorization.py \
  --vectorizationServiceUrl http://localhost:5001 \
  --url http://localhost:8080/metadata-test.json \
  --jobId test_job_url \
  --totalClients 1 \
  --orchestratorUrl http://host.docker.internal:5000
```

### Expected Pipeline Success Output

```
2025-07-10 12:39:46,051 INFO: Sending POST to http://localhost:5001/vectorize with body: {'url': 'metadata-test.json', 'jobId': 'test_job_metadata', 'totalClients': 1, 'orchestratorUrl': 'http://host.docker.internal:5000'}
2025-07-10 12:39:46,087 INFO: Response code: 200
2025-07-10 12:39:46,087 INFO: Response body: {"encodersCount":1,"message":"Vectorization completed.","outputPaths":{"encodersOnly":"/app/output/encoders_only.json","enhancedData":"/app/output/enhanced_dataset.json","schema":"/app/output/schema.json"},"schemaCount":6}
2025-07-10 12:39:46,087 INFO: Vectorization trigger request succeeded.
```

## 4. Result Verification

### Check Output Files

```bash
# Access container to check outputs
docker exec -it vectorization_service_container /bin/bash
ls -la /app/output/

# Should show:
# enhanced_dataset.json
# encoders_only.json  
# schema.json
```

### Verify Processing Logs

```bash
# Check vectorization service logs
docker logs vectorization_service_container

# Should show successful processing of all data types:
# - NUMERIC features (age, salary)
# - BOOLEAN features (isActive, hasInsurance)
# - NOMINAL features (department, jobTitle)
```

## 5. Advanced Testing

### Test Different Data Types

```bash
# Test with boolean-only data
python trigger_vectorization.py \
  --vectorizationServiceUrl http://localhost:5001 \
  --url boolean-only-dataset.json \
  --jobId test_boolean \
  --totalClients 1 \
  --orchestratorUrl http://host.docker.internal:5000

# Test with numeric-only data
python trigger_vectorization.py \
  --vectorizationServiceUrl http://localhost:5001 \
  --url numeric-only-dataset.json \
  --jobId test_numeric \
  --totalClients 1 \
  --orchestratorUrl http://host.docker.internal:5000
```

### Demo Script

```bash
cd vectorization-service
python demo_enhanced_vectorization.py
```

## 6. Troubleshooting

### Common Issues

1. **Container Connection Errors**
   - Ensure all containers are running: `docker ps`
   - Check container logs: `docker logs <container_name>`

2. **File Not Found Errors**
   - Verify files exist inside containers: `docker exec -it <container> ls /app/`
   - Check file permissions and paths

3. **Port Conflicts**
   - Ensure ports 5000, 5001, 6379, 9001 are not in use
   - Use `netstat -an | grep <port>` to check

4. **Network Issues**
   - Use `host.docker.internal` for inter-container communication
   - Avoid `localhost` when containers need to communicate

### Docker Network Configuration

The services use different Docker networks:
- **Orchestrator**: `computations-orchestrator_default`
- **Vectorization**: `vectorization-service_default`

For communication between containers, use:
- **From container to host**: `http://host.docker.internal:5000`
- **From host to container**: `http://localhost:5000`

## 7. Cleanup

```bash
# Stop all services
cd vectorization-service
docker-compose down

cd ../computations-orchestrator
docker-compose down

# Remove all containers and networks
docker system prune -f
```

## 8. Success Criteria

All tests should pass with these results:

✅ **Unit Tests**: 19/19 tests pass  
✅ **Boolean Processing**: Legacy compatibility maintained  
✅ **Numeric Processing**: 7-field vectors (numOfNotNull, min, max, avg, q1, q2, q3)  
✅ **Categorical Processing**: 3-field vectors (numOfNotNull, numUniqueValues, topValueCount)  
✅ **Pipeline Integration**: HTTP 200 responses with proper JSON output  
✅ **Service Communication**: SMPC posting and orchestrator notification  
✅ **File Handling**: Both local files and URLs supported  

## 9. Next Steps

After successful testing:
1. Review output files for correctness
2. Verify schema alignment with expectations
3. Test with production datasets
4. Monitor performance metrics
5. Configure production deployment settings 