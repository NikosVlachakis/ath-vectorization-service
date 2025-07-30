# app.py
import logging
import sys
import os
from flask import Flask
from application.vectorization_bp import vectorization_bp  # import the blueprint

# Import self-contained logging configuration
try:
    from logging_config import setup_service_logging
    CENTRALIZED_LOGGING = True
except ImportError:
    CENTRALIZED_LOGGING = False

def create_app():
    """Flask application factory"""
    if CENTRALIZED_LOGGING:
        # Setup centralized logging
        logger_instance = setup_service_logging('vectorization-service')
        logger_instance.log_action("Initializing Vectorization Service Flask Application")
    else:
        # Fallback to original logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )
        logging.info("Initializing Vectorization Service Flask Application")
    
    app = Flask(__name__)
    app.register_blueprint(vectorization_bp)
    
    if CENTRALIZED_LOGGING:
        logger_instance.log_success("Vectorization Service Flask application created successfully")
    else:
        logging.info("Vectorization Service Flask application created successfully")
    return app

if __name__ == "__main__":
    app = create_app()
    logging.info("Starting Vectorization Service on 0.0.0.0:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
