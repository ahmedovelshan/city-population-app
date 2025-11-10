from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch, ConnectionError
import os
import time

app = Flask(__name__)

# Use the same env variable as in Deployment
ES_HOST = os.environ.get('ELASTICSEARCH_URL', 'http://elasticsearch:9200')

# Retry connecting to Elasticsearch
for i in range(30):
    try:
        es = Elasticsearch(ES_HOST)
        if es.ping():
            print("Connected to Elasticsearch!")
            break
    except ConnectionError:
        print("Elasticsearch not ready, retrying...")
        time.sleep(5)
else:
    raise Exception("Elasticsearch not available after 30 retries")

INDEX_NAME = "cities"

# Create index if it doesn't exist
if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME)

# Health check endpoint
@app.route("/health", methods=["GET"])
def health_check(): 
    return "OK", 200

# Upsert city (insert or update)
@app.route("/city", methods=["POST"])
def upsert_city():
    data = request.get_json()
    city = data.get("city")
    population = data.get("population")

    if not city or population is None:
        return jsonify({"error": "city and population required"}), 400

    es.index(index=INDEX_NAME, id=city.lower(), body={"city": city, "population": population})
    return jsonify({"message": f"{city} added/updated successfully"}), 200

# Query city population
@app.route("/city/<city_name>", methods=["GET"])
def get_city(city_name):
    res = es.get(index=INDEX_NAME, id=city_name.lower(), ignore=[404])
    if not res.get("found"):
        return jsonify({"error": "City not found"}), 404
    return jsonify(res["_source"]), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
