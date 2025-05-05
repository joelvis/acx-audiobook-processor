import logging
from app import app

if __name__ == "__main__":
    # Configure logging for better error information
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set Flask logger level
    app.logger.setLevel(logging.INFO)
    
    print("Starting ACX Audiobook Processor server...")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
