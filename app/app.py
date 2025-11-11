from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch, exceptions
import os
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Config
ES_HOST = os.environ.get("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ES_USER = os.environ.get("ELASTICSEARCH_USERNAME", "elastic") 
ES_PASS = os.environ.get("ELASTICSEARCH_PASSWORD", "password")
INDEX_NAME = "cities"

# Elasticsearch client with connection pooling
es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    request_timeout=30,
    max_retries=3,
    retry_on_timeout=True,
    verify_certs=False
)

# Wait for Elasticsearch to be ready
def wait_for_elasticsearch():
    for i in range(30):
        try:
            if es.ping():
                logger.info("Connected to Elasticsearch")
                return True
        except:
            pass
        logger.info(f"Waiting for Elasticsearch... ({i+1}/30)")
        time.sleep(2)
    logger.error("Failed to connect to Elasticsearch")
    return False

# Initialize data
def init_data():
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "city": {"type": "keyword"},
                        "population": {"type": "long"}
                    }
                }
            }
        )
        logger.info(f"Created index: {INDEX_NAME}")

    cities = [
        {"city": "Baku", "population": 2200000},
        {"city": "London", "population": 9000000},
        {"city": "New York", "population": 8500000},
        {"city": "Paris", "population": 2100000}
    ]
    
    for city in cities:
        es.index(
            index=INDEX_NAME,
            id=city["city"].lower(),
            document=city,
            op_type="create",
            refresh=True
        )
    logger.info("Initial data loaded")

# Initialize
if wait_for_elasticsearch():
    init_data()

# Routes
@app.route("/health")
def health():
    status = 200 if es.ping() else 503
    return jsonify({"status": "ok" if status == 200 else "unhealthy"}), status

@app.route("/city", methods=["POST"])
def upsert_city():
    data = request.get_json()
    city = data.get("city")
    population = data.get("population")
    
    if not city or population is None:
        return jsonify({"error": "city and population required"}), 400
    
    try:
        es.index(
            index=INDEX_NAME,
            id=city.lower(),
            document={"city": city, "population": population},
            refresh=True
        )
        return jsonify({"message": f"{city} upserted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/city/<city_name>")
def get_city(city_name):
    try:
        res = es.get(index=INDEX_NAME, id=city_name.lower())
        return jsonify(res["_source"]), 200
    except exceptions.NotFoundError:
        return jsonify({"error": "City not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)