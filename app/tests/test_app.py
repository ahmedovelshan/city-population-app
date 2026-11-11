import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as city_app


class CityApiTests(unittest.TestCase):
    def setUp(self):
        self.client = city_app.app.test_client()

    @patch.object(city_app, "es_request")
    def test_upsert_city_uses_normalized_document_id(self, es_request):
        response = self.client.post(
            "/city",
            json={"city": " New York ", "population": 8500000},
        )

        self.assertEqual(response.status_code, 200)
        es_request.assert_called_once_with(
            "PUT",
            "/cities/_doc/new%20york",
            {"city": "New York", "population": 8500000},
        )

    def test_upsert_rejects_non_json_payload(self):
        response = self.client.post("/city", data="not-json")

        self.assertEqual(response.status_code, 400)

    def test_upsert_rejects_missing_fields(self):
        response = self.client.post("/city", json={"city": "Baku"})

        self.assertEqual(response.status_code, 400)

    def test_upsert_rejects_invalid_population_values(self):
        for population in (-1, 1.5, True, "100"):
            with self.subTest(population=population):
                response = self.client.post(
                    "/city",
                    json={"city": "Baku", "population": population},
                )
                self.assertEqual(response.status_code, 400)

    def test_upsert_rejects_blank_city(self):
        response = self.client.post(
            "/city",
            json={"city": "   ", "population": 10},
        )

        self.assertEqual(response.status_code, 400)

    @patch.object(city_app, "es_request", return_value={"_source": {"city": "Baku", "population": 2200000}})
    def test_get_city_returns_document(self, es_request):
        response = self.client.get("/city/Baku")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["population"], 2200000)
        es_request.assert_called_once_with("GET", "/cities/_doc/baku")

    @patch.object(city_app, "es_request")
    def test_get_city_returns_404_when_document_is_missing(self, es_request):
        error_response = Mock(status_code=404)
        es_request.side_effect = requests.exceptions.HTTPError(
            response=error_response
        )

        response = self.client.get("/city/Atlantis")

        self.assertEqual(response.status_code, 404)

    @patch.object(city_app, "es_request")
    def test_health_is_unhealthy_when_elasticsearch_is_unavailable(self, es_request):
        es_request.side_effect = requests.exceptions.ConnectionError("unavailable")

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 503)

    def test_liveness_does_not_depend_on_elasticsearch(self):
        response = self.client.get("/live")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "alive"})


if __name__ == "__main__":
    unittest.main()
