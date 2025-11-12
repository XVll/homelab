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

**Kafka + Zookeeper:**
- Kafka Port: 9092
- Zookeeper Port: 2181
- Connection: `kafka://10.10.10.111:9092`
- Topic auto-creation enabled

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
- ✅ Environment variables configured in .env
- ✅ Created MinIO bucket `tempo-traces`
- ✅ Deployed and running on observability VM (10.10.10.112)
- ✅ Added Tempo datasource to Grafana with full integration
- ⏳ Pending: Configure applications to send traces to Tempo

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

**Using Tempo:**
- Access: Grafana → Explore → Select "Tempo" datasource
- Query traces by TraceID or search
- Tempo automatically correlates with Prometheus metrics and Loki logs
- Send traces: OTLP gRPC endpoint at `http://10.10.10.112:4317`

### AI Development Infrastructure (Planning Phase)

**Status:** 📋 Under evaluation - Not yet deployed

This section documents the AI infrastructure stack being planned for building AI-powered applications, agents, and automation workflows. The focus is on:
- AI agents performing autonomous tasks (decision-making, file manipulation, function calling)
- Document processing and manipulation
- Background AI workflows
- Chatbot interfaces
- System integration and automation

---

#### Core AI Infrastructure

**AI Gateway & Proxy:**
- 📋 **LiteLLM** - Universal API gateway for LLM providers (planned)
  - **Purpose:** Single unified API for multiple LLM providers (OpenAI, Anthropic, Ollama, Azure)
  - **Features:** Load balancing, automatic fallbacks, cost tracking, rate limiting, response caching
  - **Why needed:** Cost optimization, reliability (fallbacks), unified interface for all AI providers
  - **Deployment:** dev VM (10.10.10.114)
  - **Integration:** All applications call LiteLLM instead of direct provider APIs
  - **Configuration:** Provider credentials, model routing rules, caching policies
  - **Example use:** App calls LiteLLM → routes to cheapest available model → falls back if primary fails

**AI Observability:**
- 📋 **Langfuse** - LLM observability and analytics platform (planned)
  - **Purpose:** Track, debug, and optimize all AI interactions
  - **Features:**
    - Trace every LLM call with full context (prompts, completions, latency, costs)
    - Cost tracking per user, per feature, per model
    - Prompt versioning and A/B testing
    - User analytics (who's using AI features, quality ratings)
    - Performance metrics (token usage, error rates, latency)
  - **Why critical:** Without observability, impossible to debug issues or control costs
  - **Deployment:** dev VM (10.10.10.114)
  - **Storage:** PostgreSQL on db VM (10.10.10.111)
  - **Integration:** LiteLLM logs to Langfuse automatically, SDKs for direct instrumentation
  - **Example queries:**
    - "Why is my AI bill $500 this month?" → See breakdown by user/feature/model
    - "Which prompts are failing most?" → View error rates and examples
    - "How much does feature X cost per request?" → See average cost analysis

**Vector Database (RAG):**
- 📋 **Qdrant** - High-performance vector database for semantic search (planned)
  - **Purpose:** Store and search document embeddings for RAG (Retrieval Augmented Generation)
  - **Features:**
    - Fast similarity search (find relevant documents for AI context)
    - Filtering and metadata (search by date, category, user, etc.)
    - Multi-tenancy support (separate data per user/organization)
    - Payload storage (store original text + embeddings together)
  - **Why needed:** Enable AI to answer questions using your documents/data
  - **Deployment:** db VM (10.10.10.111) - data infrastructure tier
  - **Use cases:**
    - Document Q&A: "What does contract X say about Y?"
    - Semantic search: Find similar documents/support tickets
    - Agent memory: Store conversation history, retrieve relevant context
    - Knowledge base: AI answers using your documentation
  - **Integration:** Apps generate embeddings (via LiteLLM) → store in Qdrant → query for relevant chunks
  - **Storage:** Persistent volume, scales to millions of vectors

**Document Processing:**
- 📋 **Unstructured.io** - Advanced document extraction and processing (planned)
  - **Purpose:** Extract structured data from documents for AI consumption
  - **What it extracts:**
    - Text with layout preservation (headers, paragraphs, lists)
    - Tables (converted to markdown/JSON)
    - Images with descriptions
    - Metadata (author, date, document type)
  - **Features:**
    - OCR support for scanned documents
    - Intelligent chunking for LLMs (preserves context)
    - 1000+ file format support (PDF, Word, Excel, images, etc.)
    - Self-hosted REST API
  - **Why better than simple extraction:**
    - Preserves document structure (AI understands context better)
    - Chunks intelligently (doesn't break mid-sentence)
    - Handles complex layouts (multi-column PDFs, scientific papers)
  - **Deployment:** dev VM (10.10.10.114)
  - **Alternative options evaluated:**
    - Apache Tika: Simple text extraction (no structure, no tables, no OCR)
    - Docling (IBM): Best for complex PDFs, but Python-only, no REST API
    - LlamaParse: Commercial cloud API (not self-hosted)
  - **Example workflow:**
    1. Upload PDF to app → store in MinIO
    2. App calls Unstructured API → returns structured chunks
    3. App generates embeddings (LiteLLM) → stores in Qdrant
    4. User asks question → app searches Qdrant → sends relevant chunks to AI

**Workflow Automation:**
- 📋 **n8n** - Visual workflow automation platform (planned)
  - **Purpose:** Automate AI-driven workflows across systems (no-code/low-code)
  - **Features:**
    - 400+ integrations (email, Slack, databases, APIs, webhooks, file storage)
    - Visual workflow builder (drag-and-drop)
    - Built-in AI nodes (OpenAI, Anthropic, LangChain)
    - Conditional logic (IF/ELSE based on AI decisions)
    - Error handling (retries, fallbacks, notifications)
    - Cron scheduling and webhook triggers
  - **Why needed:** Connect AI decisions to real-world actions
  - **Deployment:** dev VM (10.10.10.114)
  - **Storage:** PostgreSQL on db VM (10.10.10.111)
  - **Use cases:**
    - **Document uploaded** → Extract text → AI summarizes → Send to Slack
    - **Email received** → AI categorizes → Route to correct department
    - **Event occurs** → AI decides action → Execute (notify, create ticket, update DB)
    - **Schedule: daily** → AI analyzes reports → Sends summary email
  - **Integration with existing:**
    - Triggers: Webhooks from your apps, scheduled tasks, file uploads (MinIO)
    - Actions: Call any API, send email, update database, run scripts
    - AI: LiteLLM for AI calls, Qdrant for context retrieval
  - **vs Inngest:**
    - n8n: Visual workflows, system integration, no-code (homelab automation + prototyping)
    - Inngest: Code-first AI workflows (TypeScript/Python) for production app features
    - **Use both:** n8n for homelab automation, Inngest for app-integrated AI tasks

---

#### AI Architecture for Web Applications

**Primary use case:** AI-powered features in custom web apps (.NET, TypeScript, etc.)

**Proposed Architecture:**
```
[Web Application (.NET/TypeScript)]
    ↓ (API call)
[LiteLLM Proxy] → OpenAI/Anthropic/Ollama
    ↓ (logs all calls)
[Langfuse] → Observability dashboard

[Web Application]
    ↓ (background task)
[RabbitMQ] → Event queue
    ↓ (worker consumes)
[Inngest Worker] → AI processing
    ↓ (retrieve context)
[Qdrant] → Relevant documents
    ↓ (call AI with context)
[LiteLLM] → AI response
    ↓ (store result)
[RabbitMQ] → Notify app
    ↓
[Web Application] → Display to user
```

**Example: Document Processing Workflow**
1. User uploads invoice (PDF) in web app
2. App stores in MinIO, sends event to RabbitMQ: `{type: "document.uploaded", id: "123"}`
3. Inngest worker receives event
4. Worker calls Unstructured API → extracts: vendor, amount, due date, line items
5. Worker generates embeddings (LiteLLM) → stores in Qdrant
6. Worker calls LiteLLM with context: "Summarize this invoice and flag if urgent"
7. AI analyzes: Amount $15K + due in 3 days = urgent
8. Worker sends result to RabbitMQ
9. Web app receives notification, shows summary + "URGENT" flag to user
10. Langfuse logs entire workflow: prompts, tokens, cost, latency

**Example: AI Decision-Making Workflow (via n8n)**
1. Customer support email arrives
2. n8n webhook receives email
3. n8n calls Unstructured → extracts email content
4. n8n searches Qdrant → finds similar past tickets
5. n8n calls LiteLLM: "Categorize this email: billing/tech/sales. Is it urgent?"
6. AI responds: "Category: billing, Urgency: high, Reason: account suspended"
7. n8n executes decision:
   - IF urgent + billing → Create high-priority ticket + notify billing team via Slack
   - IF tech + low → Create ticket + auto-respond with knowledge base article
8. Langfuse tracks cost, latency, decision quality

---

#### Document Processing Pipeline Options

**Goal:** Convert documents (PDF, Word, scanned images) into AI-ready chunks with embeddings

**Pipeline Stages:**
```
1. EXTRACTION  → Get text/data from files
2. CHUNKING    → Split into manageable pieces
3. ENRICHMENT  → Add metadata, clean up
4. EMBEDDING   → Convert to vectors
5. STORAGE     → Store in vector DB (Qdrant)
6. RETRIEVAL   → Search when needed (RAG)
```

**Extraction Tool Comparison:**

| Tool | Complexity | Structure | Tables | OCR | Best For |
|------|-----------|----------|--------|-----|----------|
| **Unstructured** | ⭐⭐⭐ | ✅ Yes | ✅ Yes | ✅ Yes | RAG, AI apps (recommended) |
| Apache Tika | ⭐ | ❌ No | ❌ No | ❌ No | Simple text extraction |
| Docling (IBM) | ⭐⭐⭐ | ✅ Yes | ✅ Yes | ✅ Yes | Complex PDFs (no REST API) |
| LlamaParse | ⭐ | ✅ Yes | ✅ Yes | ✅ Yes | Cloud SaaS (not self-hosted) |

**Recommended Pipeline (Option 1 - Best Quality):**
```
Document upload → Unstructured API → Structured chunks + tables + images
                       ↓
                  LiteLLM (OpenAI embeddings) → Vectors
                       ↓
                  Qdrant → Store chunks + vectors + metadata
                       ↓
              User query → Search Qdrant → Retrieve relevant chunks
                       ↓
              LiteLLM (with context) → AI answer
```

**Cost-Optimized Pipeline (Option 2 - Free Embeddings):**
```
Document → Unstructured → Chunks
              ↓
         Ollama (local embeddings) → Vectors (free, no API costs)
              ↓
         Qdrant → Storage
```
⚠️ **Requires:** GPU for acceptable performance (or very slow on CPU)

**Simple Pipeline (Option 3 - Basic Documents):**
```
Document → Apache Tika → Plain text
              ↓
         Manual chunking → Fixed-size chunks
              ↓
         LiteLLM (embeddings) → Qdrant
```
✅ **Good for:** Simple documents (emails, basic PDFs, text files)

**Chunking Strategies:**
- **Fixed-size:** Split every N tokens (simple, breaks context)
- **Semantic:** Split by paragraphs/sections (preserves meaning) ← Unstructured default
- **Recursive:** Try section → paragraph → sentence → tokens (best quality) ← LangChain

**Embedding Options:**
| Option | Cost | Quality | Speed | Privacy |
|--------|------|---------|-------|---------|
| OpenAI (via LiteLLM) | $$$ | ⭐⭐⭐⭐⭐ | Fast | Cloud |
| Anthropic (via LiteLLM) | $$$ | ⭐⭐⭐⭐⭐ | Fast | Cloud |
| Ollama (local) | Free | ⭐⭐⭐⭐ | Slow (CPU) / Fast (GPU) | Self-hosted |
| Sentence Transformers | Free | ⭐⭐⭐⭐ | Medium | Self-hosted |

---

#### Optional Components (Not Planned Yet)

**Local LLM Inference:**
- 📋 **Ollama** - Run open-source LLMs locally (Llama 3, Mistral, etc.)
  - **Pros:** Free inference, data privacy, good for embeddings/classification
  - **Cons:** Requires GPU for acceptable speed, lower quality than GPT-4/Claude
  - **Use cases:** Embeddings (free), simple tasks, cost optimization
  - **Decision:** Skip for now, add later if GPU available and cost becomes issue

**AI App Builder (Low Priority):**
- 📋 **Dify** - No-code AI application builder
  - **Purpose:** Visual builder for AI chatbots, agents, RAG apps
  - **Features:** Drag-and-drop agent creation, built-in RAG, pre-built templates
  - **Why skipping:** Redundant with n8n + Inngest + custom development
  - **When to add:** If non-developers need to build AI features quickly
- 📋 **Flowise** - Alternative to Dify (lighter, more developer-friendly)
  - **Purpose:** Visual LangChain workflow builder
  - **Pro:** Exports to code, lighter than Dify
  - **Decision:** Choose Dify OR Flowise if needed (not both)

---

#### Deployment Plan (Not Started)

**Phase 1 - Core Infrastructure (Essential):**
1. **Langfuse** - AI observability (CRITICAL - deploy first)
2. **LiteLLM** - AI gateway (CRITICAL)
3. **Qdrant** - Vector database (CRITICAL for RAG)
4. **n8n** - Workflow automation
5. **Unstructured** - Document processing

**Already Deployed (Reuse):**
- ✅ Inngest - AI workflow orchestration (dev VM)
- ✅ RabbitMQ - Message queue for app ↔ AI communication (db VM)
- ✅ PostgreSQL - Shared by Langfuse, n8n (db VM)
- ✅ Redis - Shared state/caching (db VM)
- ✅ MinIO - Document storage (db VM)

**Phase 2 - Optional (Add Later):**
- Ollama - Local LLM inference (if GPU available)
- Dify or Flowise - If rapid prototyping needed

**Estimated Resource Requirements:**
- CPU: +4-6 cores total
- Memory: +8-12GB RAM
- Storage: +20-50GB (depends on document volume)
- Network: Outbound to AI provider APIs (OpenAI/Anthropic)

---

#### Integration with Existing Stack

**Databases (db VM - 10.10.10.111):**
- PostgreSQL: Langfuse, n8n
- Redis: Shared caching, Inngest state
- MinIO: Document storage (PDFs, images, generated files)
- Qdrant: Vector embeddings

**Monitoring (observability VM - 10.10.10.112):**
- Prometheus: LiteLLM metrics (request count, latency, errors)
- Grafana: AI dashboards (cost, usage, performance)
- Loki: All AI service logs
- Alloy: Metrics + log collection from AI services

**Development (dev VM - 10.10.10.114):**
- Inngest: AI workflow orchestration (already deployed)
- LiteLLM: AI gateway (planned)
- Langfuse: AI observability (planned)
- n8n: Workflow automation (planned)
- Unstructured: Document processing (planned)

**Reverse Proxy (edge VM - 10.10.10.110):**
- Traefik routes for all AI services (private by default)
- SSL termination via Cloudflare

**Proposed Traefik Routes (all private):**
- `langfuse.onurx.com` → Langfuse UI
- `litellm.onurx.com` → LiteLLM proxy (API endpoint)
- `qdrant.onurx.com` → Qdrant API + dashboard
- `n8n.onurx.com` → n8n workflow editor
- `unstructured.onurx.com` → Unstructured API

---

#### Questions to Resolve

**Before deployment, need to decide:**

1. **LLM Providers:**
   - Which APIs to use? (OpenAI, Anthropic, both?)
   - API keys already in 1Password?
   - Cost budget per month?

2. **GPU Availability:**
   - Do we have GPU for Ollama (local embeddings)?
   - Or rely on cloud APIs only?

3. **Document Types:**
   - What file types most important? (PDF, Word, Excel, images, scanned docs?)
   - Average document size and volume?

4. **Use Case Priority:**
   - Start with chatbot, document Q&A, or automation first?
   - Which AI features in apps are highest priority?

5. **Cost Optimization:**
   - Use expensive models (GPT-4, Claude Sonnet) or cheaper (GPT-3.5, Haiku)?
   - LiteLLM routing rules (try cheap model first, escalate if needed)?

---

#### Reference Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER WEB APPLICATION                        │
│                    (.NET / TypeScript / etc.)                   │
└───────────┬─────────────────────────────────────┬───────────────┘
            │                                     │
            │ Direct API calls                    │ Background tasks
            ↓                                     ↓
    ┌───────────────┐                   ┌─────────────────┐
    │   LiteLLM     │                   │   RabbitMQ      │
    │  AI Gateway   │                   │  Message Queue  │
    └───────┬───────┘                   └────────┬────────┘
            │                                    │
            ├─→ OpenAI                           ↓
            ├─→ Anthropic               ┌─────────────────┐
            ├─→ Ollama (local)          │ Inngest Worker  │
            │                           │  (TypeScript)   │
            ↓                           └────────┬────────┘
    ┌───────────────┐                           │
    │   Langfuse    │←──────────────────────────┤
    │ Observability │                           │
    └───────────────┘                           ↓
                                        ┌────────────────┐
    ┌───────────────┐                  │  Unstructured  │
    │     n8n       │                  │   Doc Extract  │
    │  Automation   │                  └────────┬───────┘
    └───────┬───────┘                           │
            │                                   ↓
            ├────────────────────────→  ┌───────────────┐
            │                           │    Qdrant     │
            │                           │  Vector DB    │
            │                           └───────────────┘
            ↓
    ┌───────────────┐
    │ Email/Slack/  │
    │ DB/API calls  │
    └───────────────┘
```

---

**Status:** This section will be updated as we refine requirements, test tools, and begin deployment.

---

### Critical Action Items

**🔴 HIGH PRIORITY:**
1. **Authentication** - Authentik deployed but no applications configured (includes Hoppscotch SSO)
2. **Grafana Dashboards** - Add Synology to Systems Overview (metrics ready, needs manual UI work)
3. **Resource Limits** - No CPU/memory limits on containers
4. **Health Checks** - Several services missing health checks
5. **VM 100 Backup Fix** - Xpenology backup timeout (needs QEMU guest agent disabled)

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
- ✅ **SonarQube Community Edition** - Code quality, security scanning, tech debt tracking (deployed)
  - Location: dev VM (10.10.10.114)
  - Storage: PostgreSQL on db VM (10.10.10.111)
  - Features: Static analysis, security vulnerabilities, code coverage, tech debt
  - Integration: Gitea Actions, GitHub Runner
  - Traefik: https://sonar.onurx.com (private)
  - Status: Running, default credentials admin/admin (change on first login)
- 📋 **Trivy** - Container and dependency security scanning (planned)
  - Type: CLI tool (no server required)
  - Integration: CI/CD pipelines (Gitea Actions, GitHub Actions)
  - Scans: Container images, filesystems, Git repositories, Kubernetes manifests

**Search & Discovery:**
- ✅ **Meilisearch v1.12** - Fast, typo-tolerant search engine (deployed)
  - Location: dev VM (10.10.10.114)
  - Storage: Embedded LMDB database (local disk)
  - Features: Full-text search, typo tolerance, faceted search, filtering, geo search
  - Use cases: Product search, documentation, autocomplete, content discovery
  - Authentication: Master key (1Password)
  - Traefik: https://search.onurx.com (private)
  - Status: Running, health check passing

**AI/Workflow Orchestration:**
- ✅ **Inngest (Self-Hosted)** - AI agent and workflow orchestration platform (deployed)
  - Location: dev VM (10.10.10.114)
  - Storage: PostgreSQL (10.10.10.111), Redis (10.10.10.111)
  - Ports: 8288 (API), 8289 (Connect Gateway)
  - Features: AI workflows with built-in retries, LLM streaming support, token tracking, multi-agent orchestration
  - Use cases: AI agents, multi-step LLM workflows, background jobs, event-driven architecture
  - SDK Support: TypeScript/JavaScript, Python, Go (no .NET support yet)
  - Traefik: https://inngest.onurx.com (private)
  - Status: Running, all services healthy (API, executor, runner, connect-gateway)

**Error Tracking:**
- 📋 **Sentry Cloud (Free Tier)** - Error tracking, crash reporting, performance monitoring (SaaS)
  - Decision: Use Sentry Cloud instead of self-hosted (requires 50+ containers, 32GB RAM)
  - Free tier: 5K errors/month, 10K performance units/month
  - Features: Stack traces, error trends, performance APM, release tracking
  - Integration: All application SDKs (Python, Node.js, Go, etc.)
  - Sign up: https://sentry.io

**Testing Infrastructure:**
- 📋 **k6** - Load and performance testing (planned)
  - Type: CLI tool (optional InfluxDB for metrics storage)
  - Integration: CI/CD pipelines
  - Features: JavaScript-based tests, Grafana integration
- 📋 **Playwright** - End-to-end browser testing (planned)
  - Type: CLI tool (no server required)
  - Integration: CI/CD pipelines
  - Features: Multi-browser support (Chromium, Firefox, WebKit)

**Event Streaming:**
- ✅ **Kafka 7.8.0 + Zookeeper** - Event streaming platform (deployed)
  - Location: db VM (10.10.10.111)
  - Ports: 9092 (Kafka), 2181 (Zookeeper)
  - Use cases: Event streaming, microservices communication, data pipelines, real-time analytics
  - Integration: Event-driven applications, data pipelines

**Message Brokers:**
- ✅ **RabbitMQ 4.0** - AMQP message broker with Management UI (deployed)
  - Location: db VM (10.10.10.111)
  - Ports: 5672 (AMQP), 15672 (Management UI)
  - Use cases: Task queues (Celery), pub/sub patterns, RPC, microservices messaging
  - Features: Queue management, message routing, dead letter queues, priority queues
  - Traefik: https://rabbitmq.onurx.com (private)
  - Status: Running, health check passing
- ✅ **Mosquitto MQTT** - Lightweight IoT message broker (deployed)
  - Location: db VM (10.10.10.111)
  - Port: 1883 (MQTT)
  - Use cases: IoT devices, Home Assistant bridge
- ✅ **Redis** - Pub/sub, streams, queuing, caching (deployed)
  - Location: db VM (10.10.10.111)
  - Port: 6379

**Deployment Priority:**
1. **Phase 1:** ✅ Tempo, Hoppscotch (DEPLOYED)
2. **Phase 2:** ✅ SonarQube, Kafka (DEPLOYED) | 📋 Trivy (integrate with CI/CD when needed)
3. **Phase 3:** Sentry Cloud (use SaaS free tier instead of self-hosted)
4. **Phase 4:** k6, Playwright, additional services (add as needed for projects)

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
- RabbitMQ: https://rabbitmq.onurx.com

**Development:**
- Gitea: https://git.onurx.com
- Coolify: https://deploy.onurx.com
- Hoppscotch: https://api.onurx.com
- SonarQube: https://sonar.onurx.com
- Meilisearch: https://search.onurx.com
- Inngest: https://inngest.onurx.com

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
