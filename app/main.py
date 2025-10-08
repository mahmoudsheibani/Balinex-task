import os
import time
import signal
import sys
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import logging
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Global state
is_ready = True
shutdown_in_progress = False

# Simple function to count primes (CPU-bound work)
def count_primes(n):
    """Count prime numbers up to n"""
    if n < 2:
        return 0
    
    count = 0
    for num in range(2, n + 1):
        is_prime = True
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                is_prime = False
                break
        if is_prime:
            count += 1
    return count


@app.route('/healthz', methods=['GET'])
def health():
    """Health check - is the process alive?"""
    if shutdown_in_progress:
        return jsonify({"status": "shutting down"}), 503
    return jsonify({"status": "healthy"}), 200


@app.route('/readyz', methods=['GET'])
def ready():
    """Readiness check - can we serve traffic?"""
    if not is_ready or shutdown_in_progress:
        return jsonify({"status": "not ready"}), 503
    return jsonify({"status": "ready"}), 200


@app.route('/version', methods=['GET'])
def version():
    """Return app version"""
    app_version = os.getenv('APP_VERSION', 'unknown')
    return jsonify({"version": app_version}), 200


@app.route('/compute', methods=['POST'])
def compute():
    """Compute prime numbers up to n"""
    try:
        data = request.get_json()
        if not data or 'n' not in data:
            return jsonify({"error": "missing 'n' parameter"}), 400
        
        n = int(data['n'])
        if n < 0 or n > 100000:
            return jsonify({"error": "n must be between 0 and 100000"}), 400
        
        start_time = time.time()
        result = count_primes(n)
        latency = time.time() - start_time
        
        logger.info(f"Computed primes up to {n}: result={result}, latency={latency:.4f}s")
        
        return jsonify({
            "n": n,
            "primes_count": result,
            "latency_seconds": round(latency, 4)
        }), 200
        
    except ValueError:
        return jsonify({"error": "invalid input"}), 400
    except Exception as e:
        logger.error(f"Error in compute: {str(e)}")
        return jsonify({"error": "internal server error"}), 500


def graceful_shutdown(signum, frame):
    """Handle graceful shutdown"""
    global shutdown_in_progress
    logger.info("Received shutdown signal, starting graceful shutdown...")
    shutdown_in_progress = True
    # Give time for load balancer to detect we're not ready
    time.sleep(5)
    logger.info("Shutdown complete")
    sys.exit(0)


if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)
    
    # Simulate startup time
    logger.info("Starting up...")
    time.sleep(2)
    is_ready = True
    logger.info("Application ready to serve traffic")
    
    # Start server
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)