# Kubernetes Plan

## Goal

Kubernetes should be used to demonstrate scalability and production-oriented deployment. It should not be implemented before the core product works.

Kubernetes is an advanced phase, not the starting point.

## When to Start Kubernetes

Start Kubernetes after:

- backend API works;
- frontend works;
- database works;
- webhooks are processed;
- incidents are created;
- logs are downloaded;
- AI analysis works;
- background workers exist;
- Docker Compose works.

## Components to Deploy

Initial Kubernetes components:

```text
frontend
api
analysis-worker
llm-gateway
notification-service
postgres
redis or rabbitmq
prometheus
grafana
```

If the project remains a modular monolith, deploy:

```text
frontend
api
worker
postgres
redis or rabbitmq
prometheus
grafana
```

## Kubernetes Objects

Use:

```text
Deployment
Service
ConfigMap
Secret
Ingress
PersistentVolumeClaim
HorizontalPodAutoscaler
ServiceAccount
```

## Recommended Folder Structure

```text
infrastructure/kubernetes/
  base/
    frontend-deployment.yaml
    api-deployment.yaml
    worker-deployment.yaml
    postgres.yaml
    redis.yaml
    configmap.yaml
    secrets.example.yaml
  observability/
    prometheus.yaml
    grafana.yaml
  overlays/
    local/
    production-like/
```

## Health Checks

Every service should expose:

```text
/health
/ready
```

Use:

- liveness probe;
- readiness probe.

## Autoscaling

Best candidate for autoscaling:

```text
analysis-worker
```

Reason:

AI analysis and log processing are background workloads and may increase when many builds fail.

Possible scaling signals:

- CPU;
- queue length;
- custom metrics later.

## Resource Limits

Set resource requests and limits.

Example components:

```text
api
worker
llm-gateway
notification-service
```

## Secrets

Do not commit real secrets.

Use Kubernetes Secrets for:

```text
database password
GitHub client secret
GitHub webhook secret
GitHub App private key
OpenAI API key
Anthropic API key
Gemini API key
```

Commit only example files:

```text
secrets.example.yaml
```

## ConfigMaps

Use ConfigMaps for:

```text
environment name
log level
API URLs
feature flags
provider configuration names
```

## Local Kubernetes

Recommended local options:

```text
kind
minikube
Docker Desktop Kubernetes
```

## Dissertation Demo

A good Kubernetes demo:

1. Run local cluster.
2. Deploy API, frontend, worker, database, queue.
3. Send multiple fake failed workflow events.
4. Show queue length increasing.
5. Show analysis worker scaling.
6. Show Grafana dashboard metrics.

## Risks

### Risk: Too Much Time Spent on Kubernetes

Mitigation:

- implement Kubernetes after product core works;
- keep manifests simple;
- use local cluster only if needed.

### Risk: Database Complexity

Mitigation:

- use managed or local PostgreSQL for demo;
- avoid spending too much time on production-grade database operations.

### Risk: Secrets Mismanagement

Mitigation:

- use example secret files only;
- document required values;
- never commit real credentials.

## Minimum Kubernetes Deliverable

For dissertation, minimum useful Kubernetes deliverable:

- frontend deployment;
- API deployment;
- worker deployment;
- PostgreSQL;
- Redis or RabbitMQ;
- health checks;
- HPA for worker;
- Prometheus metrics scraping;
- Grafana dashboard.

This is enough to demonstrate scalability and observability.
