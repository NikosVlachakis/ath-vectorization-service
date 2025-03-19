# Vectorization Service

A microservice that processes and transforms dataset features for secure multi-party computation (SMPC). The service:

1. **Data Collection** - Fetches and validates JSON datasets from specified REST endpoints.

2. **Data Processing** - Transforms raw JSON features into normalized vectors compatible with SMPC.

3. **Data Transmission** -  Sends the processed vectorized data to the respective SMPC client.

4. **Workflow Management** - Notifies the Computations Orchestrator of processing completion status.


## How to Run

### If you want to build and run the image locally, simply execute the provided script:

```bash
bash run_vectorization.bsh
```

The script internally runs:
```bash
docker-compose run vectorization_service python main.py \
  --url "<dataset_url>" \
  --query "<feature_name>" \
  --jobId "<job_id>" \
  --clientId "<client_id>" \
  --totalClients <total_clients> \
  --smpcUrl "<smpc_service_url>" \
  --orchestratorUrl "<orchestrator_url>"
```

Where:
- `url` is the URL of the dataset JSON file.
- `query` If provided, only this specific Boolean feature is processed.
- `job_id` is the ID of the job.
- `client_id` is the ID of the client.
- `total_clients` is the total number of clients.
- `smpc_service_url` is the URL of the SMPC service.
- `orchestrator_url` is the URL of the Computations Orchestrator.


### If you want to run the prebuilt image from Docker Hub, you do not need to build it locally. Instead, use the following command:

```bash
docker run --rm nikosvlah/vectorization-service:latest \
  python main.py \
  --url "<dataset_url>" \
  --query "<feature_name>" \
  --jobId "<job_id>" \
  --clientId "<client_id>" \
  --totalClients <total_clients> \
  --smpcUrl "<smpc_service_url>" \
  --orchestratorUrl "<orchestrator_url>"
```
