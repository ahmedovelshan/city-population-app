from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
import os

app = Flask(__name__)

ES_HOST = os.environ.get('ES_HOST', 'http://localhost:9200')
es = Elasticsearch(ES_HOST)

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
