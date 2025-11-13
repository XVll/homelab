# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Documentation Strategy

**SINGLE SOURCE OF TRUTH: README.md ONLY**

1. **NEVER create new .md files** for documentation, notes, or deployment instructions
2. **ALWAYS update README.md** when:
   - A service is deployed or configured
   - Important decisions are made
   - Quick reference notes are needed
   - Progress needs to be tracked
3. **NEVER create files like**:
   - DEPLOY.md, SETUP.md, NOTES.md, INFRASTRUCTURE.md
   - Service-specific docs (ADGUARD-SETUP.md, TRAEFIK-NOTES.md, etc.)
   - Any other markdown files for tracking or documentation

**Exception:**
- `CLAUDE.md` - This file (instructions for Claude)
- `README.md` - Single source of truth (UPDATE THIS)

**When to update README.md:**
- Service deployed → Update "Current Status" section
- New pattern learned → Add to relevant section
- Important command used → Add to "Common Operations"
- Decision made → Update relevant section
- Next steps identified → Update "Critical Action Items"

**Documentation style in README.md:**
- Focused, not stories
- Actionable commands and notes
- "To do X: do Y" format
- Example: "To add Traefik route → edit services.yml + routers.yml"
- Keep it scannable and quick to reference

## Repository Overview

Homelab infrastructure repository managing Docker-based services across multiple Proxmox VMs. All VMs use the same pattern:
- Repository cloned at `/opt/homelab/` on each VM
- Each VM has a subdirectory (e.g., `db/`, `edge/`, `observability/`)
- All VMs are stateless and disposable

## Working Philosophy

**Progressive Development**: Build incrementally, one service at a time. No large dumps of information or code.

**User Control**: Present information, get decisions, implement. User stays in control.

**Decision Tracking**: When decisions are made during implementation:
1. Update affected code immediately
2. Update README.md (NOT separate files)
3. No over-engineering - simple solutions first

## Architecture

### VM Layout

| VM | IP | Directory | Services |
|----|-----|-----------|----------|
| edge | 10.10.10.110 | `/opt/homelab/` | Traefik, AdGuard, Authentik, NetBird |
| db | 10.10.10.111 | `/opt/homelab/` | PostgreSQL, MongoDB, Redis, MinIO, Qdrant, ClickHouse, RabbitMQ, Kafka, Mosquitto |
| observability | 10.10.10.112 | `/opt/homelab/` | Portainer, Grafana, Loki, Tempo, Alloy, Glance, Langfuse |
| media | 10.10.10.113 | `/opt/homelab/` | Plex, Sonarr, Radarr, Prowlarr, SABnzbd, qBittorrent, Bazarr, Overseerr, Tautulli, Notifiarr |
| dev | 10.10.10.114 | `/opt/homelab/` | Gitea (Git + Registry + CI), Hoppscotch, SonarQube, Meilisearch, Inngest |
| ai | 10.10.10.115 | `/opt/homelab/` | LiteLLM, Docling, n8n, Mem0, Open WebUI |
| deploy | 10.10.10.101 | `/opt/homelab/` | Coolify |
| ha | 10.10.10.116 | N/A | Home Assistant (Home Assistant OS) |

### Deployment Strategy

Services are deployed progressively in dependency order:
1. **Phase 1**: Database infrastructure (PostgreSQL, MongoDB, Redis, MinIO, Qdrant, ClickHouse, RabbitMQ, Kafka, Mosquitto) → Portainer
2. **Phase 2**: Edge services (Traefik → AdGuard → Authentik → NetBird)
3. **Phase 3**: Observability (Grafana, Loki, Tempo, Alloy, Glance, Langfuse)
4. **Phase 4**: Applications (AI, media, dev, deploy stacks)

## Common Commands

### Deploying Services

All services use 1Password for secrets management:
```bash
# Deploy a service
op run --env-file=.env -- docker compose up -d <service-name>

# Deploy all services in compose file
op run --env-file=.env -- docker compose up -d

# Check logs
docker compose logs -f <service-name>

# Check status
docker compose ps
```

### Updating Services

```bash
# Pull latest images
docker compose pull

# Recreate containers with new config/images
op run --env-file=.env -- docker compose up -d

# Update specific service
docker compose pull <service-name>
op run --env-file=.env -- docker compose up -d <service-name>
```

### Completely Removing and Reinstalling a Service

```bash
# Stop and remove container + named volumes
docker compose down <service-name> -v

# Remove bind mount data (./service/data directories)
sudo rm -rf <service-name>/data/*

# Remove from database if service uses one
# PostgreSQL:
docker exec postgres psql -U postgres -c "DROP DATABASE dbname;"
# MongoDB:
docker exec mongodb mongosh --eval "use dbname; db.dropDatabase();"

# Redeploy fresh
docker compose pull <service-name>
op run --env-file=.env -- docker compose up -d <service-name>

# Clean up dangling resources
docker system prune -f
```

## Important Patterns

### 1Password Integration

All `.env` files contain only 1Password references (not actual secrets):
```bash
# .env file (safe to commit)
MONGODB_ROOT_USER=op://Server/mongodb/username
MONGODB_ROOT_PASSWORD=op://Server/mongodb/password
```

The `op run --env-file=.env` command fetches secrets at runtime. Never commit actual passwords.

### Git Workflow

Changes to configuration files follow this pattern:
1. Edit files on local machine: `~/repositories/homelab/`
2. Commit changes: `git add . && git commit -m "message" && git push`
3. Pull on VMs: `ssh fx@10.10.10.xxx 'cd /opt/homelab && git pull'`
4. Restart affected services: `op run --env-file=.env -- docker compose up -d <service>`

### Service Dependencies

All services connect to centralized databases on db host:
```yaml
# PostgreSQL
DATABASE_URL: postgresql://user:pass@10.10.10.111:5432/dbname

# MongoDB
MONGO_URL: mongodb://user:pass@10.10.10.111:27017/dbname

# Redis
REDIS_URL: redis://:password@10.10.10.111:6379/0

# MinIO
S3_ENDPOINT: http://10.10.10.111:9000
```

### Progressive Service Deployment

When enabling new services:
1. Uncomment the service in `docker-compose.yml`
2. Uncomment corresponding env vars in `.env`
3. Ensure dependencies are running
4. Deploy: `op run --env-file=.env -- docker compose up -d <service-name>`

## Directory Structure

**Standardized Layout** - All VMs follow this pattern:

```
{vm-name}/
├── docker-compose.yml
├── .env                        # 1Password references only
├── {service-name}/
│   ├── config/                 # Service configs (committed)
│   ├── certs/                  # TLS certs (gitignored)
│   └── data/                   # Runtime data (gitignored)
```

## Key Configuration Files

### Database Configurations

- `db/mongodb/config/mongod.conf` - MongoDB config
- `db/postgres/config/postgresql.conf` - PostgreSQL tuning
- `db/postgres/config/pg_hba.conf` - PostgreSQL access control

### Observability Configurations

- `observability/grafana/provisioning/` - Datasources, dashboards
- `observability/loki/config/config.yml` - Log aggregation
- `observability/tempo/config/config.yml` - Trace aggregation
- `observability/alloy/config/config.alloy` - Metrics/logs/traces collection
- `observability/glance/config.yml` - Dashboard configuration
- `observability/langfuse/` - AI observability (uses ClickHouse on db VM)

### Edge Configurations

- `edge/traefik/config/traefik.yml` - Static config (entrypoints, SSL)
- `edge/traefik/config/dynamic/middlewares.yml` - Auth, headers, rate limiting
- `edge/traefik/config/dynamic/services.yml` - Backend server targets
- `edge/traefik/config/dynamic/routers.yml` - Domain routing rules

## Troubleshooting

### 1Password Issues
```bash
# Verify token is set
echo $OP_SERVICE_ACCOUNT_TOKEN

# Test connection
op vault list

# Test secret retrieval
op read "op://Server/mongodb/username"
```

### Container Issues
```bash
# Check if port already in use
sudo netstat -tulpn | grep <port>

# Check container logs
docker compose logs --tail=50 <service-name>

# Restart service
docker compose restart <service-name>
```

### Network Connectivity
```bash
# Test database connectivity from another VM
nc -zv 10.10.10.111 27017    # MongoDB
nc -zv 10.10.10.111 5432     # PostgreSQL
nc -zv 10.10.10.111 6379     # Redis
```

## Working with This Repository

### Making Changes to Configuration

1. Edit files on local machine: `~/repositories/homelab/`
2. Commit and push: `git add . && git commit -m "message" && git push`
3. Pull on affected VMs: `ssh fx@10.10.10.xxx 'cd /opt/homelab && git pull'`
4. Restart affected services

### Adding a New Service

1. Add service definition to appropriate `docker-compose.yml`
2. Add required env vars to `.env` file (using `op://` references)
3. Create 1Password entries if needed
4. Add any config files to `config/` directory
5. Test deploy: `op run --env-file=.env -- docker compose up -d <service-name>`
6. Check logs: `docker compose logs -f <service-name>`
7. Update README.md with service details
8. Commit changes

### Creating a New VM

See README.md → "Initial Setup" → "Creating a New VM" for complete checklist.

Key points:
1. Clone from template (full clone)
2. Set static IP in Proxmox
3. Boot VM and configure hostname
4. Set `OP_SERVICE_ACCOUNT_TOKEN` in `~/.bashrc`
5. Re-login to load environment variable
6. Clone repository: `git clone https://git.onurx.com/fx/homelab.git /opt/homelab`
7. Navigate to VM directory and deploy services

## Security Notes

- All secrets stored in 1Password (vault: "Server")
- `.env` files are safe to commit (contain only `op://` references)
- Never commit actual passwords or tokens
- Each VM should have its own SSH key (or use same key, copied after cloning)
- TLS certificates auto-generated in `certs/` directories (gitignored)

## Network Information

- VLAN 10 (10.10.10.0/24): Homelab services
- Gateway: 10.10.10.1
- DNS: AdGuard Home on 10.10.10.110
- All VMs communicate over VLAN 10
- VPN: NetBird (100.92.0.0/16)

## Critical Rules for Claude

### Always Use Existing Infrastructure Services

**NEVER deploy separate databases or services when we already have them!**

Use these existing services from db host (10.10.10.111):
- **PostgreSQL** - For any app needing SQL database
- **MongoDB** - For any app needing NoSQL/document database
- **Redis** - For caching, sessions, queues
- **MinIO** - For object storage (S3-compatible)
- **Qdrant** - For vector storage (AI/embeddings)
- **ClickHouse** - For analytics/time-series data
- **RabbitMQ** - For message queuing
- **Kafka** - For event streaming
- **Mosquitto** - For MQTT / IoT communication

### Always Choose Private or Public in Traefik

**NEVER add a Traefik route without explicit middleware!**

Every service in `edge/traefik/config/dynamic/routers.yml` MUST have either:
- **`private-default`** - Internal only (home + NetBird VPN) ← Use this by default
- **`public-access`** - Internet accessible ← Only for public services

**IP Whitelist:**
- Home network: `10.10.10.0/24`
- NetBird VPN: `100.92.0.0/16`

**Testing:**
- Private services from internet → **403 Forbidden** ✅
- Private services from home/VPN → Works ✅
- Public services from anywhere → Works ✅

### Documentation Updates

When making any infrastructure changes:
1. Update the code/configuration
2. Update README.md immediately
3. Commit both together
4. NEVER create new markdown files

Keep README.md as the single source of truth.
