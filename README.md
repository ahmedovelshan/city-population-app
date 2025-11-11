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
├── README.md
├── app
│ ├── Dockerfile
│ ├── app.py
│ └── requirements.txt
└── helm-chart
    ├── Chart.yaml
    ├── templates
    │ ├── app-deployment.yaml
    │ ├── app-service.yaml
    │ ├── elasticsearch-configmap.yaml
    │ ├── elasticsearch-deployment.yaml
    │ ├── elasticsearch-networkpolicy.yaml
    │ ├── elasticsearch-service.yaml
    │ ├── namespace.yaml
    │ └── secret.yaml
    └── values.yaml
```

---

## Prerequisites

- Kubernetes cluster (local: Minikube / kind / remote cluster) 
- kubectl
- git 
- Helm 3  
- GitHub repository with GHCR enabled  

---

## Build and Push Docker Image

GitHub Actions automatically builds and pushes the Docker image to GHCR whenever changes occur in the following:

```
app/**
```

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
Data will not persist if pods are restarted.

#### Deploy with persistent storage (using StorageClass)
```bash
helm upgrade --install city-population ./helm-chart   --set namespace.name=default   --set elasticsearch.persistence.enabled=true   --set elasticsearch.persistence.storageClass=<your-storage-class>   --set elasticsearch.persistence.size=10Gi
```
Replace `<your-storage-class>` with a valid StorageClass in your cluster.

#### Deploy with custom Elasticsearch credentials
```bash
helm upgrade --install city-population ./helm-chart   --set namespace.name=default   --set elasticsearch.persistence.enabled=true   --set elasticsearch.persistence.storageClass=<your-storage-class>   --set elasticsearch.persistence.size=10Gi   --set elasticsearch.username=<your-username>   --set elasticsearch.password=<your-password>
```
By default, it uses preconfigured credentials (`elastic` / `password`).

---

## Verify Deployment

```bash
kubectl get pods
kubectl get svc
```

---

## Testing Inside Kubernetes

Start a debug pod:
```bash
kubectl run -it debug --image=curlimages/curl --restart=Never -- sh
```

Run the API requests inside the debug pod:
```bash
curl http://city-populations:5000/health
curl http://city-populations:5000/city/London
curl -X POST http://city-populations:5000/city   -H "Content-Type: application/json"   -d '{"city": "Rome", "population": 2873000}'
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
- Flask app communicates with Elasticsearch via the Kubernetes service `elasticsearch:9200`.  
- The Helm chart deploys both pods and services together.

---

## Helm Chart Notes

- Flask app connects automatically to Elasticsearch via Kubernetes service: `http://elasticsearch:9200`  

---

## Reflection

### Challenges Faced
- Ensuring proper connection between the Flask app and Elasticsearch inside Kubernetes.  
- Managing Elasticsearch credentials securely within Helm values and secrets.  
- Handling Elasticsearch readiness and ensuring the app waits until the database is available.  
- Designing a Helm chart flexible enough to support both ephemeral and persistent deployments.  

### Suggestions for Production Scaling
- **High Availability (HA)**: Deploy Elasticsearch as a multi-node cluster using StatefulSets with persistent volumes.  
- **Observability**: Integrate Prometheus and Grafana to monitor application and Elasticsearch performance metrics.  
- **Security Hardening**:  
  - Use Kubernetes Secrets for storing credentials and enable SSL/TLS for communication between services.  
  - Restrict access to Elasticsearch using NetworkPolicies.  
- **Scalability**:  
  - Use Horizontal Pod Autoscaler (HPA) for the Flask app.  
  - Optimize Elasticsearch with appropriate resource requests/limits and shard/replica configurations.  
- **CI/CD Automation**: Integrate Helm deployments with GitHub Actions for automated versioned releases.

---

## License

MIT License
