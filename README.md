# City Population App

A containerized Python Flask application that manages city population data, exposes REST API endpoints, and stores data in Elasticsearch. The app and Elasticsearch are deployable together on Kubernetes via a Helm chart.

---

## Features

- **REST API endpoints**  
  - **Health Check**: `GET /health` → returns `OK`  
  - **Upsert City**: `POST /city` → insert or update a city's population  
  - **Query City**: `GET /city/<city_name>` → retrieve population of a city  
- Stores all data in **Elasticsearch**  
- Containerized with **Docker**  
- Deployable with **Helm** on Kubernetes  
- Automated Docker image build & push via **GitHub Actions**  

---

## Project Structure

```
city-population-app/
├── README.md
├── app
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
└── helm-chart
    ├── Chart.yaml
    ├── templates
    │   ├── app-deployment.yaml
    │   ├── app-service.yaml
    │   ├── elasticsearch-configmap.yaml
    │   ├── elasticsearch-deployment.yaml
    │   ├── elasticsearch-networkpolicy.yaml
    │   ├── elasticsearch-service.yaml
    │   ├── namespace.yaml
    │   └── secret.yaml
    └── values.yaml
```

---

## Prerequisites

- Kubernetes cluster (local: Minikube / kind / remote cluster)  
- `kubectl` CLI  
- `git`  
- Helm 3  
- GitHub repository with **GHCR** enabled  

---

## Build and Push Docker Image

GitHub Actions automatically builds and pushes the Docker image to GHCR whenever changes occur in:

- `app/**`
- `helm-chart/**`
- `Dockerfile`

---

## Deploy to Kubernetes with Helm

1. Clone the repository:

```bash
git clone https://github.com/ahmedovelshan/city-population-app.git
cd city-population-app
```

2. ### Deploying the Application

#### Deploy without persistence (default)

```bash
helm upgrade --install city-population ./helm-chart   --set namespace.name=default   --set elasticsearch.persistence=false
```

> ⚠️ Data will not persist if pods are restarted.

#### Deploy with persistent storage (using StorageClass)

```bash
helm upgrade --install city-population ./helm-chart   --set namespace.name=default   --set elasticsearch.persistence.enabled=true   --set elasticsearch.persistence.storageClass=<your-storage-class>   --set elasticsearch.persistence.size=10Gi
```

> Replace `<your-storage-class>` with a valid StorageClass in your cluster.

#### Deploy with custom Elasticsearch credentials

```bash
helm upgrade --install city-population ./helm-chart   --set namespace.name=default   --set elasticsearch.persistence.enabled=true   --set elasticsearch.persistence.storageClass=<your-storage-class>   --set elasticsearch.persistence.size=10Gi   --set elasticsearch.username=<your-username>   --set elasticsearch.password=<your-password>
```

> By default, the app uses credentials `elastic / password`.

3. Verify pods and services:

```bash
kubectl get pods
kubectl get svc
```

---

## Testing the Application Inside Kubernetes

Start a debug pod:

```bash
kubectl run -it debug --image=curlimages/curl --restart=Never -- sh
```

Run the API requests from the debug pod:

```bash
# Health check
curl http://city-populations:5000/health

# Query city population
curl http://city-populations:5000/city/London

# Upsert a new city
curl -X POST http://city-populations:5000/city   -H "Content-Type: application/json"   -d '{"city": "Rome", "population": 2873000}'

# Verify the new city
curl http://city-populations:5000/city/Rome
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

- Flask app communicates with Elasticsearch via the Kubernetes service: `elasticsearch:9200`  
- The Helm chart deploys both pods and services together.

---

## Helm Chart Notes

- The Flask app automatically connects to Elasticsearch using the Kubernetes service URL.  

---

## Reflection

- **Challenges:** Handling Elasticsearch connection at pod startup, pre-populating initial city data, and ensuring Helm values are configurable for storage and credentials.  
- **Scaling suggestions:** Use an HA Elasticsearch cluster, add monitoring (Prometheus/Grafana), implement security hardening, and use persistent storage for production environments.  

---

## License

MIT License
