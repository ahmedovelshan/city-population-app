import logging
import os
import time
from urllib.parse import quote

import requests
from flask import Flask, jsonify, request

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__)

ES_HOST = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200").rstrip("/")
ES_USER = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
ES_PASS = os.getenv("ELASTICSEARCH_PASSWORD", "")
INDEX_NAME = "cities"
MAX_CITY_NAME_LENGTH = 100
MAX_POPULATION = 2**63 - 1


def es_request(method, path, payload=None):
    """Send an authenticated request to Elasticsearch."""
    url = f"{ES_HOST}{path}"
    response = requests.request(
        method,
        url,
        json=payload,
        auth=(ES_USER, ES_PASS),
        headers={"Content-Type": "application/json"},
        timeout=(3, 10),
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def wait_for_elasticsearch(attempts=30, interval=2):
    """Wait for Elasticsearch before initializing the application."""
    for attempt in range(1, attempts + 1):
        try:
            es_request("GET", "/")
            logger.info("Connected to Elasticsearch")
            return True
        except requests.exceptions.RequestException as exc:
            logger.info(
                "Waiting for Elasticsearch (%s/%s): %s",
                attempt,
                attempts,
                exc,
            )
            if attempt < attempts:
                time.sleep(interval)
    return False


def init_data():
    """Create the index if needed and idempotently seed example cities."""
    mapping = {
        "mappings": {
            "properties": {
                "city": {"type": "keyword"},
                "population": {"type": "long"},
            }
        }
    }
    try:
        try:
            es_request("PUT", f"/{INDEX_NAME}", mapping)
        except requests.exceptions.HTTPError as exc:
            error_type = None
            if exc.response is not None:
                try:
                    error_type = exc.response.json().get("error", {}).get("type")
                except (ValueError, AttributeError):
                    pass
            if error_type != "resource_already_exists_exception":
                raise

        cities = [
            {"city": "Baku", "population": 2200000},
            {"city": "London", "population": 9000000},
            {"city": "New York", "population": 8500000},
            {"city": "Paris", "population": 2100000},
        ]
        for city in cities:
            document_id = quote(city["city"].casefold(), safe="")
            es_request("PUT", f"/{INDEX_NAME}/_doc/{document_id}", city)

        logger.info("City data initialized")
        return True
    except requests.exceptions.RequestException:
        logger.exception("Failed to initialize Elasticsearch data")
        return False


def initialize():
    """Fail container startup if Elasticsearch cannot be initialized."""
    if not wait_for_elasticsearch() or not init_data():
        raise RuntimeError("Elasticsearch initialization failed")


def normalize_city_name(value):
    if not isinstance(value, str):
        return None
    city = value.strip()
    if not city or len(city) > MAX_CITY_NAME_LENGTH:
        return None
    return city


@app.route("/live", methods=["GET"])
def live():
    """Liveness check: confirms only that the Flask process is responding."""
    return jsonify({"status": "alive"}), 200


@app.route("/health", methods=["GET"])
def health():
    """Readiness check: confirms that Elasticsearch is reachable."""
    try:
        es_request("GET", "/_cluster/health")
        return jsonify({"status": "healthy"}), 200
    except requests.exceptions.RequestException:
        logger.exception("Readiness check failed")
        return jsonify({"status": "unhealthy"}), 503


@app.route("/city", methods=["POST"])
def upsert_city():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    city = normalize_city_name(data.get("city"))
    population = data.get("population")
    if city is None:
        return jsonify(
            {"error": f"city must be a non-empty string of at most {MAX_CITY_NAME_LENGTH} characters"}
        ), 400
    if type(population) is not int or not 0 <= population <= MAX_POPULATION:
        return jsonify(
            {"error": "population must be a non-negative 64-bit integer"}
        ), 400

    document_id = quote(city.casefold(), safe="")
    try:
        es_request(
            "PUT",
            f"/{INDEX_NAME}/_doc/{document_id}",
            {"city": city, "population": population},
        )
        return jsonify({"message": f"{city} upserted"}), 200
    except requests.exceptions.RequestException:
        logger.exception("Failed to upsert city %s", city)
        return jsonify({"error": "Unable to save city at this time"}), 502


@app.route("/city/<city_name>", methods=["GET"])
def get_city(city_name):
    city = normalize_city_name(city_name)
    if city is None:
        return jsonify({"error": "Invalid city name"}), 400

    document_id = quote(city.casefold(), safe="")
    try:
        result = es_request("GET", f"/{INDEX_NAME}/_doc/{document_id}")
        return jsonify(result["_source"]), 200
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return jsonify({"error": "City not found"}), 404
        logger.exception("Elasticsearch rejected city lookup for %s", city)
        return jsonify({"error": "Unable to retrieve city at this time"}), 502
    except (requests.exceptions.RequestException, KeyError):
        logger.exception("Failed to retrieve city %s", city)
        return jsonify({"error": "Unable to retrieve city at this time"}), 502


if __name__ == "__main__":
    initialize()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
