# Homelab Infrastructure

Docker-based homelab infrastructure on Proxmox VMs. All VMs are stateless and disposable, with configurations managed via Git.

## Quick Reference

**Network:** VLAN 10 (10.10.10.0/24) | **Gateway:** 10.10.10.1 | **DNS:** 10.10.10.110 (AdGuard)

| VM | IP | Services |
|----|-----|----------|
| edge | 10.10.10.110 | Traefik, AdGuard, Authentik, NetBird |
| db | 10.10.10.111 | MongoDB, PostgreSQL, Redis, MinIO, Mosquitto |
| observability | 10.10.10.112 | Portainer, Prometheus, Grafana, Loki, Alloy, Homepage |
| media | 10.10.10.113 | Plex, Sonarr, Radarr, Prowlarr, SABnzbd, qBittorrent, Bazarr, Overseerr |
| dev | 10.10.10.114 | Gitea, Docker Registry, GitHub Runner |
| deploy | 10.10.10.101 | Coolify (deployment platform) |
| ha | 10.10.10.116 | Home Assistant |

**Common commands:**
```bash
cd /opt/homelab/<vm-name>
op run --env-file=.env -- docker compose up -d <service>
docker compose logs -f <service>
```

---

## Table of Contents

1. [Architecture](#architecture)
2. [Initial Setup](#initial-setup)
3. [Service Deployment](#service-deployment)
4. [Management Interfaces](#management-interfaces)
5. [Common Operations](#common-operations)
6. [Service Configuration](#service-configuration)
7. [Troubleshooting](#troubleshooting)
8. [Current Status](#current-status)

---

## Architecture

### Directory Structure

All VMs follow this pattern:
```
/opt/homelab/{vm-name}/
├── docker-compose.yml       # Service definitions
├── .env                     # 1Password references only (safe to commit)
├── {service-name}/
│   ├── config/              # Service configs (committed to git)
│   ├── certs/               # TLS certs (gitignored)
│   └── data/                # Runtime data (gitignored)
```

### Git Repository

- **Repository:** https://git.onurx.com/fx/homelab (public)
- **Local path:** `/opt/homelab/` on all VMs
- **Workflow:** Edit locally → commit → push → pull on VMs → restart services

### Secrets Management

All secrets stored in **1Password vault "Server"**:
- `.env` files contain only `op://Server/item/field` references
- Use `op run --env-file=.env -- docker compose up -d` to inject secrets
- Never commit actual passwords

### Dependency Order

Services should be deployed in this order:
1. **db VM:** MongoDB → PostgreSQL → Redis → MinIO → Mosquitto
2. **observability VM:** Portainer → Prometheus → Grafana → Loki → Alloy → Homepage
3. **edge VM:** Traefik → AdGuard → Authentik → NetBird
4. **Other VMs:** Deploy as needed

---

## Initial Setup

### Creating a New VM

**On Proxmox host:**
```bash
# Clone from template (full clone recommended)
qm clone <template-id> <new-vm-id> --name <vm-name> --full

# Configure static IP
qm set <new-vm-id> --ipconfig0 ip=10.10.10.<ip>/24,gw=10.10.10.1

# Start VM
qm start <new-vm-id>
```

**On new VM (after boot):**
```bash
# Set hostname
sudo hostnamectl set-hostname <vm-name>

# Set 1Password token in ~/.bashrc
echo 'export OP_SERVICE_ACCOUNT_TOKEN="ops_xxx"' >> ~/.bashrc
source ~/.bashrc

# Test 1Password connection
op vault list

# Clone repository
cd /opt
sudo git clone https://git.onurx.com/fx/homelab.git
sudo chown -R fx:fx homelab/
cd homelab
git branch --set-upstream-to=origin/main main
```

### VM Template Setup

Base packages installed in template:
- Docker + Docker Compose
- Git (pre-configured: `git config --global user.name "XVll" && git config --global user.email "onur03@gmail.com"`)
- 1Password CLI
- QEMU guest agent
- Standard utilities (curl, wget, vim, htop)

**DO NOT** set `OP_SERVICE_ACCOUNT_TOKEN` in template - set per VM.

---

## Service Deployment

### Standard Deployment Pattern

```bash
# Navigate to VM directory
cd /opt/homelab/<vm-name>

# Deploy specific service
op run --env-file=.env -- docker compose up -d <service-name>

# Deploy all services in compose file
op run --env-file=.env -- docker compose up -d

# Check logs
docker compose logs -f <service-name>

# Check status
docker compose ps
```

### Service-Specific Notes

#### Database Services (db VM - 10.10.10.111)

**PostgreSQL:**
- Port: 5432
- Connection: `postgresql://user:pass@10.10.10.111:5432/dbname`
- Create database: `docker exec postgres psql -U postgres -c "CREATE DATABASE dbname;"`

**MongoDB:**
- Port: 27017
- Connection: `mongodb://user:pass@10.10.10.111:27017/dbname`
- Shell access: `docker exec -it mongodb mongosh`

**Redis:**
- Port: 6379
- Connection: `redis://:password@10.10.10.111:6379/0`
- Test: `docker exec redis redis-cli -a password ping`

**MinIO:**
- S3 API: 9000
- Console: 9002
- Connection: `http://10.10.10.111:9000` with access key/secret

**Mosquitto MQTT:**
- Port: 1883 (MQTT), 9003 (WebSockets)
- Connection: `mqtt://10.10.10.111:1883`
- Anonymous connections enabled by default

#### Reverse Proxy (edge VM - 10.10.10.110)

**Traefik:**
- Dashboard: http://10.10.10.110:8080 or https://traefik.onurx.com
- Configuration: `edge/traefik/config/`
  - `traefik.yml` - Static config (entrypoints, SSL)
  - `dynamic/middlewares.yml` - Auth, headers, rate limiting
  - `dynamic/services.yml` - Backend targets
  - `dynamic/routers.yml` - Domain routing rules
- Auto-reloads dynamic configs (no restart needed)
- SSL: Cloudflare DNS-01 challenge, wildcard `*.onurx.com`

**Security Model - ALWAYS Choose Private or Public:**
```yaml
# Private service (home + VPN only)
router-name:
  rule: "Host(`service.onurx.com`)"
  entryPoints: [websecure]
  service: service-name
  middlewares:
    - private-default  # ← REQUIRED for internal services
  tls:
    certResolver: cloudflare

# Public service (internet accessible)
router-name:
  rule: "Host(`service.onurx.com`)"
  entryPoints: [websecure]
  service: service-name
  middlewares:
    - public-access  # ← ONLY for public services
  tls:
    certResolver: cloudflare
```

**IP Whitelist:**
- Home network: `10.10.10.0/24`
- NetBird VPN: `100.92.0.0/16`

**Current public services:** ha.onurx.com, dmo.onurx.com, king.onurx.com, wsking.onurx.com, deploy.onurx.com

#### Monitoring Stack (observability VM - 10.10.10.112)

**Prometheus:**
- URL: https://prometheus.onurx.com
- Port: 9090
- Retention: 90 days
- Scrapes: Node exporter, cAdvisor, SNMP (Synology)

**Grafana:**
- URL: https://grafana.onurx.com
- Port: 3000
- Credentials: 1Password `op://Server/grafana`
- Datasources: Prometheus, Loki (auto-provisioned)

**Loki:**
- URL: https://loki.onurx.com
- Port: 3100
- Retention: 90 days
- Storage: Filesystem (local)
- Access: Via Grafana Explore

**Alloy:**
- Deployed on all VMs (collects logs + metrics)
- Observability VM: Full metrics + logs
- Other VMs: Logs only
- UI: http://10.10.10.112:12345 (observability VM only)

**Homepage:**
- URL: https://home.onurx.com
- Port: 3002
- Configuration: `observability/homepage/config/`
- Unified dashboard for all infrastructure services

#### Media Stack (media VM - 10.10.10.113)

**Storage:** NFS mount from Synology at `/mnt/nas/media`
```
/mnt/nas/media/
├── library/
│   ├── movies/  (Radarr)
│   └── tv/      (Sonarr)
└── downloads/
    ├── sabnzbd/  (Usenet - primary)
    └── torrents/ (VPN + qBittorrent - fallback)
```

**Workflow:**
1. Request via Overseerr → Sonarr/Radarr
2. Search via Prowlarr (indexers)
3. Download via SABnzbd (Usenet) or qBittorrent (torrents)
4. Hardlink to library (on same filesystem)
5. Bazarr adds subtitles
6. Plex scans and serves

**Services:**
- Plex: http://10.10.10.113:32400/web
- Overseerr: http://10.10.10.113:5055
- Sonarr: http://10.10.10.113:8989
- Radarr: http://10.10.10.113:7878
- Prowlarr: http://10.10.10.113:9696
- SABnzbd: http://10.10.10.113:8085
- qBittorrent: http://10.10.10.113:8080 (via Gluetun VPN)
- Bazarr: http://10.10.10.113:6767

#### Development Stack (dev VM - 10.10.10.114)

**Gitea:**
- URL: https://git.onurx.com
- Ports: 3001 (HTTP), 222 (SSH)
- Features: Git hosting, Actions (CI/CD), Container Registry
- Database: PostgreSQL on db VM
- Note: Not actively used for CI/CD (using GitHub Runner instead)

**Docker Registry:**
- Port: 5000
- Internal only: http://10.10.10.114:5000
- Usage: `docker push 10.10.10.114:5000/image:tag`

**GitHub Runner:**
- Self-hosted runner for GitHub Actions
- Provides access to homelab resources
- No minute limits

#### Deployment Platform (deploy VM - 10.10.10.101)

**Coolify:**
- URL: https://deploy.onurx.com (public - has own auth)
- Port: 8000
- PaaS for deploying applications
- GitHub webhooks configured

#### Home Automation (ha VM - 10.10.10.116)

**Home Assistant:**
- URL: https://ha.onurx.com (public)
- Port: 8123
- Home Assistant OS (not Docker)
- Database: PostgreSQL on db VM
- Backups: Settings → System → Backups

---

## Management Interfaces

### Layer 1: Homepage Dashboard (Primary Entry Point)
- **URL:** https://home.onurx.com
- **Purpose:** Single pane of glass for all services
- Service directory, health checks, Docker stats, quick access

### Layer 2: Grafana (Deep Metrics & Observability)
- **URL:** https://grafana.onurx.com
- **Purpose:** Metrics, logs, performance analysis
- **Systems Overview Dashboard:** Clean table view with CPU, memory, disk, network, load avg for all VMs
- Explore → Loki for log queries
- Pre-built dashboards for infrastructure overview

### Layer 3: Portainer (Container Management)
- **URL:** https://portainer.onurx.com
- **Purpose:** Visual Docker management across all VMs
- Portainer agents on: edge, db, dev, media VMs

---

## Common Operations

### Updating Services

```bash
# Pull latest image
docker compose pull <service-name>

# Recreate container with new image
op run --env-file=.env -- docker compose up -d <service-name>

# Update all services
docker compose pull
op run --env-file=.env -- docker compose up -d
```

### Completely Removing and Reinstalling

```bash
# Stop and remove container + named volumes
docker compose down <service-name> -v

# Remove bind mount data (NOT removed by docker compose down)
sudo rm -rf <service-name>/data/*

# Remove database if service uses one
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

### Testing Database Connections

```bash
# From db VM
docker exec postgres pg_isready -U postgres
docker exec mongodb mongosh --eval "db.adminCommand('ping')"
docker exec redis redis-cli -a password ping

# From another VM
psql -h 10.10.10.111 -U user -d dbname
mongosh --host 10.10.10.111:27017 -u user -p pass
redis-cli -h 10.10.10.111 -a password ping
```

### Adding Traefik Routes

1. Add service to `edge/traefik/config/dynamic/services.yml`:
```yaml
service-name:
  loadBalancer:
    servers:
      - url: "http://10.10.10.x:port"
```

2. Add router to `edge/traefik/config/dynamic/routers.yml`:
```yaml
service-name:
  rule: "Host(`service.onurx.com`)"
  entryPoints: [websecure]
  service: service-name
  middlewares:
    - private-default  # or public-access
  tls:
    certResolver: cloudflare
```

3. Traefik auto-reloads (no restart needed)

### Checking Logs

```bash
# Via Grafana (recommended):
# https://grafana.onurx.com → Explore → Loki
{container="service-name"}
{host="vm-name"}
{level="error"}
{cluster="homelab"} |~ "(?i)error|fail"

# Via Docker:
docker compose logs -f <service-name>
docker compose logs --tail=50 <service-name>
```

### Updating Configuration Files

```bash
# On local machine (Mac):
cd ~/Repositories/infrastructure-1
# Edit files
git add . && git commit -m "Update config" && git push

# On VM:
ssh fx@10.10.10.xxx
cd /opt/homelab
git pull
op run --env-file=.env -- docker compose up -d <affected-service>
```

---

## Service Configuration

### Critical Rules

#### Always Use Existing Infrastructure Services

**NEVER deploy separate databases when we already have them!**

Use these from db host (10.10.10.111):
- PostgreSQL for SQL databases
- MongoDB for NoSQL/document databases
- Redis for caching, sessions, queues
- MinIO for object storage (S3-compatible)
- Mosquitto for MQTT/message broker

#### Always Choose Private or Public in Traefik

**NEVER add a Traefik route without explicit middleware!**

Every service MUST have either:
- `private-default` - Internal only (home + NetBird VPN) ← Use by default
- `public-access` - Internet accessible ← Only for public services

#### Single Source of Truth

This README.md is the ONLY documentation file. When changes are made:
1. Update this README.md
2. Commit changes
3. Push to git

### 1Password Configuration

Required items in vault "Server":
- `mongodb` - fields: username, password
- `postgres` - fields: username, password
- `redis` - field: password
- `minio` - fields: username, password
- `grafana` - fields: username, password
- `cloudflare` - fields: email, api_token
- `authentik-db` - field: password
- `authentik` - field: secret_key
- `netbird` - field: token

Generate secrets:
```bash
# Authentik secret key
openssl rand -base64 50

# Authentik internal token
openssl rand -hex 105
```

### Prometheus Queries

```promql
# System metrics
up                                          # All targets
node_cpu_seconds_total                      # CPU usage
container_memory_usage_bytes                # Docker memory

# Synology NAS (via SNMP)
systemStatus{instance="10.10.10.100"}       # System status
diskHealthStatus{instance="10.10.10.100"}   # Disk health
raidStatus{instance="10.10.10.100"}         # RAID status
```

### Loki Queries

```logql
{cluster="homelab"}                          # All logs
{host="db"}                                  # Specific VM
{container="mongodb"}                        # Specific container
{level="error"}                              # Errors only
{cluster="homelab"} |~ "(?i)error|fail"     # Search pattern
```

---

## Troubleshooting

### VirtioFS Mount Issues (if using VirtioFS)
```bash
mount | grep virtiofs
sudo mount -a
cat /etc/fstab | grep docker-vm
```

### NAS Mount Issues (Media VM)
```bash
# Check if NAS is mounted
mount | grep 10.10.10.100
df -h /mnt/nas/media

# Mount NAS if not mounted
sudo mount /mnt/nas/media

# Verify mount persists after reboot (should show in fstab)
cat /etc/fstab | grep nas

# Check what services can see the NAS
docker exec sabnzbd ls -lah /media/

# If downloads went to local disk (check Grafana - disk full warning):
# 1. Unmount NAS temporarily: sudo umount /mnt/nas/media
# 2. Check local files: sudo ls -lah /mnt/nas/media/
# 3. Remove local files: sudo rm -rf /mnt/nas/media/downloads/*
# 4. Remount NAS: sudo mount /mnt/nas/media
# 5. Restart media services: docker restart sabnzbd sonarr radarr
```

**Prometheus Alert:** `NASNotMounted` alert will fire if NAS unmounts (checks filesystem size < 1TB)

### 1Password Issues
```bash
# Verify token
echo $OP_SERVICE_ACCOUNT_TOKEN

# Test connection
op vault list

# Test secret retrieval
op read "op://Server/mongodb/username"
```

### Container Issues
```bash
# Check port conflicts
sudo netstat -tulpn | grep <port>

# Check container logs
docker compose logs --tail=50 <service-name>

# Restart service
docker compose restart <service-name>

# Rebuild service
docker compose up -d --force-recreate <service-name>
```

### Network Connectivity
```bash
# Test database connectivity
nc -zv 10.10.10.111 27017    # MongoDB
nc -zv 10.10.10.111 5432     # PostgreSQL
nc -zv 10.10.10.111 6379     # Redis

# Test DNS resolution
nslookup service.onurx.com 10.10.10.110

# Test HTTP endpoint
curl -I https://service.onurx.com
```

### Git Issues
```bash
# Repository not pulling
cd /opt/homelab
git status
git remote -v

# Reset to remote state
git fetch origin
git reset --hard origin/main

# Fix permissions
sudo chown -R fx:fx /opt/homelab
```

---

## Current Status

### Deployed Services

**Phase 1 - Foundation:** ✅ Complete
- MongoDB, PostgreSQL, Redis, MinIO, Mosquitto
- Portainer

**Phase 2 - Edge Services:** ✅ Complete
- Traefik (reverse proxy + SSL)
- AdGuard Home (DNS)
- Authentik (SSO - deployed but not configured)
- NetBird (VPN client)

**Phase 3 - Observability:** ✅ Complete
- Prometheus (metrics - 90 day retention)
- Grafana (dashboards - systems overview, system detail)
- Loki (logs - 90 day retention)
- Alloy (collectors on all VMs - metrics + logs)
- Homepage (unified dashboard)
- SNMP monitoring for Synology NAS

**Phase 4 - Applications:** ⏳ In Progress
- Gitea (Git hosting + CI/CD)
- GitHub Runner (CI/CD)
- Docker Registry
- Coolify (deployment platform)
- Home Assistant
- Media stack (Plex, *arr, downloaders)

### Critical Action Items

**🔴 HIGH PRIORITY:**
1. **Backup Strategy** - No VM backups configured (Proxmox Backup Server or vzdump)
2. **Authentication** - Authentik deployed but no applications configured
3. **Resource Limits** - No CPU/memory limits on containers
4. **Health Checks** - Several services missing health checks

**🟡 MEDIUM PRIORITY:**
1. **SSL Migration** - Route more services via Traefik (AdGuard, Portainer)
2. **Synology Monitoring** - SNMP configured but needs Grafana dashboard

**✅ COMPLETED:**
1. **NAS Mount Monitoring** - Prometheus alert configured for media VM NAS mount
2. **Media Stack** - All services deployed (Plex, SABnzbd, Sonarr, Radarr, etc.)

**🟢 LOW PRIORITY:**
1. **Cloudflare Tunnels** - Migrate from direct DNS (blocked by email migration)
2. **SSL Certificate Monitoring** - Add Prometheus alerts for cert expiry

### Network Information

- VLAN 10: 10.10.10.0/24
- Gateway: 10.10.10.1
- DNS: AdGuard Home (10.10.10.110)
- Wildcard DNS: `*.onurx.com` → 10.10.10.110
- VPN: NetBird (100.92.0.0/16)

### Access URLs

**Management:**
- Homepage: https://home.onurx.com
- Portainer: https://portainer.onurx.com
- Grafana: https://grafana.onurx.com (Systems Overview, System Detail dashboards)
- Prometheus: https://prometheus.onurx.com
- Traefik: https://traefik.onurx.com

**Edge:**
- Authentik: https://auth.onurx.com
- AdGuard: http://10.10.10.110:8888

**Database:**
- MinIO Console: http://10.10.10.111:9002

**Development:**
- Gitea: https://git.onurx.com
- Coolify: https://deploy.onurx.com

**Applications:**
- Home Assistant: https://ha.onurx.com

---

## Additional Notes

### Docker Networking

**Traefik routing:**
- Same VM: Use container name (e.g., `http://container-name:port`)
- Different VM: Use VM IP (e.g., `http://10.10.10.112:3000`)

**Flow:** User → DNS → Traefik (10.10.10.110) → Backend service

### Security Notes

- All secrets in 1Password (never commit passwords)
- `.env` files safe to commit (contain only `op://` references)
- Each VM has own SSH key (or copy from template)
- TLS certificates auto-generated (gitignored)
- Private services blocked from internet by default

### Git Configuration

Repository is **public** (allows VMs to pull without auth)
- Remote: https://git.onurx.com/fx/homelab.git
- Branch tracking: main → origin/main
- DNS resolves via AdGuard wildcard

---

**Last Updated:** 2025-11-02
