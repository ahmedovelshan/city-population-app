from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import os

app = Flask(__name__)

# -----------------------------
# Environment variables
# -----------------------------
ES_HOST = os.environ.get("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ES_USER = os.environ.get("ELASTICSEARCH_USERNAME", "elastic")
ES_PASS = os.environ.get("ELASTICSEARCH_PASSWORD", "password")

# -----------------------------
# Connect to Elasticsearch
# -----------------------------
es = Elasticsearch(ES_HOST, basic_auth=(ES_USER, ES_PASS))
if es.ping():
    print("Connected to Elasticsearch!")
else:
    print("Warning: Elasticsearch not reachable at startup. Init container should have waited for it.")

# -----------------------------
# Index configuration
# -----------------------------
INDEX_NAME = "cities"

# Pre-populated cities
prepopulated_cities = [
    {"city": "Baku", "population": 2200000},
    {"city": "London", "population": 9000000},
    {"city": "New York", "population": 8500000},
    {"city": "Paris", "population": 2100000}
]

# Create index and insert pre-populated data safely
try:
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME)
        print(f"Index '{INDEX_NAME}' created.")

    for city in prepopulated_cities:
        es.index(index=INDEX_NAME, id=city["city"].lower(), document=city)
    print("Pre-populated cities inserted successfully.")

except Exception as e:
    print(f"Could not create index or insert data: {e}")

# -----------------------------
# API Endpoints
# -----------------------------

# Health check
@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

# Upsert a city
@app.route("/city", methods=["POST"])
def upsert_city():
    data = request.get_json()
    city = data.get("city")
    population = data.get("population")

    if not city or population is None:
        return jsonify({"error": "city and population required"}), 400

    try:
        es.index(index=INDEX_NAME, id=city.lower(), document={"city": city, "population": population})
        return jsonify({"message": f"{city} added/updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to add/update city: {e}"}), 500

# Query a city population
@app.route("/city/<city_name>", methods=["GET"])
def get_city(city_name):
    try:
        res = es.get(index=INDEX_NAME, id=city_name.lower(), ignore=[404])
        if not res.get("found"):
            return jsonify({"error": "City not found"}), 404
        return jsonify(res["_source"]), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve city: {e}"}), 500

# -----------------------------
# Start Flask App
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
