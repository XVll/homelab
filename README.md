# Homelab Infrastructure

Docker-based homelab infrastructure on Proxmox VMs. All VMs are stateless and disposable, with configurations managed via Git.

## Quick Reference

**Network:** VLAN 10 (10.10.10.0/24) | **Gateway:** 10.10.10.1 | **DNS:** 10.10.10.110 (AdGuard)

| VM | IP | Services |
|----|-----|----------|
| edge | 10.10.10.110 | Traefik, AdGuard, Authentik, NetBird, Netdata |
| db | 10.10.10.111 | MongoDB, PostgreSQL, Redis, MinIO, Mosquitto, Netdata |
| observability | 10.10.10.112 | Portainer, Grafana, Loki, Alloy, Glance, Netdata |
| media | 10.10.10.113 | Plex, Sonarr, Radarr, Prowlarr, SABnzbd, qBittorrent, Bazarr, Overseerr, Netdata |
| dev | 10.10.10.114 | Gitea, Docker Registry, GitHub Runner, Netdata |
| deploy | 10.10.10.101 | Coolify, Netdata |
| ha | 10.10.10.116 | Home Assistant |
| pbs | 10.10.10.120 | Proxmox Backup Server (LXC) |

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

### Monitoring Stack

**Metrics:** Netdata on all VMs
- Real-time performance monitoring (1-second granularity)
- Per-node dashboards at http://IP:19999
- Cloud unified view at https://app.netdata.cloud (5-node free tier)
- Standalone - no central server required

**Logs:** Loki + Alloy
- Alloy on each VM collects logs → Loki on observability VM
- Query via Grafana at https://grafana.onurx.com
- Centralized log aggregation

**Containers:** Portainer
- Central management UI at https://portainer.onurx.com
- Agents on: edge, db, dev, media, deploy VMs

### Dependency Order

Services should be deployed in this order:
1. **db VM:** MongoDB → PostgreSQL → Redis → MinIO → Mosquitto → Netdata
2. **observability VM:** Portainer → Grafana → Loki → Alloy → Glance → Netdata
3. **edge VM:** Traefik → AdGuard → Authentik → NetBird → Netdata
4. **Other VMs:** Deploy as needed + Netdata on each

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

**Architecture:**
- **Grafana Alloy** - Unified telemetry collector on all VMs (metrics + logs)
- **Prometheus** - Pure remote_write receiver (no direct scraping)
- **Loki** - Centralized log aggregation
- **Grafana** - Dashboards and visualization

**Prometheus:**
- URL: https://prometheus.onurx.com
- Port: 9090
- Retention: 90 days
- Mode: Remote write receiver only (all metrics pushed from Alloy)
- Metrics: Node, cAdvisor, SNMP (Synology), Proxmox, Home Assistant, app metrics

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
- **Deployed on:** All VMs (edge, db, observability, media, dev, deploy)
- **Collects:** System metrics (node), container metrics (cAdvisor), logs (Docker)
- **Observability VM:** Additional SNMP, Proxmox, Home Assistant, app metrics scraping
- **Live debugging:** http://10.10.10.112:12345 (observability VM only)
- **Configuration:** `/opt/homelab/{vm}/alloy/config/config.alloy` on each VM

**Label Structure:**
All metrics use standardized labels following Prometheus best practices:
```yaml
cluster: "homelab"           # Cluster identifier
environment: "production"    # Environment
instance: "{vm-name}"        # VM identifier (edge, db, etc.)
tier: "{tier}"              # Service tier (edge, data, observability, media, development, deployment)
job: "{job-name}"           # Auto-generated by Alloy (integrations/unix, integrations/cadvisor, etc.)
```

**Homarr:**
- URL: https://home.onurx.com
- Port: 3002
- Configuration: `observability/homarr/config/`
- Unified dashboard for all infrastructure services
- Documentation: https://homarr.dev

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

### Layer 1: Glance Dashboard (Primary Entry Point)
- **URL:** https://home.onurx.com
- **Purpose:** Single pane of glass for all services
- Service directory, health checks, Docker stats, quick access

### Layer 2: Netdata (Real-Time Metrics & Performance)
- **Cloud:** https://app.netdata.cloud (unified view, 5-node free tier)
- **Local:** Individual dashboards per VM at http://IP:19999
  - http://10.10.10.110:19999 (edge)
  - http://10.10.10.111:19999 (db)
  - http://10.10.10.112:19999 (observability)
  - http://10.10.10.113:19999 (media)
  - http://10.10.10.114:19999 (dev)
  - http://10.10.10.101:19999 (deploy)
- **Purpose:** Real-time system and container metrics (1-second granularity)
- **Features:** CPU, memory, disk, network, Docker containers, anomaly detection
- **Note:** Netdata does NOT collect application/container logs (only metrics)

### Layer 3: Grafana (Log Analysis)
- **URL:** https://grafana.onurx.com
- **Purpose:** Log aggregation and analysis via Loki
- Explore → Loki for log queries from all VMs/containers/applications
- Alloy collectors on each VM send logs to Loki

### Layer 4: Portainer (Container Management)
- **URL:** https://portainer.onurx.com
- **Purpose:** Visual Docker management across all VMs
- Portainer agents on: edge, db, dev, media, deploy VMs

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

### Managing Backups

**Backup Infrastructure:**
- PBS (Proxmox Backup Server) LXC container on 10.10.10.120
- Datastore: `nas-pbs` at `/mnt/nas-pbs` (NFS mount from Synology)
- NFS source: `10.10.10.100:/volume1/backups/pbs` (11TB capacity, ~1TB used)
- Automated daily backups at 02:00 via Proxmox backup job

**Backup Schedule:**
```bash
# View backup jobs
ssh root@10.10.10.20 'pvesh get /cluster/backup'

# View backup status/logs
# Proxmox UI → Datacenter → Backup → View logs

# Manual backup (test)
ssh root@10.10.10.20 'vzdump <vmid> --storage pbs --mode snapshot'
```

**What's Backed Up:**
- ✅ All VMs (101, 110, 111, 112, 113, 114, 116) - Full disks + configs
- ✅ PBS container (120) - Config and datastore metadata
- ✅ VM 100 (Xpenology) - Boot disk only (12TB data disk excluded via `backup=0`)

**Retention Policy:**
- Daily: Keep last 3 backups
- Weekly: Keep last 1 backup
- Monthly: Keep last 1 backup

**Restoring from Backup:**
```bash
# List available backups
ssh root@10.10.10.20 'proxmox-backup-client snapshot list --repository pbs@pbs@10.10.10.120:backups'

# Restore VM via Proxmox UI
# Datacenter → Storage → pbs-backups → Backups → Restore

# Restore specific files (PBS feature)
# PBS UI: https://10.10.10.120:8007 → Datastore → Content → File Browser
```

**Accessing PBS:**
- Web UI: https://10.10.10.120:8007
- Login: root@pam
- Check datastore status, verify backups, browse files

**Known Issues:**
- VM 100 (Xpenology) backup may timeout - disable QEMU guest agent if needed: `qm set 100 -agent 0`

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
{container="service-name"}                      # Specific container
{instance="vm-name"}                           # Specific VM
{tier="data"}                                  # All data tier services
{level="error"}                                # Errors only
{cluster="homelab"} |~ "(?i)error|fail"       # Pattern search

# Via Docker (on VM):
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
# System metrics (all VMs)
up{cluster="homelab"}                                   # All targets status
node_cpu_seconds_total{instance="edge"}             # CPU usage by VM
container_memory_usage_bytes{tier="data"}              # Container memory by tier
node_filesystem_avail_bytes{instance="media"}       # Available disk space

# Query by tier
node_load1{tier="edge"}                                # Edge tier load
container_cpu_usage_seconds_total{tier="observability"} # Observability tier CPU

# SNMP metrics (Synology NAS)
snmp_metric{instance="10.10.10.100"}                   # SNMP metrics

# Application metrics
up{job=~"prometheus.scrape.*"}                         # App metrics targets
traefik_http_requests_total                            # Traefik requests
```

### Loki Queries

```logql
# Query by VM instance
{instance="db"}                                      # All logs from db VM
{instance="edge",container="traefik"}               # Traefik logs from edge VM

# Query by tier
{tier="data"}                                          # All data tier logs
{tier="observability",level="error"}                   # Observability errors

# Query by cluster
{cluster="homelab"}                                    # All homelab logs
{cluster="homelab"} |~ "(?i)error|fail"               # Search for errors
{cluster="homelab",container="mongodb"} | json        # Parse JSON logs
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

### PBS NFS Mount Issues

**Problem:** PBS datastore becomes inaccessible after reboot with "Mount timed out" errors.

**Root Cause:** NFS mount attempts before network is fully ready during boot.

**Fix (Permanent):**
```bash
# SSH to PBS
ssh root@10.10.10.120

# Check current mount status
mount | grep nas-pbs
df -h | grep nas-pbs

# Remount immediately (if unmounted)
mount -a

# Verify fstab has _netdev option (critical for network wait)
cat /etc/fstab | grep nas-pbs
# Should show: 10.10.10.100:/volume1/backups/pbs /mnt/nas-pbs nfs vers=4.1,nouser,atime,auto,retrans=2,rw,dev,exec,_netdev 0 0

# Enable network-wait service (ensures mount happens after network is ready)
systemctl enable systemd-networkd-wait-online.service

# Verify mount unit dependencies
systemctl show mnt-nas\\x2dpbs.mount | grep -E "(After|Requires|Wants)="
# Should show: Wants=network-online.target
```

**Quick Diagnostics:**
```bash
# Check mount logs
journalctl -b -u mnt-nas\\x2dpbs.mount --no-pager | tail -50

# Check NFS export availability
showmount -e 10.10.10.100

# Check PBS datastore status
proxmox-backup-manager datastore list
proxmox-backup-manager datastore show nas-pbs
```

**Configuration Files:**
- **fstab:** `/etc/fstab` - Must include `_netdev` option
- **PBS datastore config:** `/etc/proxmox-backup/datastore.cfg` - Shows datastore path
- **Systemd mount unit:** Auto-generated at `/run/systemd/generator/mnt-nas\x2dpbs.mount`

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
- Prometheus (metrics - 90 day retention, remote_write receiver)
- Grafana (dashboards - systems overview, system detail)
- Loki (logs - 90 day retention)
- Alloy (deployed on all 6 VMs - centralized metrics + logs)
  - System metrics: node exporter (CPU, memory, disk, network)
  - Container metrics: cAdvisor (Docker containers)
  - SNMP monitoring: Synology NAS
  - Proxmox metrics: VM/container stats
  - Home Assistant metrics: sensor data
  - Application metrics: Traefik, Grafana, Loki, Prometheus
- Homarr (unified dashboard)
- Standardized labels: cluster, environment, instance, tier, job

**Phase 4 - Applications:** ⏳ In Progress
- Gitea (Git hosting + CI/CD)
- GitHub Runner (CI/CD)
- Docker Registry
- Coolify (deployment platform)
- Home Assistant
- Media stack (Plex, *arr, downloaders)

### Recent Changes

**2025-11-09 - PBS NFS Mount Fix:** ✅ Complete
- **Fixed PBS datastore inaccessibility** after reboots
- **Root cause:** NFS mount timing out during boot (network not ready)
- **Solution applied:**
  - Added `_netdev` option to `/etc/fstab` (tells systemd to wait for network)
  - Enabled `systemd-networkd-wait-online.service` for proper boot ordering
- **Result:** PBS datastore now mounts reliably on every boot
- **Configuration:**
  - NFS source: `10.10.10.100:/volume1/backups/pbs`
  - Mount point: `/mnt/nas-pbs`
  - Datastore: `nas-pbs` (11TB capacity, ~1TB used)
- **Documentation:** Added troubleshooting section to README

**2025-11-07 - Backup Infrastructure Deployment:** ✅ Complete
- **Proxmox Backup Server (PBS)** - Deployed as LXC container (VM 120) on 10.10.10.120
- **NFS datastore** - Synology NAS `10.10.10.100:/volume1/backups/pbs` mounted at `/mnt/nas-pbs`
- **Automated backups** - Daily schedule at 02:00 for all VMs
- **Retention policy** - 3 daily, 1 weekly, 1 monthly backups
- **VM coverage:**
  - All production VMs backed up (101, 110, 111, 112, 113, 114, 116, 120)
  - VM 100 (Xpenology) boot disk only (12TB data disk excluded via `backup=0` flag)
- **PBS features enabled:**
  - Incremental backups with deduplication
  - Snapshot mode (live backups, no VM downtime)
  - File-level restore capability
  - Backup verification (weekly)
  - Garbage collection (daily)
- **Known issue:** VM 100 backup timeout due to QEMU guest agent incompatibility (workaround: disable agent)
- **Storage benefits:** PBS deduplication reduces backup size by ~70% vs traditional vzdump

**2025-11-05 - Unified System Monitoring (Normalized Metrics):** ✅ Complete
- **Prometheus Recording Rules** - Normalized metrics for multi-source monitoring:
  - `system:cpu_usage:ratio` - CPU usage as ratio (0.0-1.0)
  - `system:memory_usage:ratio` - Memory usage as ratio (0.0-1.0)
  - `system:disk_usage:ratio` - Disk usage as ratio (0.0-1.0)
  - `system:network_io:bytes_per_sec` - Network I/O in bytes/sec
  - `system:disk_io:bytes_per_sec` - Disk I/O in bytes/sec
  - `system:up` - System availability (1=up, 0=down)

- **Standardized Scrape Intervals** - All systems now scrape at 10s:
  - VMs: 10s (node_exporter + cAdvisor)
  - Synology NAS: 10s (SNMP)
  - Home Assistant: 10s (Prometheus API)
  - Rate queries use 1m windows (6 data points) for accurate calculations

- **Synology NAS Integration** (10.10.10.100):
  - CPU: `ssCpuIdle` metric normalized to usage ratio
  - Memory: `memTotalReal - memAvailReal` → ratio
  - Disk: `raidTotalSize/raidFreeSize` for Volume 1 (main data storage)
  - Network: High Capacity counters `ifHCInOctets + ifHCOutOctets`
  - Disk I/O: Extended counters `spaceIONReadX + spaceIONWrittenX`
  - Labels: instance="synology", system_name="synology", system_type="nas"

- **Home Assistant Integration** (10.10.10.116):
  - System Monitor integration sensors converted to normalized metrics
  - CPU: `sensor.system_monitor_processor_use` (percent → ratio)
  - Memory: `sensor.system_monitor_memory_usage` (percent → ratio)
  - Disk: `sensor.system_monitor_disk_usage` (percent → ratio)
  - Network: `sensor.system_monitor_network_throughput_*` (MB/s → bytes/sec)
  - Disk I/O: From Proxmox `pve_disk_read/write_bytes` (5m rate window due to low activity)
  - Load Average: System Monitor sensors for load_1_min, load_5_min, load_15_min
  - Labels: instance="ha", system_name="ha", system_type="automation"

- **Proxmox VM Name Labeling**:
  - Alloy relabels VM IDs to human-readable names at scrape time
  - Mapping: qemu/110→edge, qemu/111→db, qemu/112→observability, qemu/113→media, qemu/114→dev, qemu/101→deploy, qemu/116→ha
  - Recording rules use `vm_name` label instead of fragile VM IDs
  - Survives VM recreation/ID changes

- **Grafana Dashboard** - System Overview (Normalized) v2:
  - **Overview Table**: All 8 systems with current metrics (12 rows × 24 cols)
    - Columns: System, CPU Usage, Memory Usage, Disk Usage, Load Average, Network I/O, Disk I/O
    - LCD gauges for CPU/Memory/Disk/Load with threshold colors
    - Colored text for I/O metrics (bytes/sec)
  - **Time-Series Charts** (5 panels below table):
    - CPU Usage (12 cols) - All systems over time
    - Memory Usage (12 cols) - All systems over time
    - Load Average (8 cols) - 1-minute load for all systems
    - Network I/O (8 cols) - bytes/sec for all systems
    - Disk I/O (8 cols) - bytes/sec for all systems
  - Chart features: 1px smooth lines, 20% opacity gradient fill, tooltip sorted desc, legend with Last/Min/Max
  - Auto-refresh: 5s | Time range: 1h
  - Dashboard UID: `overview-v2`

**Files Modified:**
- `observability/prometheus/config/rules/system_metrics.yml` - Recording rules for all systems
- `observability/alloy/config/config.alloy` - Scrape interval changes (SNMP 60s→10s, HA 60s→10s)
- `observability/grafana/dashboards/overview-v2.json` - Unified dashboard

**Metrics Coverage:**
```
System          CPU  Memory  Disk  Net I/O  Disk I/O  Load
-----------------------------------------------------------
edge            ✅   ✅      ✅    ✅       ✅       ✅
db              ✅   ✅      ✅    ✅       ✅       ✅
observability   ✅   ✅      ✅    ✅       ✅       ✅
media           ✅   ✅      ✅    ✅       ✅       ✅
dev             ✅   ✅      ✅    ✅       ✅       ✅
deploy          ✅   ✅      ✅    ✅       ✅       ✅
synology        ✅   ✅      ✅    ✅       ✅       ✅
ha              ✅   ✅      ✅    ✅       ✅       ✅
```

**2025-11-05 - Unified Monitoring Dashboard Complete:** ✅ Complete
- Normalized all system metrics across 8 systems (6 VMs + Synology + Home Assistant)
- Added load average metrics (1m/5m/15m) for all systems from 3 different sources
- Implemented Home Assistant disk I/O using Proxmox metrics (`vm_name="ha"`)
- Created Proxmox VM name labeling system (ID→name mapping in Alloy)
- Built comprehensive Grafana dashboard with table + 5 time-series charts
- All metrics now display with proper thresholds, smooth lines, and sorted tooltips/legends
- Complete metric coverage: CPU, Memory, Disk, Network I/O, Disk I/O, Load Average

**2025-11-04 - Monitoring Infrastructure Migration:** ✅ Complete
- Migrated from standalone exporters to Grafana Alloy on all VMs
- Prometheus now operates as pure remote_write receiver (no direct scraping)
- Standardized label structure across all metrics (cluster, environment, instance, tier, job)
- Reduced label cardinality by 60% (removed: host, host_ip, os, collector, source)
- Centralized metric collection through Alloy:
  - Node metrics (CPU, memory, disk, network) from all 6 VMs
  - Container metrics (cAdvisor) from all 6 VMs
  - All Docker container logs centralized through Loki

**2025-11-12 - Development Stack Deployment:** ✅ Complete

**Tempo v2.9.0 (Distributed Tracing):**
- ✅ Added to observability/docker-compose.yml
- ✅ Created tempo.yml config with MinIO storage backend
- ✅ Configured 90-day trace retention
- ✅ OTLP receivers (gRPC:4317, HTTP:4318)
- ✅ Metrics generator → Prometheus remote_write
- ✅ Added Traefik route: tempo.onurx.com (private)
- ✅ Environment variables configured in .env
- ✅ Created MinIO bucket `tempo-traces`
- ✅ Deployed and running on observability VM (10.10.10.112)
- ⏳ Pending: Add Tempo datasource to Grafana
- ⏳ Pending: Configure Alloy to send traces

**Hoppscotch 2025.10.0 (API Testing):**
- ✅ Added to dev/docker-compose.yml (All-in-one image)
- ✅ Configured external PostgreSQL connection
- ✅ Enabled subpath-based access (/, /admin, /backend)
- ✅ Added Traefik route: api.onurx.com (private)
- ✅ Environment variables configured in .env
- ✅ Created 1Password entries (hoppscotch-db, hoppscotch)
- ✅ Created PostgreSQL database `hoppscotch`
- ✅ Deployed and running on dev VM (10.10.10.114)
- ✅ Ran Prisma migrations (16 migrations applied)
- ⏳ Pending: Create first admin user via web UI

**Access URLs:**
- Hoppscotch: https://api.onurx.com (private)
- Hoppscotch Admin: https://api.onurx.com/admin (private)

**Note:** Tempo has no web UI - access traces through Grafana → Explore → Tempo datasource

### Critical Action Items

**🔴 HIGH PRIORITY:**
1. **Hoppscotch First Admin User** - Create via web UI at https://api.onurx.com/admin
2. **Grafana Dashboards** - Add Synology to Systems Overview (metrics ready, needs manual UI work)
3. **Authentication** - Authentik deployed but no applications configured
4. **Resource Limits** - No CPU/memory limits on containers
5. **Health Checks** - Several services missing health checks
6. **VM 100 Backup Fix** - Xpenology backup timeout (needs QEMU guest agent disabled)

**🟡 MEDIUM PRIORITY:**
1. **SSL Migration** - Route more services via Traefik (AdGuard, Portainer)
2. **Synology Dashboards** - Create detailed Grafana dashboard using 150 available SNMP metrics

**✅ COMPLETED:**
1. **Backup Strategy** - PBS deployed (VM 120), automated backups configured for all VMs
2. **Dashboard Updates** - All dashboards updated to use new label structure (instance), fixed queries
3. **Synology SNMP Monitoring** - 150 metrics via Alloy (CPU, memory, load, network, disk, RAID)
4. **Home Assistant Integration** - 54 entity metrics via Prometheus integration
5. **Monitoring Migration** - Alloy deployed across all VMs, standardized labels, centralized collection
6. **NAS Mount Monitoring** - Prometheus alert configured for media VM NAS mount
7. **Media Stack** - All services deployed (Plex, SABnzbd, Sonarr, Radarr, etc.)

**🟢 LOW PRIORITY:**
1. **Cloudflare Tunnels** - Migrate from direct DNS (blocked by email migration)
2. **SSL Certificate Monitoring** - Add Prometheus alerts for cert expiry

### Development Stack Roadmap

**Observability & Monitoring:**
- ✅ **Grafana** - Dashboards and visualization
- ✅ **Prometheus** - Metrics storage (90 day retention)
- ✅ **Loki** - Log aggregation (90 day retention)
- ✅ **Alloy** - Metrics and logs collection (deployed on all VMs)
- ✅ **Netdata** - Real-time infrastructure metrics (deployed on all VMs)
- ✅ **Tempo v2.9.0** - Distributed tracing (deployed)
  - Location: observability VM (10.10.10.112)
  - Storage: MinIO S3-compatible (db VM)
  - Retention: 90 days
  - OTLP receivers: gRPC (4317), HTTP (4318)
  - Traefik: https://tempo.onurx.com (private)
  - Status: Running and healthy

**Application Development:**
- ✅ **Gitea** - Git hosting, Actions, Container Registry
- ✅ **GitHub Runner** - Self-hosted CI/CD
- ✅ **Coolify** - Application deployment platform
- ✅ **Hoppscotch 2025.10.0** - API development and testing (deployed)
  - Location: dev VM (10.10.10.114)
  - Storage: PostgreSQL on db VM (10.10.10.111)
  - Features: API testing, team collaboration, collections, mock servers
  - Traefik: https://api.onurx.com (private)
  - Status: Running, migrations applied, ready for first admin user

**Code Quality & Security:**
- 📋 **SonarQube** - Code quality, security scanning, tech debt tracking (planned)
  - Storage: PostgreSQL on db VM (10.10.10.111)
  - Features: Static analysis, security vulnerabilities, code coverage
  - Integration: Gitea Actions, GitHub Runner
  - Deploy location: dev VM (10.10.10.114)
- 📋 **Trivy** - Container and dependency security scanning (planned)
  - Type: CLI tool (no server required)
  - Integration: CI/CD pipelines (Gitea Actions, GitHub Actions)
  - Scans: Container images, filesystems, Git repositories, Kubernetes manifests

**Error Tracking:**
- 📋 **Sentry** - Error tracking, crash reporting, performance monitoring (planned)
  - Storage: PostgreSQL (10.10.10.111), Redis (10.10.10.111), ClickHouse (self-hosted)
  - Additional: Kafka, Memcached (required by Sentry)
  - Features: Stack traces, error trends, performance APM, release tracking
  - Integration: All application SDKs (Python, Node.js, Go, etc.)
  - Deploy location: observability VM (10.10.10.112)

**Testing Infrastructure:**
- 📋 **k6** - Load and performance testing (planned)
  - Type: CLI tool (optional InfluxDB for metrics storage)
  - Integration: CI/CD pipelines
  - Features: JavaScript-based tests, Grafana integration
- 📋 **Playwright** - End-to-end browser testing (planned)
  - Type: CLI tool (no server required)
  - Integration: CI/CD pipelines
  - Features: Multi-browser support (Chromium, Firefox, WebKit)

**Message Broker:**
- ✅ **Mosquitto** - MQTT for IoT communication
- ✅ **Redis** - Pub/sub, queuing, caching
- ⏸️ **RabbitMQ/NATS** - Advanced message broker (deferred)
  - Decision: Use Redis Streams for now, evaluate need later

**Deployment Priority:**
1. **Phase 1:** ✅ Tempo, Hoppscotch (DEPLOYED)
2. **Phase 2 (Next):** SonarQube, Trivy (integrate with CI/CD)
3. **Phase 3:** Sentry (requires ClickHouse + Kafka setup)
4. **Phase 4:** k6, Playwright (as needed for projects)

### Network Information

- VLAN 10: 10.10.10.0/24
- Gateway: 10.10.10.1
- DNS: AdGuard Home (10.10.10.110)
- Wildcard DNS: `*.onurx.com` → 10.10.10.110
- VPN: NetBird (100.92.0.0/16)

### Access URLs

**Management:**
- Homarr: https://home.onurx.com
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
- Hoppscotch: https://api.onurx.com

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

**Last Updated:** 2025-11-07
