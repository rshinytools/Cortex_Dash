# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Clinical Dashboard Platform in various environments, from development to production. It covers containerization, orchestration, infrastructure provisioning, and operational best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment](#production-deployment)
5. [Container Orchestration](#container-orchestration)
6. [Infrastructure as Code](#infrastructure-as-code)
7. [CI/CD Pipelines](#cicd-pipelines)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Security Configuration](#security-configuration)
10. [Backup and Recovery](#backup-and-recovery)
11. [Scaling and Performance](#scaling-and-performance)
12. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 100GB SSD
- Network: 1Gbps

**Recommended for Production:**
- CPU: 8+ cores
- RAM: 32GB+
- Storage: 500GB+ NVMe SSD
- Network: 10Gbps

### Required Software

```bash
# Essential tools
docker >= 20.10.0
docker-compose >= 2.0.0
kubectl >= 1.24.0
helm >= 3.8.0
terraform >= 1.0.0

# Optional but recommended
ansible >= 5.0.0
prometheus
grafana
elasticsearch
```

### Environment Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

## Development Deployment

### Local Development Setup

**Docker Compose Configuration:**

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: cortex_dash_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:dev_password@postgres:5432/cortex_dash_dev
      REDIS_URL: redis://redis:6379
      SECRET_KEY: dev-secret-key-change-in-production
      DEBUG: "true"
    volumes:
      - ./backend:/app
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
      NEXT_PUBLIC_WS_URL: ws://localhost:8000/ws
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: npm run dev

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    environment:
      DATABASE_URL: postgresql://postgres:dev_password@postgres:5432/cortex_dash_dev
      REDIS_URL: redis://redis:6379
      SECRET_KEY: dev-secret-key-change-in-production
    volumes:
      - ./backend:/app
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    command: celery -A app.core.celery_app worker --loglevel=info

volumes:
  postgres_data:
  redis_data:
```

**Development Scripts:**

```bash
#!/bin/bash
# scripts/dev-setup.sh

set -e

echo "Setting up development environment..."

# Create environment file
cp .env.example .env.dev
echo "Created .env.dev file"

# Build and start services
docker-compose -f docker-compose.dev.yml up --build -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Run database migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Load sample data
docker-compose -f docker-compose.dev.yml exec backend python scripts/load_sample_data.py

echo "Development environment ready!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
```

### Hot Reload Configuration

```dockerfile
# backend/Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install development dependencies
RUN pip install watchdog[watchmedo]

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

```dockerfile
# frontend/Dockerfile.dev
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

## Staging Deployment

### Staging Environment Configuration

```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - backend

  backend:
    image: cortex-dash/backend:${IMAGE_TAG}
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET: ${JWT_SECRET}
      ENVIRONMENT: staging
    volumes:
      - app_data:/app/data
    restart: unless-stopped
    networks:
      - backend
      - frontend
    depends_on:
      - postgres
      - redis

  frontend:
    image: cortex-dash/frontend:${IMAGE_TAG}
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
      NEXT_PUBLIC_WS_URL: ${WS_URL}
    restart: unless-stopped
    networks:
      - frontend
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    restart: unless-stopped
    networks:
      - frontend
    depends_on:
      - frontend

  celery:
    image: cortex-dash/backend:${IMAGE_TAG}
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
    volumes:
      - app_data:/app/data
    command: celery -A app.core.celery_app worker --loglevel=info
    restart: unless-stopped
    networks:
      - backend
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
  app_data:

networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge
```

### Staging Environment Variables

```bash
# .env.staging
POSTGRES_DB=cortex_dash_staging
POSTGRES_USER=cortex_user
POSTGRES_PASSWORD=secure_staging_password
REDIS_PASSWORD=redis_staging_password
SECRET_KEY=staging-secret-key-64-chars-long
JWT_SECRET=jwt-staging-secret-key
IMAGE_TAG=staging-latest
API_URL=https://staging-api.cortexdash.com/api/v1
WS_URL=wss://staging-api.cortexdash.com/ws
```

### Nginx Configuration

```nginx
# nginx/staging.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name staging.cortexdash.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name staging.cortexdash.com;

        ssl_certificate /etc/nginx/ssl/staging.crt;
        ssl_certificate_key /etc/nginx/ssl/staging.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        client_max_body_size 100M;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## Production Deployment

### Production Architecture

```mermaid
graph TB
    LB[Load Balancer] --> WAF[Web Application Firewall]
    WAF --> CDN[Content Delivery Network]
    CDN --> RP[Reverse Proxy]
    
    RP --> FE1[Frontend Instance 1]
    RP --> FE2[Frontend Instance 2]
    RP --> FE3[Frontend Instance 3]
    
    RP --> BE1[Backend Instance 1]
    RP --> BE2[Backend Instance 2]
    RP --> BE3[Backend Instance 3]
    
    BE1 --> DB[(Primary DB)]
    BE2 --> DB
    BE3 --> DB
    
    DB --> DBR[(Read Replica)]
    
    BE1 --> Cache[Redis Cluster]
    BE2 --> Cache
    BE3 --> Cache
    
    BE1 --> Q[Message Queue]
    BE2 --> Q
    BE3 --> Q
    
    Q --> W1[Worker 1]
    Q --> W2[Worker 2]
    Q --> W3[Worker 3]
```

### Docker Production Images

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash cortex

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder
COPY --from=builder /root/.local /home/cortex/.local

# Copy application code
COPY --chown=cortex:cortex . .

# Create data directory
RUN mkdir -p /app/data && chown cortex:cortex /app/data

USER cortex

# Make sure scripts in .local are usable
ENV PATH=/home/cortex/.local/bin:$PATH

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
```

### Production Compose Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres-primary:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_REPLICATION_USER: ${POSTGRES_REPLICATION_USER}
      POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
    volumes:
      - postgres_primary_data:/var/lib/postgresql/data
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/pg_hba.conf:/etc/postgresql/pg_hba.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    networks:
      - backend
    restart: unless-stopped

  postgres-replica:
    image: postgres:15-alpine
    environment:
      PGUSER: ${POSTGRES_REPLICATION_USER}
      POSTGRES_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
      POSTGRES_MASTER_SERVICE: postgres-primary
    volumes:
      - postgres_replica_data:/var/lib/postgresql/data
    networks:
      - backend
    restart: unless-stopped
    depends_on:
      - postgres-primary

  redis-cluster:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000 --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - backend
    restart: unless-stopped

  backend:
    image: cortex-dash/backend:${IMAGE_TAG}
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-primary:5432/${POSTGRES_DB}
      DATABASE_READ_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-replica:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis-cluster:6379
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET: ${JWT_SECRET}
      ENVIRONMENT: production
      WORKERS: 4
    volumes:
      - app_data:/app/data
    networks:
      - backend
      - frontend
    restart: unless-stopped
    depends_on:
      - postgres-primary
      - redis-cluster
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  frontend:
    image: cortex-dash/frontend:${IMAGE_TAG}
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
      NEXT_PUBLIC_WS_URL: ${WS_URL}
    networks:
      - frontend
    restart: unless-stopped
    depends_on:
      - backend
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  celery-worker:
    image: cortex-dash/backend:${IMAGE_TAG}
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-primary:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis-cluster:6379
    volumes:
      - app_data:/app/data
    command: celery -A app.core.celery_app worker --loglevel=info --concurrency=4
    networks:
      - backend
    restart: unless-stopped
    depends_on:
      - postgres-primary
      - redis-cluster
    deploy:
      replicas: 3

  celery-beat:
    image: cortex-dash/backend:${IMAGE_TAG}
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres-primary:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis-cluster:6379
    command: celery -A app.core.celery_app beat --loglevel=info
    networks:
      - backend
    restart: unless-stopped
    depends_on:
      - postgres-primary
      - redis-cluster
    deploy:
      replicas: 1

volumes:
  postgres_primary_data:
  postgres_replica_data:
  redis_data:
  app_data:

networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge
```

## Container Orchestration

### Kubernetes Deployment

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cortex-dash
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cortex-config
  namespace: cortex-dash
data:
  ENVIRONMENT: "production"
  POSTGRES_DB: "cortex_dash_prod"
  POSTGRES_USER: "cortex_user"
---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cortex-secrets
  namespace: cortex-dash
type: Opaque
data:
  POSTGRES_PASSWORD: <base64-encoded-password>
  REDIS_PASSWORD: <base64-encoded-password>
  SECRET_KEY: <base64-encoded-secret>
  JWT_SECRET: <base64-encoded-jwt-secret>
---
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: cortex-dash
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: cortex-config
              key: POSTGRES_DB
        - name: POSTGRES_USER
          valueFrom:
            configMapKeyRef:
              name: cortex-config
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: cortex-secrets
              key: POSTGRES_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: cortex-dash
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
---
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: cortex-dash
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: cortex-dash/backend:latest
        env:
        - name: DATABASE_URL
          value: "postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@postgres:5432/$(POSTGRES_DB)"
        - name: POSTGRES_USER
          valueFrom:
            configMapKeyRef:
              name: cortex-config
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: cortex-secrets
              key: POSTGRES_PASSWORD
        - name: POSTGRES_DB
          valueFrom:
            configMapKeyRef:
              name: cortex-config
              key: POSTGRES_DB
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: cortex-secrets
              key: SECRET_KEY
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: cortex-dash
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
---
# k8s/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: cortex-dash
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: cortex-dash/frontend:latest
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "https://api.cortexdash.com/api/v1"
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: cortex-dash
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
    targetPort: 3000
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cortex-ingress
  namespace: cortex-dash
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - cortexdash.com
    - api.cortexdash.com
    secretName: cortex-tls
  rules:
  - host: cortexdash.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
  - host: api.cortexdash.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

### Helm Chart

```yaml
# helm/cortex-dash/Chart.yaml
apiVersion: v2
name: cortex-dash
description: A Helm chart for Cortex Dashboard Platform
type: application
version: 1.0.0
appVersion: "1.0.0"
---
# helm/cortex-dash/values.yaml
replicaCount:
  backend: 3
  frontend: 3
  workers: 3

image:
  backend:
    repository: cortex-dash/backend
    tag: "latest"
    pullPolicy: IfNotPresent
  frontend:
    repository: cortex-dash/frontend
    tag: "latest"
    pullPolicy: IfNotPresent

service:
  type: ClusterIP
  backend:
    port: 8000
  frontend:
    port: 3000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: cortexdash.com
      paths:
        - path: /
          pathType: Prefix
          service: frontend
    - host: api.cortexdash.com
      paths:
        - path: /
          pathType: Prefix
          service: backend
  tls:
    - secretName: cortex-tls
      hosts:
        - cortexdash.com
        - api.cortexdash.com

postgresql:
  enabled: true
  auth:
    postgresPassword: "change-me"
    database: "cortex_dash"
  primary:
    persistence:
      size: 100Gi

redis:
  enabled: true
  auth:
    password: "change-me"
  master:
    persistence:
      size: 10Gi

resources:
  backend:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1"
  frontend:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

nodeSelector: {}
tolerations: []
affinity: {}
```

## Infrastructure as Code

### Terraform Configuration

```hcl
# terraform/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.16"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.8"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${var.environment}-cortex-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = true

  tags = {
    Environment = var.environment
    Project     = "cortex-dash"
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"

  cluster_name    = "${var.environment}-cortex-cluster"
  cluster_version = "1.24"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    main = {
      min_size     = 3
      max_size     = 10
      desired_size = 6

      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"

      tags = {
        Environment = var.environment
        Project     = "cortex-dash"
      }
    }
  }

  tags = {
    Environment = var.environment
    Project     = "cortex-dash"
  }
}

# RDS Database
resource "aws_db_subnet_group" "cortex" {
  name       = "${var.environment}-cortex-db-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name        = "${var.environment}-cortex-db-subnet"
    Environment = var.environment
  }
}

resource "aws_db_instance" "cortex" {
  identifier = "${var.environment}-cortex-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.large"

  allocated_storage     = 100
  max_allocated_storage = 1000
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "cortex_dash"
  username = "cortex_user"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.cortex.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "${var.environment}-cortex-db-final-snapshot"

  tags = {
    Name        = "${var.environment}-cortex-db"
    Environment = var.environment
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "cortex" {
  name       = "${var.environment}-cortex-cache-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_replication_group" "cortex" {
  description          = "${var.environment} Cortex Redis cluster"
  replication_group_id = "${var.environment}-cortex-redis"

  node_type            = "cache.r6g.large"
  port                 = 6379
  parameter_group_name = "default.redis7"

  num_cache_clusters = 3
  subnet_group_name  = aws_elasticache_subnet_group.cortex.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token

  tags = {
    Name        = "${var.environment}-cortex-redis"
    Environment = var.environment
  }
}

# Security Groups
resource "aws_security_group" "rds" {
  name_prefix = "${var.environment}-cortex-rds-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-cortex-rds-sg"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.environment}-cortex-redis-"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-cortex-redis-sg"
  }
}
```

```hcl
# terraform/variables.tf
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "redis_auth_token" {
  description = "Redis authentication token"
  type        = string
  sensitive   = true
}
```

## CI/CD Pipelines

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy Cortex Dashboard

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Run backend tests
      run: |
        cd backend
        pytest

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'

    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci

    - name: Run frontend tests
      run: |
        cd frontend
        npm test

    - name: Build frontend
      run: |
        cd frontend
        npm run build

  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-

    - name: Build and push backend image
      uses: docker/build-push-action@v5
      with:
        context: ./backend
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/backend:${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

    - name: Build and push frontend image
      uses: docker/build-push-action@v5
      with:
        context: ./frontend
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/frontend:${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    needs: build
    runs-on: ubuntu-latest
    environment: staging

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Add your deployment commands here

  deploy-production:
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment: production

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to production
      run: |
        echo "Deploying to production environment"
        # Add your deployment commands here
```

### GitLab CI/CD Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

test:backend:
  stage: test
  image: python:3.11
  services:
    - postgres:15
  variables:
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/test_db
  before_script:
    - cd backend
    - pip install -r requirements.txt
  script:
    - pytest
  coverage: '/TOTAL.+?(\d+\%)$/'

test:frontend:
  stage: test
  image: node:18
  before_script:
    - cd frontend
    - npm ci
  script:
    - npm test
    - npm run build

build:backend:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA ./backend
    - docker push $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA

build:frontend:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA ./frontend
    - docker push $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA

deploy:staging:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/backend backend=$CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
    - kubectl set image deployment/frontend frontend=$CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
  environment:
    name: staging
    url: https://staging.cortexdash.com
  only:
    - develop

deploy:production:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/backend backend=$CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
    - kubectl set image deployment/frontend frontend=$CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
  environment:
    name: production
    url: https://cortexdash.com
  only:
    - main
  when: manual
```

## Monitoring and Logging

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'cortex-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'cortex-frontend'
    static_configs:
      - targets: ['frontend:3000']
    metrics_path: '/api/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Cortex Dashboard Platform",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "active_sessions_total",
            "legendFormat": "Active Sessions"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "postgres_stat_database_numbackends",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack Configuration

```yaml
# logging/elasticsearch.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

## Security Configuration

### SSL/TLS Configuration

```nginx
# nginx/ssl.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

ssl_stapling on;
ssl_stapling_verify on;

add_header Strict-Transport-Security "max-age=63072000" always;
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### Security Headers

```python
# backend/app/middleware/security.py
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
```

## Backup and Recovery

### Database Backup Script

```bash
#!/bin/bash
# scripts/backup-database.sh

set -e

# Configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-cortex_dash}
DB_USER=${DB_USER:-postgres}
BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-7}

# Create backup directory
mkdir -p $BACKUP_DIR

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/cortex_dash_$TIMESTAMP.sql"

# Create backup
echo "Creating database backup..."
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

echo "Backup created: ${BACKUP_FILE}.gz"

# Clean up old backups
find $BACKUP_DIR -name "cortex_dash_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully"
```

### Disaster Recovery Plan

```bash
#!/bin/bash
# scripts/disaster-recovery.sh

set -e

BACKUP_FILE=$1
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-cortex_dash}
DB_USER=${DB_USER:-postgres}

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Starting disaster recovery..."

# Stop application services
docker-compose down

# Restore database
echo "Restoring database from $BACKUP_FILE..."
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
else
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $BACKUP_FILE
fi

# Start services
docker-compose up -d

echo "Disaster recovery completed"
```

## Scaling and Performance

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: cortex-dash
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
  namespace: cortex-dash
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Performance Optimization

```python
# backend/app/core/performance.py
import asyncio
from functools import wraps
from typing import Optional
import redis
import json

# Redis connection pool
redis_pool = redis.ConnectionPool(
    host='redis',
    port=6379,
    decode_responses=True,
    max_connections=20
)

def cache_result(ttl: int = 300, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            r = redis.Redis(connection_pool=redis_pool)
            cached = r.get(cache_key)
            
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            r.setex(cache_key, ttl, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator

# Connection pooling for database
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

## Troubleshooting

### Common Issues and Solutions

**Issue: Container fails to start**
```bash
# Check container logs
docker logs <container_name>

# Check container configuration
docker inspect <container_name>

# Check resource usage
docker stats
```

**Issue: Database connection errors**
```bash
# Test database connectivity
psql -h <host> -p <port> -U <user> -d <database>

# Check database status
pg_isready -h <host> -p <port>

# Check connection limits
SELECT * FROM pg_stat_activity;
```

**Issue: High memory usage**
```bash
# Check memory usage by container
docker stats --no-stream

# Check system memory
free -h

# Check for memory leaks
valgrind --tool=memcheck --leak-check=full <command>
```

### Health Check Scripts

```bash
#!/bin/bash
# scripts/health-check.sh

# API health check
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $API_STATUS != "200" ]; then
    echo "API health check failed: $API_STATUS"
    exit 1
fi

# Database health check
DB_STATUS=$(pg_isready -h localhost -p 5432 -U postgres)
if [ $? != 0 ]; then
    echo "Database health check failed: $DB_STATUS"
    exit 1
fi

# Redis health check
REDIS_STATUS=$(redis-cli ping)
if [ "$REDIS_STATUS" != "PONG" ]; then
    echo "Redis health check failed"
    exit 1
fi

echo "All health checks passed"
```

---

## Quick Reference

### Deployment Commands
```bash
# Development
docker-compose -f docker-compose.dev.yml up --build

# Staging
docker-compose -f docker-compose.staging.yml up -d

# Production
helm install cortex-dash ./helm/cortex-dash -f values.prod.yaml

# Kubernetes
kubectl apply -f k8s/
```

### Monitoring URLs
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090
- Kibana: http://localhost:5601

### Emergency Procedures
1. **Scale down**: `kubectl scale deployment backend --replicas=0`
2. **Database backup**: `./scripts/backup-database.sh`
3. **Rollback**: `helm rollback cortex-dash <revision>`

---

*This deployment guide provides comprehensive coverage of deployment scenarios. For specific cloud provider configurations or advanced orchestration setups, consult the respective platform documentation.*