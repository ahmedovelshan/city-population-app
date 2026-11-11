# City Population App

A containerized Flask REST API for city population data, backed by Elasticsearch and deployable to Kubernetes with Helm.

## Features

- `GET /live`: process liveness check (does not depend on Elasticsearch).
- `GET /health`: readiness check (requires Elasticsearch).
- `POST /city`: insert or update a city and its population.
- `GET /city/<city_name>`: retrieve a city's population.
- Non-root Docker image and production Gunicorn WSGI server.
- Helm deployment with optional Elasticsearch persistent storage.
- GitHub Actions unit tests and GHCR image publishing.

## Project structure

```text
.
├── .github/workflows/docker-build-push.yml
├── app
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── tests/test_app.py
└── helm-chart
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
```

## Run tests locally

Python 3.11 or newer is recommended.

```bash
python -m pip install -r app/requirements.txt
PYTHONPATH=app python -m unittest discover -s app/tests -v
```

The tests mock Elasticsearch and do not require a running cluster.

## Build the Docker image

Run from the repository root:

```bash
docker build -t city-population-app:local ./app
```

The container waits for Elasticsearch, creates the index if needed, seeds the example cities, and then starts Gunicorn. Set `ELASTICSEARCH_URL`, `ELASTICSEARCH_USERNAME`, and `ELASTICSEARCH_PASSWORD` when running it outside Kubernetes.

## Deploy to Kubernetes with Helm

Prerequisites: Kubernetes, kubectl, Helm 3, and a cluster with sufficient resources for Elasticsearch.

Create a password file outside the repository. Do not commit credentials:

```bash
umask 077
read -rsp "Elasticsearch password: " ES_PASSWORD
printf '%s' "$ES_PASSWORD" > /tmp/city-population-es-password
unset ES_PASSWORD
```

Install without persistent storage (the default; Elasticsearch data is lost when its pod is recreated):

```bash
helm upgrade --install city-population ./helm-chart \
  --namespace city-population-app --create-namespace \
  --set-file elasticsearch.password=/tmp/city-population-es-password
```

For persistent Elasticsearch data, provide a StorageClass available in your cluster:

```bash
helm upgrade --install city-population ./helm-chart \
  --namespace city-population-app --create-namespace \
  --set-file elasticsearch.password=/tmp/city-population-es-password \
  --set elasticsearch.persistence.enabled=true \
  --set elasticsearch.persistence.storageClass=YOUR_STORAGE_CLASS \
  --set elasticsearch.persistence.size=10Gi
```

Remove the temporary password file after installation:

```bash
rm -f /tmp/city-population-es-password
```

The chart intentionally requires an Elasticsearch password and does not ship with a default credential. For production, use an external secret manager and enable TLS for Elasticsearch traffic.

Check the deployment:

```bash
kubectl get pods -n city-population-app
kubectl get services -n city-population-app
kubectl port-forward -n city-population-app service/city-populations 5000:5000
```

## API examples

```bash
curl http://127.0.0.1:5000/live
curl http://127.0.0.1:5000/health
curl -X POST http://127.0.0.1:5000/city \
  -H "Content-Type: application/json" \
  -d '{"city":"Rome","population":2873000}'
curl http://127.0.0.1:5000/city/Rome
```

Population must be a non-negative 64-bit integer. City names must be non-empty strings of at most 100 characters.

## CI/CD

Pull requests that modify the application or Helm chart run the Python unit tests and compile check. Pushes to `main` that modify `app/**` run the tests, build the Docker image, and publish immutable commit-SHA and `latest` tags to GHCR. The workflow then updates the Helm chart's image tag and app version.

The GitHub Actions workflow uses read-only permissions by default and grants package/content write permissions only to the publishing job.

## License

MIT
