# City Population App

A containerized Python Flask application that manages city population data, exposes REST API endpoints, and stores data in Elasticsearch. The app and Elasticsearch are deployable together on Kubernetes via a Helm chart.

---

## Features

- REST API endpoints:  
  - **Health Check**: `GET /health` → returns `OK`  
  - **Upsert City**: `POST /city` → insert or update city population  
  - **Query City**: `GET /city/<city_name>` → get population of a city  
- Stores all data in Elasticsearch  
- Containerized with Docker  
- Deployable with Helm on Kubernetes  
- Automated Docker image build & push via GitHub Actions  

---

## Project Structure

```
city-population-app/
├── app/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── helm-chart/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── app-deployment.yaml
│       ├── app-service.yaml
│       ├── elasticsearch-deployment.yaml
│       ├── elasticsearch-service.yaml
│       └── ingress.yaml  # optional
├── .github/workflows/docker-build-push.yml
└── README.md
```

---

## Prerequisites

- Docker  
- Kubernetes cluster (local: Minikube / kind / remote cluster)  
- Helm 3  
- GitHub repository with GHCR enabled  

---

## Build and Push Docker Image

GitHub Actions automatically builds and pushes the Docker image to **GHCR** when `app/app.py` changes.

Manual build (optional):

```bash
docker build -t ghcr.io/ahmedovelshan/city-population-app:latest ./app
docker push ghcr.io/ahmedovelshan/city-population-app:latest
```

---

## Deploy to Kubernetes with Helm

1. Clone the repository:  
```bash
git clone <your-repo-url>
cd city-population-app
```

2. Deploy the Helm chart:  
```bash
helm install city-system ./helm-chart
```

3. Verify pods and services:  
```bash
kubectl get pods
kubectl get svc
```

4. Port-forward Flask app to test locally:  
```bash
kubectl port-forward svc/city-populations 5000:5000
curl http://localhost:5000/health
```

---

## Application Flow Diagram

```
+-------------------+        +------------------+
|                   |        |                  |
|   Flask App Pod   | -----> | Elasticsearch Pod|
|                   |        |                  |
+-------------------+        +------------------+
           ^                          ^
           |                          |
           +------ Kubernetes Service -+
```
- Flask app communicates with Elasticsearch via the Kubernetes service `elasticsearch:9200`.  
- The Helm chart deploys both pods and services together.

---

## Helm Chart Notes

- Flask app connects automatically to Elasticsearch via Kubernetes service: `http://elasticsearch:9200`  
- The Helm chart uses `latest` image tag with `imagePullPolicy: Always`  
- Optional Ingress can be configured in `values.yaml`

---

## Reflection

During implementation, the main challenges were configuring Elasticsearch and Flask to communicate reliably in Kubernetes and automating Docker image builds with GitHub Actions. Deploying both the app and Elasticsearch via a single Helm chart required careful environment variable and service setup. For production, the application could be scaled using a multi-node Elasticsearch cluster for HA, persistent volumes, and snapshot backups. Observability can be added with Prometheus, Grafana, and centralized logging, while security should include TLS, authentication, and RBAC. CI/CD and autoscaling ensure smooth deployments and app scalability.

---

## License

MIT License

