from flask import Flask, request, jsonify
import requests
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ES_HOST = os.environ.get("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ES_USER = os.environ.get("ELASTICSEARCH_USERNAME", "elastic")
ES_PASS = os.environ.get("ELASTICSEARCH_PASSWORD", "password")
INDEX_NAME = "cities"

def es_request(method, path, json=None):
    url = f"{ES_HOST}{path}"
    auth = (ES_USER, ES_PASS)
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.request(method, url, json=json, auth=auth, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"ES request failed: {e}")
        raise

def wait_for_elasticsearch():
    for i in range(30):
        try:
            es_request('GET', '/')
            logger.info("Connected to Elasticsearch")
            return True
        except:
            logger.info(f"Waiting for Elasticsearch... ({i+1}/30)")
            time.sleep(2)
    return False

def init_data():
    try:
        # Create index
        es_request('PUT', f'/{INDEX_NAME}', {
            "mappings": {
                "properties": {
                    "city": {"type": "keyword"},
                    "population": {"type": "long"}
                }
            }
        })
        
        cities = [
            {"city": "Baku", "population": 2200000},
            {"city": "London", "population": 9000000},
            {"city": "New York", "population": 8500000},
            {"city": "Paris", "population": 2100000}
        ]
        
        for city in cities:
            es_request('POST', f'/{INDEX_NAME}/_doc/{city["city"].lower()}', city)
        
        logger.info("Data initialized")
    except Exception as e:
        logger.error(f"Init failed: {e}")

if wait_for_elasticsearch():
    init_data()

@app.route("/health")
def health():
    try:
        es_request('GET', '/_cluster/health')
        return jsonify({"status": "healthy"}), 200
    except:
        return jsonify({"status": "unhealthy"}), 503

@app.route("/city", methods=["POST"])
def upsert_city():
    try:
        data = request.get_json()
        city = data.get("city")
        population = data.get("population")
        
        if not city or population is None:
            return jsonify({"error": "city and population required"}), 400
        
        es_request('POST', f'/{INDEX_NAME}/_doc/{city.lower()}', {
            "city": city, 
            "population": population
        })
        return jsonify({"message": f"{city} upserted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/city/<city_name>")
def get_city(city_name):
    try:
        result = es_request('GET', f'/{INDEX_NAME}/_doc/{city_name.lower()}')
        return jsonify(result['_source']), 200
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "City not found"}), 404
        raise
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)