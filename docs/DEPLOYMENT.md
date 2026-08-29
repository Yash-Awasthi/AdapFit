# AdapFit Deployment Guide

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your values

# 2. Start all services
docker-compose up -d

# 3. Verify
curl http://localhost:8000/health
curl http://localhost/admin/
```

## Development Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Mobile
cd mobile
npm install
npx expo start
```

## Production Deployment

### AWS (ECS + RDS)
```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name adapfit

# 2. Build and push
docker build -t adapfit .
docker tag adapfit:latest <account>.dkr.ecr.<region>.amazonaws.com/adapfit:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/adapfit:latest

# 3. Create ECS cluster with Fargate
# 4. Create RDS PostgreSQL instance
# 5. Create ElastiCache Redis cluster
# 6. Configure ALB for load balancing
```

### GCP (Cloud Run + Cloud SQL)
```bash
# 1. Build and deploy
gcloud builds submit --tag gcr.io/<project>/adapfit
gcloud run deploy adapfit --image gcr.io/<project>/adapfit --platform managed
```

### Azure (Container Apps + Azure Database)
```bash
# 1. Create Azure Container Registry
az acr create --resource-group adapfit-rg --name adapfit --sku Standard

# 2. Build and push
az acr build --registry adapfit --image adapfit:v1 .
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `JWT_SECRET_KEY` | Secret for JWT signing | Yes |
| `GEMINI_API_KEY` | Google AI API key | No |
| `ENVIRONMENT` | development/staging/production | Yes |
| `LOG_LEVEL` | debug/info/warning/error | No |

## SSL/TLS Setup

```bash
# Generate self-signed cert (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/selfsigned.key \
    -out nginx/selfsigned.crt

# For production: Use Let's Encrypt
certbot certonly --webroot -w /var/www/html -d adapfit.com
```

## Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics`
- **Admin Dashboard**: `GET /admin/`
- **API Docs**: `GET /docs`
- **OpenAPI Schema**: `GET /api/v1/openapi.json`

## Database Migrations

```bash
# Initialize database
python backend/app/scripts/init_db.py

# Or use Docker
docker-compose exec backend python /app/backend/app/scripts/init_db.py
```

## Scaling

```bash
# Horizontal scaling with docker-compose
docker-compose up -d --scale backend=3

# Or use Kubernetes
kubectl scale deployment adapfit-backend --replicas=3
```
