# Homelab Infrastructure

Production Docker-based infrastructure on Proxmox VMs. All VMs are stateless with Git-managed configs and 1Password secrets.

## Quick Reference

**Network:** VLAN 10 (10.10.10.0/24) | **Gateway:** 10.10.10.1 | **DNS:** AdGuard (10.10.10.110)

| VM | IP | Stack | Status |
|----|-----|-------|--------|
| edge | 10.10.10.110 | Traefik, AdGuard, Authentik, NetBird | ✅ |
| db | 10.10.10.111 | PostgreSQL, MongoDB, Redis, MinIO, Qdrant, ClickHouse, RabbitMQ, Kafka, Mosquitto | ✅ |
| observability | 10.10.10.112 | Portainer, Grafana, Loki, Tempo, Alloy, Glance, Langfuse | ✅ |
| media | 10.10.10.113 | Plex, *arr Stack, Overseerr | ✅ |
| dev | 10.10.10.114 | Gitea (Git + Registry + CI), Hoppscotch, SonarQube, Meilisearch, Inngest | ✅ |
| ai | 10.10.10.115 | LiteLLM, Docling, n8n, Open WebUI | ✅ |
| deploy | 10.10.10.101 | Coolify | ✅ |
| ha | 10.10.10.116 | Home Assistant | ✅ |

**Access:** All services via `https://<service>.onurx.com` (private network only - home + NetBird VPN)

---

## Architecture

### Core Patterns

**Directory Structure:**
```
/opt/homelab/<vm>/
├── docker-compose.yml    # Service definitions
├── .env                  # 1Password refs (op://Server/...)
└── <service>/
    ├── config/           # Committed configs
    └── data/             # Gitignored runtime data
```

**Secrets:** All passwords in 1Password vault "Server"
- `.env` files contain only `op://` references (safe to commit)
- Deploy with: `op run --env-file=.env -- docker compose up -d`

**Git Workflow:**
1. Edit locally in `~/Repositories/homelab/`
2. Commit & push changes
3. Pull on VMs: `ssh fx@IP 'cd /opt/homelab && git pull'`
4. Restart affected services

**Monitoring:**
- Netdata on all VMs (http://IP:19999) - Real-time metrics
- Grafana (https://grafana.onurx.com) - Dashboards + Loki logs
- Portainer (https://portainer.onurx.com) - Container management

**Networking:**
- VLAN 10: All services (10.10.10.0/24)
- NetBird VPN: Remote access (100.92.0.0/16)
- Traefik: Reverse proxy with Cloudflare TLS

---

## Initial Setup

### Creating a New VM

**In Proxmox:**
1. Clone template VM (full clone)
2. Set static IP in Proxmox network settings
3. Start VM

**On VM (first boot):**
```bash
# Set hostname
sudo hostnamectl set-hostname <vm-name>

# Set 1Password token (for all sessions including SSH)
echo 'OP_SERVICE_ACCOUNT_TOKEN="ops_xxx"' | sudo tee -a /etc/environment

# Re-login to load environment
exit  # then SSH back in

# Test 1Password
op vault list

# Clone repository
git clone https://git.onurx.com/fx/homelab.git /opt/homelab
cd /opt/homelab/<vm-name>

# Deploy services
op run --env-file=.env -- docker compose up -d
```

### VM Template Setup

Template includes:
- Debian 12 with Docker + Docker Compose
- User: `fx` (sudo access)
- SSH key authentication
- Static network config (edited per VM in Proxmox)

---

## Service Deployment

### Standard Deployment

```bash
# Navigate to VM directory
cd /opt/homelab/<vm-name>

# Deploy all services
op run --env-file=.env -- docker compose up -d

# Deploy specific service
op run --env-file=.env -- docker compose up -d <service>

# View logs
docker compose logs -f <service>

# Check status
docker compose ps
```

### Update Services

```bash
# Pull latest images
docker compose pull

# Recreate with new config/images
op run --env-file=.env -- docker compose up -d

# Or specific service
docker compose pull <service>
op run --env-file=.env -- docker compose up -d <service>
```

### Complete Service Reinstall

```bash
# Stop and remove (including volumes)
docker compose down <service> -v

# Remove bind mount data
sudo rm -rf <service>/data/*

# Clean database if used
# PostgreSQL: docker exec postgres psql -U postgres -c "DROP DATABASE dbname;"
# MongoDB: docker exec mongodb mongosh --eval "use dbname; db.dropDatabase();"

# Redeploy
docker compose pull <service>
op run --env-file=.env -- docker compose up -d <service>

# Clean up
docker system prune -f
```

---

## Key Services

### Edge Stack (10.10.10.110)

**Traefik** - Reverse proxy + TLS
- Routes: `edge/traefik/config/dynamic/routers.yml`
- Services: `edge/traefik/config/dynamic/services.yml`
- Middlewares: `edge/traefik/config/dynamic/middlewares.yml`
- Security: `private-default` (home + VPN) or `public-access`

**AdGuard** - DNS + Ad blocking
- Web UI: https://adguard.onurx.com
- DNS: 10.10.10.110:53
- Rewrites configured for `.onurx.com` domains

**Authentik** - SSO (future integration)
- Web UI: https://auth.onurx.com

**NetBird** - VPN
- Network: 100.92.0.0/16
- Management: https://app.netbird.io

### Database Stack (10.10.10.111)

**PostgreSQL** - SQL databases
- Port: 5432
- Databases: litellm, n8n, langfuse, authentik, gitea

**MongoDB** - Document databases
- Port: 27017
- Databases: glance

**Redis** - Cache + queues
- Port: 6379
- Used by: LiteLLM, n8n, Langfuse

**MinIO** - S3-compatible storage
- Console: https://minio.onurx.com
- API: s3.onurx.com (10.10.10.111:9000)

**Qdrant** - Vector database
- Port: 6333
- Used by: Open WebUI, Mem0

**ClickHouse** - Analytics database
- Port: 9000 (native), 8123 (HTTP)
- Used by: Langfuse v3

**RabbitMQ** - Message broker
- Management: https://rabbitmq.onurx.com
- Port: 5672 (AMQP)

**Kafka** - Event streaming
- Port: 9092

### AI Stack (10.10.10.115)

**LiteLLM** - AI Gateway
- Web UI: https://litellm.onurx.com
- Routes to: OpenAI, Anthropic, etc.
- Observability: Integrated with Langfuse

**Docling** - Document processing
- API: https://docling.onurx.com
- Converts: PDF, Word, Excel, PowerPoint → Text
- Docs: http://10.10.10.115:5000/docs

**n8n** - Workflow automation
- Web UI: https://n8n.onurx.com
- Uses: PostgreSQL (db), Redis (queue)

**Open WebUI** - Chat interface
- Web UI: https://chat.onurx.com
- Backend: LiteLLM
- RAG: Qdrant

**Langfuse** - AI observability (on observability VM)
- Web UI: https://langfuse.onurx.com
- Tracks: LiteLLM API calls
- Storage: PostgreSQL + ClickHouse

### Dev Stack (10.10.10.114)

**Gitea** - Git + Container Registry + CI/CD
- Web UI: https://git.onurx.com
- Registry: https://git.onurx.com (Docker v2 API)

**Hoppscotch** - API testing
- Web UI: https://api.onurx.com

**SonarQube** - Code quality
- Web UI: https://sonar.onurx.com

**Meilisearch** - Search engine
- API: https://search.onurx.com

**Inngest** - Background jobs
- Web UI: https://inngest.onurx.com

### Observability Stack (10.10.10.112)

**Grafana** - Dashboards + logs
- Web UI: https://grafana.onurx.com
- Datasources: Prometheus, Loki, Tempo

**Loki** - Log aggregation
- API: http://10.10.10.112:3100

**Tempo** - Distributed tracing
- gRPC: 10.10.10.112:4317
- HTTP: 10.10.10.112:4318

**Alloy** - Metrics + logs collector
- Deployed on all VMs
- Sends to: Prometheus (metrics), Loki (logs)

**Portainer** - Container management
- Web UI: https://portainer.onurx.com
- Agents on: edge, db, dev, media, ai, deploy VMs

**Glance** - Homelab dashboard
- Web UI: https://home.onurx.com
- Overview of all services

---

## Management Interfaces

All services accessible via `https://<service>.onurx.com` (private network only):

**Infrastructure:**
- Proxmox: https://proxmox.onurx.com (10.10.10.20:8006)
- Synology: https://synology.onurx.com (10.10.10.116:5001)
- Portainer: https://portainer.onurx.com
- Traefik: https://traefik.onurx.com
- AdGuard: https://adguard.onurx.com
- Home: https://home.onurx.com (Glance)

**Observability:**
- Grafana: https://grafana.onurx.com
- Langfuse: https://langfuse.onurx.com

**Development:**
- Git: https://git.onurx.com (Gitea)
- API: https://api.onurx.com (Hoppscotch)
- Sonar: https://sonar.onurx.com
- Deploy: https://deploy.onurx.com (Coolify)

**AI Services:**
- LiteLLM: https://litellm.onurx.com
- Docling: https://docling.onurx.com
- n8n: https://n8n.onurx.com
- Chat: https://chat.onurx.com (Open WebUI)

**Media:**
- Plex: https://plex.onurx.com
- Overseerr: https://overseerr.onurx.com
- Sonarr: https://sonarr.onurx.com
- Radarr: https://radarr.onurx.com
- Prowlarr: https://prowlarr.onurx.com

**Databases:**
- MinIO: https://minio.onurx.com
- RabbitMQ: https://rabbitmq.onurx.com

**Netdata Nodes:**
- http://10.10.10.110:19999 (edge)
- http://10.10.10.111:19999 (db)
- http://10.10.10.112:19999 (observability)
- http://10.10.10.113:19999 (media)
- http://10.10.10.114:19999 (dev)
- http://10.10.10.115:19999 (ai)
- http://10.10.10.101:19999 (deploy)

---

## Common Operations

### Configuration Changes

```bash
# 1. Edit locally
cd ~/Repositories/homelab/
# Edit files...

# 2. Commit and push
git add .
git commit -m "description"
git push

# 3. Pull on affected VMs
ssh fx@10.10.10.XXX 'cd /opt/homelab && git pull'

# 4. Restart services
ssh fx@10.10.10.XXX 'cd /opt/homelab/<vm> && op run --env-file=.env -- docker compose up -d <service>'
```

### Adding Traefik Routes

1. Add service backend in `edge/traefik/config/dynamic/services.yml`:
```yaml
service-name:
  loadBalancer:
    servers:
      - url: "http://10.10.10.XXX:PORT"
```

2. Add route in `edge/traefik/config/dynamic/routers.yml`:
```yaml
service-name:
  rule: "Host(`service.onurx.com`)"
  entryPoints:
    - websecure
  service: service-name
  middlewares:
    - private-default  # or public-access
  tls:
    certResolver: cloudflare
```

3. Deploy changes:
```bash
git add edge/traefik/config/dynamic/
git commit -m "Add <service> route"
git push
ssh fx@10.10.10.110 'cd /opt/homelab && git pull && cd edge && docker compose restart traefik'
```

### Managing Secrets

```bash
# List vault items
op item list --vault Server

# Read secret
op read "op://Server/item-name/field"

# Add new secret to 1Password first, then reference in .env
echo 'SERVICE_PASSWORD=op://Server/item/password' >> .env
```

### Database Operations

**PostgreSQL:**
```bash
# Create database
docker exec postgres psql -U postgres -c "CREATE DATABASE dbname;"

# Create user
docker exec postgres psql -U postgres -c "CREATE USER username WITH PASSWORD 'password';"

# Grant permissions
docker exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE dbname TO username;"
docker exec postgres psql -U postgres -d dbname -c "GRANT ALL ON SCHEMA public TO username;"

# Backup
docker exec postgres pg_dump -U postgres dbname > backup.sql

# Restore
docker exec -i postgres psql -U postgres dbname < backup.sql
```

**MongoDB:**
```bash
# Create database & user
docker exec mongodb mongosh <<EOF
use dbname
db.createUser({
  user: "username",
  pwd: "password",
  roles: [{role: "readWrite", db: "dbname"}]
})
EOF

# Backup
docker exec mongodb mongodump --db=dbname --out=/dump
docker cp mongodb:/dump ./backup

# Restore
docker cp ./backup mongodb:/restore
docker exec mongodb mongorestore --db=dbname /restore/dbname
```

### Container Maintenance

```bash
# View logs (last 100 lines, follow)
docker compose logs -f --tail=100 <service>

# Restart service
docker compose restart <service>

# Rebuild service
docker compose up -d --force-recreate <service>

# Remove old images
docker image prune -a

# Full cleanup
docker system prune -a --volumes  # CAREFUL: removes unused volumes
```

---

## Troubleshooting

### 1Password Issues

```bash
# Verify token set
echo $OP_SERVICE_ACCOUNT_TOKEN

# Test connection
op vault list

# Test secret retrieval
op read "op://Server/mongodb/username"

# If not working after setting in /etc/environment
# Log out and back in, or:
sudo -i bash -c 'source /etc/environment && su - fx'
```

### Network Connectivity

```bash
# Test database ports
nc -zv 10.10.10.111 5432     # PostgreSQL
nc -zv 10.10.10.111 27017    # MongoDB
nc -zv 10.10.10.111 6379     # Redis
nc -zv 10.10.10.111 9000     # MinIO

# Check Traefik routing
curl -k https://service.onurx.com/health
```

### Container Issues

```bash
# Check if port in use
sudo netstat -tulpn | grep <port>

# View full container logs
docker logs <container> --tail 200

# Check container health
docker ps --filter health=unhealthy

# Inspect container
docker inspect <container>

# Check resource usage
docker stats

# Restart stuck container
docker restart <container>
```

### Service-Specific Issues

**LiteLLM unhealthy:**
- Healthcheck expects GET /health/readiness (not HEAD /health)
- Functionally working, just healthcheck misconfigured

**Open WebUI unhealthy:**
- Similar healthcheck issue
- Service functional

**Docling unhealthy:**
- May show unhealthy during ML model loading (first ~60s)
- Check logs: `docker logs docling`

**Langfuse unhealthy:**
- ClickHouse initialization may take time on first start
- Verify PostgreSQL and ClickHouse are running

---

## Deployment Status

### ✅ Completed Infrastructure

**Edge Services:**
- Traefik (reverse proxy)
- AdGuard (DNS)
- Authentik (SSO) - configured but not integrated
- NetBird (VPN)

**Database Services:**
- PostgreSQL, MongoDB, Redis
- MinIO, RabbitMQ, Kafka, Mosquitto
- Qdrant, ClickHouse

**Observability:**
- Portainer, Grafana, Loki, Tempo, Alloy
- Netdata on all VMs
- Glance dashboard

**AI Infrastructure:**
- LiteLLM (AI gateway)
- Langfuse (AI observability)
- Docling (document processing)
- n8n (workflow automation)
- Open WebUI (chat interface)
- LiteLLM → Langfuse integration configured

**Development:**
- Gitea (git + container registry + CI/CD)
- Hoppscotch, SonarQube, Meilisearch, Inngest

**Media Stack:**
- Plex, Sonarr, Radarr, Prowlarr, Overseerr
- SABnzbd, qBittorrent, Bazarr, Tautulli

**Deployment:**
- Coolify platform

### 📝 Known Issues (Non-Critical)

**Healthcheck Failures:**
- LiteLLM, Open WebUI, Docling, Langfuse show unhealthy
- Services are functional, just healthcheck configs need adjustment
- Does not impact operation

### 🔮 Future Enhancements

**Short-term:**
- Fix healthcheck configurations
- Generate proper Langfuse API keys for observability
- Deploy Alloy to media/dev VMs for complete monitoring coverage

**Long-term:**
- Integrate Authentik SSO across services
- Add PostgreSQL/MongoDB exporters for detailed metrics
- Implement centralized alerting via Alertmanager
- Add Home Assistant integration with Traefik

---

## Important Notes

**Security:**
- All services private by default (home network + NetBird VPN only)
- Explicit `public-access` middleware required for internet exposure
- TLS certificates auto-managed by Traefik + Cloudflare
- Never commit actual secrets to git

**Backups:**
- Proxmox VM backups: Proxmox Backup Server (VM 120)
- Database backups: Configure per service
- Git repository: Source of truth for configs

**Performance:**
- Netdata provides real-time metrics (1-second granularity)
- Prometheus disabled in favor of Netdata for system metrics
- Alloy still collects logs for Loki

**Documentation:**
- This README is the single source of truth
- CLAUDE.md contains instructions for AI assistants
- No other documentation files maintained

---

**Last Updated:** 2025-11-13 | **Version:** 2.0
