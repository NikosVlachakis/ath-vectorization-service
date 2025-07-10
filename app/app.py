# app.py
import logging
from flask import Flask
from application.vectorization_bp import vectorization_bp  # import the blueprint

<<<<<<< HEAD
def create_app():
=======
# Local imports
from encoder import Encoder
from vectorization_service import VectorizationService
from services.smpc_service import SMPCService
from services.orchestrator_notifier import OrchestratorNotifier


app = Flask(__name__)

@app.route('/vectorize', methods=['POST'])
def vectorize_endpoint():
    """
    HTTP endpoint that triggers:
      1) Dataset fetch
      2) Vectorization
      3) Writes results to local outputs
      4) Posts to SMPC
      5) Notifies Orchestrator

    Request JSON body example:
    {
      "url": "<dataset_url>",
      "jobId": "<job_id>",
      "totalClients": 2,
      "orchestratorUrl": "http://orchestrator:5000"
    }
    """
    # 1) Parse input arguments from JSON
    data = request.json or {}
    url = data.get("url")
    job_id = data.get("jobId")
    total_clients = data.get("totalClients")
    orchestrator_url = data.get("orchestratorUrl")

    client_id = os.getenv('ID')  # Get CLIENT_ID from environment variables
    smpc_url = os.getenv('SMPC_URL')  # Get SMPC_URL from environment variables

    client_id = 'ZuellingPharma'
    smpc_url = 'http://195.251.63.193:9000'
    smpc_url_2 = os.getenv('SMPC_URL')  # Get SMPC_URL from environment variables

    if not url:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    # 2) Fetch the dataset
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        json_data = resp.json()
    except requests.RequestException as e:
        logging.error(f"[Vectorize] Failed to fetch dataset from {url} -> {e}")
        return jsonify({"error": f"Failed to fetch dataset: {str(e)}"}), 400

    # 3) Vectorize
    encoder_obj = Encoder()
    vectorizer = VectorizationService(encoder_obj)
    enhanced_data, encoders_list, schema_list = vectorizer.enhance_dataset(json_data)

    # 4) Write outputs to local folder
    os.makedirs("/app/output", exist_ok=True)
    output_path = "/app/output/enhanced_dataset.json"
    encoder_output_path = "/app/output/encoders_only.json"
    schema_output_path = "/app/output/schema.json"

    with open(output_path, "w") as f:
        json.dump(enhanced_data, f, indent=4)
    with open(encoder_output_path, "w") as f:
        json.dump(encoders_list, f, indent=4)
    with open(schema_output_path, "w") as f:
        json.dump(schema_list, f, indent=4)

    logging.info(f"[Vectorize] Wrote outputs to: {output_path}, {encoder_output_path}, {schema_output_path}")

    # 5) If SMPC + jobId are provided, post first encoder
    if smpc_url and job_id:

        smpc_service = SMPCService(base_url=smpc_url_2)

        first_encoder = encoders_list[0] if encoders_list else {"type": "int", "data": []}
        success = smpc_service.post_first_encoder(job_id, first_encoder)



        smpc_service = SMPCService(base_url=smpc_url)

        first_encoder = encoders_list[0] if encoders_list else {"type": "int", "data": []}
        success = smpc_service.post_first_encoder(job_id, first_encoder)

        # 6) If SMPC success, notify orchestrator if orchestratorUrl + clientId + totalClients given
        if success and orchestrator_url and client_id and total_clients is not None:
            notifier = OrchestratorNotifier(orchestrator_url)
            notified = notifier.notify(job_id, client_id, total_clients, schema_list)
            if notified:
                logging.info("[Vectorize] Successfully notified computations orchestrator.")
            else:
                logging.warning("[Vectorize] Failed to notify orchestrator.")
        else:
            logging.info("[Vectorize] SMPC update failed or missing orchestrator info; no orchestrator notify.")
    else:
        logging.info("[Vectorize] No SMPC or orchestrator arguments provided; skipping those steps.")

    return jsonify({
        "message": "Vectorization completed.",
        "outputPaths": {
            "enhancedData": output_path,
            "encodersOnly": encoder_output_path,
            "schema": schema_output_path
        },
        "encodersCount": len(encoders_list),
        "schemaCount": len(schema_list)
    }), 200

def main():
>>>>>>> b9fc02528fb1f16b0bdf466c8ef905deef196330
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    app = Flask(__name__)
    app.register_blueprint(vectorization_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5001, debug=False)
