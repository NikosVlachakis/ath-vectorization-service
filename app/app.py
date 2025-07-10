# app.py
import logging
from flask import Flask
from application.vectorization_bp import vectorization_bp  # import the blueprint

def create_app():
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
