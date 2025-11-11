from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch, exceptions
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Config
ES_HOST = os.environ.get("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ES_USER = os.environ.get("ELASTICSEARCH_USERNAME", "elastic")
ES_PASS = os.environ.get("ELASTICSEARCH_PASSWORD", "password")
INDEX_NAME = "cities"

# Elasticsearch client - FIX: Remove HEAD requests by using simple HTTP check
es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASS),
    verify_certs=False,
    ssl_show_warn=False
)

def wait_for_elasticsearch():
    for i in range(30):
        try:
            # FIX: Use proper API call instead of ping() which sends HEAD requests
            es.info()
            logger.info("Connected to Elasticsearch")
            return True
        except exceptions.AuthenticationException as e:
            logger.error(f"Authentication failed: {e}")
            return False
        except exceptions.ConnectionError as e:
            logger.info(f"Waiting for Elasticsearch... ({i+1}/30) - {e}")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Elasticsearch not ready: {e}")
            time.sleep(2)
    logger.error("Failed to connect to Elasticsearch")
    return False

def init_data():
    try:
        if not es.indices.exists(index=INDEX_NAME):
            es.indices.create(index=INDEX_NAME)
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
                refresh=True
            )
        logger.info("Initial data loaded")
    except Exception as e:
        logger.error(f"Data init failed: {e}")

# Initialize
if wait_for_elasticsearch():
    init_data()

@app.route("/health")
def health():
    try:
        es.info()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except:
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 503

@app.route("/city", methods=["POST"])
def upsert_city():
    try:
        data = request.get_json()
        city = data.get("city")
        population = data.get("population")
        
        if not city or population is None:
            return jsonify({"error": "city and population required"}), 400
        
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