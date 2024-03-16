
from monitor_watcher import app
from waitress import serve
import logging

if __name__ == "__main__":
    port = 5000
    logging.basicConfig(filename='waitress.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print(f"Server running on port {port}")
    serve(app, host="0.0.0.0", port=port)