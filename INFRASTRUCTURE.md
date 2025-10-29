# Infrastructure Progress & Notes

**Single source of truth for homelab build progress and quick reference notes.**


## Current Progress


### Phase 1: Foundation ✅ DONE
- [x] MongoDB (db host - 10.10.10.111)
- [x] PostgreSQL (db host - 10.10.10.111)
- [x] Redis (db host - 10.10.10.111)
- [x] MinIO (db host - 10.10.10.111)
- [x] Mosquitto MQTT (db host - 10.10.10.111:1883) - For Home Assistant bridge application
- [x] Portainer (observability host - 10.10.10.112)

### Phase 2: Edge Services ✅ DONE
- [x] Traefik (edge host - 10.10.10.110) - Deployed, SSL working, auto-reload enabled
- [x] AdGuard Home (edge host - 10.10.10.110) - Deployed, configured, DNS rewrites active
- [x] Authentik SSO (edge host - 10.10.10.110) - Deployed, ready to configure (admin: akadmin)
- [x] NetBird VPN (edge host - 10.10.10.110) - Client deployed, connected to NetBird cloud

### Phase 3: Observability ✅ DONE
- [x] Prometheus v3.1.0 (observability host - 10.10.10.112) - Metrics storage, 90-day retention
- [x] Grafana 11.4.0 (observability host - 10.10.10.112) - Dashboards and visualization
- [x] Loki 3.3.2 (observability host - 10.10.10.112) - Log aggregation, 90-day retention, filesystem storage
- [x] Alloy v1.11.2 (observability host - 10.10.10.112) - Collects metrics + logs from observability VM
- [x] Alloy (db host - 10.10.10.111) - Logs-only shipper, sends to central Loki
- [x] Alloy (edge host - 10.10.10.110) - Logs-only shipper, sends to central Loki
- [x] Alloy (media host - 10.10.10.113) - Logs-only shipper, sends to central Loki
- [x] Alloy (dev host - 10.10.10.114) - Logs-only shipper, sends to central Loki
- [x] Alloy (deploy host - 10.10.10.115) - Logs-only shipper, sends to central Loki
- [x] **Centralized Logging** - All Docker logs from all VMs flow to Loki, queryable in Grafana
- [x] Beszel Hub (observability host - 10.10.10.112:8090) - Lightweight monitoring dashboard
- [x] Beszel Agent (edge VM) - System + Docker metrics
- [x] Beszel Agent (db VM) - System + Docker metrics
- [x] Beszel Agent (dev VM) - System + Docker metrics
- [x] Beszel Agent (media VM) - System + Docker metrics
- [x] Beszel Agent (observability VM) - System + Docker metrics
- [x] Beszel Agent (deploy VM) - System + Docker metrics
- [x] Beszel Agent (ha VM) - System metrics (Home Assistant OS addon)
- [x] **Quick Monitoring** - Real-time CPU, memory, disk, network, Docker stats for all VMs
- [x] **✅ Full Infrastructure Monitoring Audit Complete (2025-10-28)**
  - All VMs now have Alloy + Beszel monitoring
  - Health checks added to all services where applicable
  - DNS fixed on all VMs (removed 10.10.10.1 gateway, using only AdGuard 10.10.10.110)
  - Portainer Agents deployed on edge, db, dev, media VMs (NOT on deploy/ha - handled by Dokploy/HA OS)
  - All services healthy and reporting to central observability stack
- [x] **✅ VirtioFS Migration Complete** - All VMs migrated to standard git workflow (2025-10-27)
  - Removed VirtioFS mounts from all VMs
  - Configured git remotes to Gitea (https://git.onurx.com/fx/homelab)
  - Repository made public (no auth needed for pulls)
  - All services restarted with proper 1Password secrets
  - Fixed data directory permissions (Grafana, Loki, Prometheus)
  - **Media VM (10.10.10.113) recreated** - Old VM had issues, cloned fresh from template
  - **DNS fixed** - Restarted systemd-resolved on all VMs, AdGuard DNS rewrites working
  - **Logging standardized** - All services now log to stdout for Docker log collection
    - Traefik: Removed file logging, now logs to stdout
    - PostgreSQL: Disabled logging_collector, logs to stderr
    - MongoDB: Removed file destination, defaults to stdout
  - **Result**: All 17 containers across 4 VMs sending logs to Loki/Grafana

### Phase 4: Applications ⏳ IN PROGRESS
- [ ] Jellyfin, Arr Stack, qBittorrent (media host - 10.10.10.113)
- [ ] n8n, Paperless (media host - 10.10.10.113)
- [x] **Gitea** (dev host - 10.10.10.114:3001) - Git hosting + Container Registry + Gitea Actions
- [x] **act_runner** (dev host - 10.10.10.114) - Self-hosted CI/CD runner for Gitea Actions (works for ALL repos)
- [x] **GitHub → Gitea Mirror Workflow** - Push to GitHub, auto-mirror to Gitea, CI/CD runs on act_runner
- [x] **Dokploy** (deploy host - 10.10.10.115:3000) - Deployment platform, accessible via https://deploy.onurx.com
- [x] **Home Assistant** (ha host - 10.10.10.116:8123) - Home automation platform, accessible via https://ha.onurx.com

---

## TODO - Infrastructure Audit & Action Items

**Last Audit:** 2025-10-28

### 🔴 CRITICAL - Must Fix Immediately

**1. Database Backups Missing:**
- [ ] MongoDB - No backup strategy (critical data!)
- [ ] PostgreSQL - No backup strategy (critical data!)
- [ ] MinIO - No backup strategy (critical data!)
- [ ] Gitea repos - No backup configured
- **Action:** Implement automated backup solution (Restic, borgmatic, or custom scripts)
- **Priority:** CRITICAL

**2. ✅ COMPLETED - Monitoring Agents Deployed:**
- [x] dev VM (10.10.10.114) - Alloy, Beszel, Portainer agent deployed
- [x] deploy VM (10.10.10.115) - Alloy, Beszel deployed (no Portainer - Dokploy handles management)
- [x] ha VM (10.10.10.116) - Beszel addon installed (Home Assistant OS)
- [x] observability VM (10.10.10.112) - All services audited, health checks added
- **Status:** COMPLETE (2025-10-28)

**3. Authentication & Security Gaps:**
- [ ] Prometheus - No authentication (anyone can query metrics)
- [ ] Loki - No authentication (anyone can query logs)
- [ ] Alloy UI - No authentication (config/metrics exposed)
- [ ] Traefik dashboard (port 8080) - Exposed without protection
- [ ] Authentik - No applications configured yet (SSO not working!)
- **Action:** Configure Authentik applications + add auth to all services
- **Priority:** CRITICAL

**4. Resource Limits Missing:**
- [ ] All database containers (MongoDB, PostgreSQL, Redis, MinIO) - No CPU/memory limits
- [ ] All application containers - No resource constraints
- **Action:** Add resource limits to prevent resource exhaustion
- **Priority:** HIGH

### 🟡 MEDIUM - Should Complete Soon

**5. Monitoring Configuration Gaps:**
- [ ] Beszel Hub - Not using HTTPS/Traefik (port 8090 exposed)
- [ ] AdGuard - Not using HTTPS (port 8888, HTTP only)
- [ ] Portainer - Not via Traefik (direct HTTPS on 9443)
- [ ] Grafana - Should use Authentik SSO instead of own login
- **Action:** Route services via Traefik with proper SSL
- **Priority:** MEDIUM

**6. Health Checks Missing:**

**db VM (10.10.10.111):**
- ✅ MongoDB - Has health check
- ✅ PostgreSQL - Has health check
- ✅ Redis - Has health check
- ✅ MinIO - Has health check
- ❌ Alloy - No health check
- ✅ Beszel Agent - Has health check

**edge VM (10.10.10.110):**
- ✅ Traefik - Has health check
- ❌ AdGuard - No health check
- ❌ Authentik Server - No health check
- ❌ Authentik Worker - No health check
- ❌ NetBird - No health check (N/A - stateless VPN client)
- ❌ Alloy - No health check
- ✅ Beszel Agent - Has health check

**observability VM (10.10.10.112):**
- ❌ Portainer - No health check
- ✅ Prometheus - Has health check
- ✅ Grafana - Has health check
- ✅ Loki - Has health check
- ❌ Alloy - No health check (no wget/curl in image)
- ✅ Beszel Hub - Has health check
- ✅ Beszel Agent - Has health check

**media VM (10.10.10.113):**
- ❌ Alloy - No health check
- ✅ Beszel Agent - Has health check

**dev VM (10.10.10.114):**
- ✅ Gitea - Has health check
- ❌ act_runner - No health check
- N/A postgres-check - Init container only

**Action:** Add health checks to all services where possible (Alloy doesn't have wget/curl, NetBird is stateless)
- **Priority:** MEDIUM

**7. Synology NAS Audit:**
- [ ] Document what services run on Synology
- [ ] Check if Synology is monitored (Beszel agent possible?)
- [ ] Verify Synology backup configuration
- [ ] Check if Synology logs go to Loki
- **Action:** Audit Synology and integrate with monitoring stack
- **Priority:** MEDIUM

### 🟢 LOW - Nice to Have

**8. Service Testing:**
- [ ] Gitea Actions - Test CI/CD workflow
- [ ] Gitea Container Registry - Test docker push/pull
- [ ] Dokploy - Deploy test application
- [ ] Repository mirroring - Test GitHub sync
- **Priority:** LOW

**9. SSL Certificate Monitoring:**
- [ ] No alerts if certificates fail to renew
- [ ] Should add Prometheus alert for cert expiry
- **Priority:** LOW

**10. Cloudflare Tunnels Migration (Planned):**
- [ ] Current setup works but exposes IP via onurx.com A record
- [ ] Plan: Move to Cloudflare Tunnels for better security
- **Blocker:** Email service uses @onurx.com - must migrate email first
- **Priority:** LOW (current setup is secure with IP whitelist)

### 📊 VM-by-VM Audit Status

| VM | Alloy | Beszel | Portainer | Auth Issues | Backup Status |
|----|-------|--------|-----------|-------------|---------------|
| db (111) | ✅ | ✅ | ✅ | ✅ Internal only | ❌ **NO BACKUPS** |
| edge (110) | ✅ | ✅ | ✅ | ⚠️ Traefik exposed | ✅ Config in git |
| observability (112) | ✅ | ✅ | ✅ | ❌ No auth on metrics | ✅ Config in git |
| media (113) | ✅ | ✅ | ✅ | N/A (no services yet) | N/A |
| dev (114) | ❌ | ❌ | ❌ | ⚠️ Gitea own auth | ❌ **NO BACKUPS** |
| deploy (115) | ❌ | ❌ | ❌ | ⚠️ Dokploy own auth | ❌ **NO BACKUPS** |
| ha (116) | ❌ | ❌ | N/A | ✅ HA own auth | ⚠️ Via HA backups |
| Synology | ❓ | ❓ | N/A | ❓ | ❓ **AUDIT NEEDED** |

**Legend:** ✅ Configured | ❌ Missing | ⚠️ Partial/Issues | ❓ Unknown | N/A Not applicable

---

## Quick Reference Notes

### 🔴 CRITICAL: Traefik Security - Always Choose Private or Public

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

**Current Public Services:** ha, dmo, king, wsking (old services only)

---

### 🔴 CRITICAL: Always Use Existing Infrastructure Services

**NEVER deploy separate databases or services when we already have them!**

**Use these existing services from db host (10.10.10.111):**
- **PostgreSQL** - For any app needing SQL database
- **MongoDB** - For any app needing NoSQL/document database
- **Redis** - For caching, sessions, queues
- **MinIO** - For object storage (S3-compatible)
- **Mosquitto MQTT** - For message broker / IoT communication

**How to connect:**
```yaml
# PostgreSQL
DATABASE_URL: postgresql://username:password@10.10.10.111:5432/dbname

# MongoDB
MONGO_URL: mongodb://username:password@10.10.10.111:27017/dbname

# Redis
REDIS_URL: redis://:password@10.10.10.111:6379/0

# MinIO (S3)
S3_ENDPOINT: http://10.10.10.111:9000
AWS_ACCESS_KEY_ID: (from 1Password)
AWS_SECRET_ACCESS_KEY: (from 1Password)

# MQTT (Mosquitto)
MQTT_BROKER: 10.10.10.111
MQTT_PORT: 1883
MQTT_WS_PORT: 9003  # WebSockets (optional)
# Anonymous connections enabled by default
# To add auth: docker exec mosquitto mosquitto_passwd -c /mosquitto/config/passwd username
```

**For new apps:**
1. Check if app needs database → use PostgreSQL or MongoDB
2. Check if app needs caching → use Redis
3. Check if app needs file storage → use MinIO
4. Create database/user on db host if needed
5. Add credentials to 1Password
6. Configure app to use existing service

**Benefits:**
- ✅ Centralized backup and maintenance
- ✅ Lower resource usage
- ✅ Consistent connection patterns
- ✅ Single source of truth for data

---

### GitHub → Gitea CI/CD Workflow

**Strategy:** Use GitHub as primary (industry standard), auto-mirror to Gitea for self-hosted CI/CD.

**Workflow:**
```
You → Push to GitHub → GitHub mirrors to Gitea → Gitea Actions (act_runner) → Build/Test/Deploy
```

**Setup:**
1. Create repo in Gitea (or use pull mirror)
2. Add GitHub Action to mirror pushes to Gitea (see `dev/GITHUB-GITEA-WORKFLOW.md`)
3. Create `.gitea/workflows/*.yml` files (same syntax as GitHub Actions)
4. Push to GitHub → CI/CD runs automatically on your homelab runner

**Gitea Container Registry:**
```bash
# Login
docker login git.onurx.com -u <username> -p <token>

# Push image
docker tag myapp:latest git.onurx.com/username/myapp:latest
docker push git.onurx.com/username/myapp:latest

# Use in Dokploy or compose files
image: git.onurx.com/username/myapp:latest
```

**Benefits:**
- ✅ Keep using GitHub (industry standard, familiar)
- ✅ One runner for ALL repos (no organization needed)
- ✅ No runner minute limits
- ✅ Access to homelab services in CI/CD
- ✅ Self-hosted container registry included
- ✅ Real-time sync from GitHub

**Full guide:** `dev/GITHUB-GITEA-WORKFLOW.md`

---

### Traefik (Reverse Proxy)

**Config Structure:**
```
edge/traefik/config/dynamic/
├── middlewares.yml  - Auth, headers, rate limiting, compression, IP whitelist
├── services.yml     - Backend targets (IP:port)
└── routers.yml      - Domain routing rules
```

**🔒 SECURITY MODEL: Explicit Private/Public**

**CRITICAL:** Every service MUST explicitly choose `private-default` or `public-access` middleware!

**Private Services** (internal only - home network + NetBird VPN):
```yaml
myapp:
  rule: "Host(`myapp.onurx.com`)"
  entryPoints: [websecure]
  service: myapp
  middlewares:
    - private-default  # ← REQUIRED for internal services
  tls:
    certResolver: cloudflare
```

**Public Services** (accessible from internet):
```yaml
myapp:
  rule: "Host(`myapp.onurx.com`)"
  entryPoints: [websecure]
  service: myapp
  middlewares:
    - public-access  # ← ONLY for public services
  tls:
    certResolver: cloudflare
```

**Middleware Details:**
- **`private-default`**: IP whitelist (10.10.10.0/24 + 100.92.0.0/16) + security headers
- **`public-access`**: Only security headers (no IP restriction)

**⚠️ WARNING:** Forgetting middleware = NO IP PROTECTION! Always add one of these two.

**To add a new service:**
1. Add service in `services.yml`:
   ```yaml
   myapp:
     loadBalancer:
       servers:
         - url: "http://10.10.10.x:port"
   ```

2. Add router in `routers.yml`:
   ```yaml
   myapp:
     rule: "Host(`myapp.onurx.com`)"
     entryPoints: [websecure]
     service: myapp
     middlewares:
       - private-default  # ← Choose private-default OR public-access
     tls:
       certResolver: cloudflare
   ```

3. (Optional) Add custom middleware in `middlewares.yml` if needed

**Auto-reload:** Traefik reloads dynamic configs automatically (no restart)

**Dashboard:** `http://10.10.10.110:8080` or `https://traefik.onurx.com` (private)

**SSL Certs:** Cloudflare DNS-01 challenge, stored in `/data/acme.json`

**Current Public Services:**
- ha.onurx.com (Home Assistant - old)
- dmo.onurx.com (DMO app - old)
- king.onurx.com (King game - old)
- wsking.onurx.com (King WebSocket - old)

**All other services are private** (blocked from internet, accessible via home network or NetBird VPN only)

---

### Creating a New VM

**Complete checklist for adding a new VM to the infrastructure:**

#### On Proxmox Host:

1. **Clone template VM:**
   ```bash
   # Find your template VM ID
   qm list | grep template

   # Clone (replace <template-id> and <new-vm-id>)
   qm clone <template-id> <new-vm-id> --name <vm-name> --full
   ```

2. **Configure VM:**
   ```bash
   # Set static IP
   qm set <new-vm-id> --ipconfig0 ip=10.10.10.<ip>/24,gw=10.10.10.1

   # Start VM
   qm start <new-vm-id>
   ```

3. **Wait ~30 seconds for boot, then SSH:**
   ```bash
   ssh fx@10.10.10.<ip>
   ```

#### On New VM (after SSH):

4. **Set hostname:**
   ```bash
   sudo hostnamectl set-hostname <vm-name>
   hostnamectl  # Verify
   ```

5. **Set 1Password service account token:**
   ```bash
   echo 'export OP_SERVICE_ACCOUNT_TOKEN="<your-token>"' >> ~/.bashrc
   source ~/.bashrc

   # Test 1Password connection
   op vault list
   ```

6. **Clone homelab repository:**
   ```bash
   cd /opt
   sudo git clone https://git.onurx.com/fx/homelab.git
   sudo chown -R fx:fx homelab/
   cd homelab
   git branch --set-upstream-to=origin/main main
   ls -la  # Should show files from git repository
   ```

7. **Create subdirectory for VM (if needed):**
   ```bash
   # Only if this VM needs new directory in the repo
   mkdir -p <vm-name>
   cd <vm-name>
   # Create docker-compose.yml and .env files
   ```

#### Post-Setup Tasks:

8. **Update network documentation** - Add VM to Network Layout table in this file

9. **Add Traefik routes** (if services need external access):
    - Add service to `edge/traefik/config/dynamic/services.yml`
    - Add router to `edge/traefik/config/dynamic/routers.yml`
    - Traefik auto-reloads (no restart needed)

10. **Deploy services:**
    ```bash
    # On the new VM
    cd /opt/homelab/<vm-name>

    # Create docker-compose.yml and .env files
    # Deploy services
    op run --env-file=.env -- docker compose up -d
    ```

11. **Update this file** - Document deployed services and their configuration

**Troubleshooting:**

- **Git clone failed?** Check DNS resolves `git.onurx.com`: `ping git.onurx.com`
- **Permission denied on git clone?** Repository must be public in Gitea
- **1Password not working?** Check token is set: `echo $OP_SERVICE_ACCOUNT_TOKEN`
- **Services can't connect to db host?** Check network connectivity: `nc -zv 10.10.10.111 5432`

---

### Centralized Logging (Loki + Alloy)

**Status:** ✅ Deployed | **Access:** Grafana Explore `http://10.10.10.112:3000/explore`

**Flow:** Docker containers → Alloy (each VM) → Loki (10.10.10.112:3100) → Grafana

**Config:**
- Retention: 90 days | Storage: `/opt/homelab/loki/data/`
- Labels: host, container, image, compose_service, level (auto-extracted)
- Alloy: Full config on observability VM, logs-only on db/edge/media VMs

**Common Queries:**
```logql
{cluster="homelab"}                          # All logs
{host="db-vm"}                               # Specific VM
{container="mongodb"}                        # Specific container
{level="error"}                              # Errors only
{cluster="homelab"} |~ "(?i)error|fail"     # Search pattern
{host="edge-vm", container="traefik"}       # Live stream (click "Live" button)
```

---

### Beszel (Quick Monitoring Dashboard)

**Status:** ✅ Deployed | **Access:** `http://10.10.10.112:8090`

**Purpose:** Lightweight monitoring for quick health checks (CPU, RAM, disk, network, Docker stats)

**Agents:** Hub on observability VM + Agents on db/edge/media VMs (Unix socket/port 45876)

**Deployment:**
- Secrets: `op://Server/beszel/key` and `op://Server/beszel/token`
- Deploy: `op run --env-file=.env -- docker compose up -d beszel-agent`
- Universal token auto-registers agents (regenerates hourly or on Hub restart)

**Use Case:** Beszel for "Is everything okay?" | Grafana for "Why did this happen?"

---

### AdGuard Home (DNS)

**Status:** ✅ Deployed | **Access:** `http://10.10.10.110:8888`

**Config:** Wildcard `*.onurx.com` → `10.10.10.110` | Upstream: Cloudflare/AdGuard/Google (TLS) | DNSSEC enabled

**Testing:**
```bash
nslookup auth.onurx.com 10.10.10.110  # Should return 10.10.10.110
curl -I https://auth.onurx.com        # Should return HTTP/2 200
```

---

### Authentik (SSO)

**Status:** ✅ Deployed | **Access:** `https://auth.onurx.com` | **Dependencies:** PostgreSQL + Redis (10.10.10.111)

**Setup:**
1. 1Password secrets: `authentik-db/password`, `authentik/secret_key` (generate: `openssl rand -base64 50`)
2. Create PostgreSQL database on db host:
   ```sql
   CREATE USER authentik WITH PASSWORD 'xxx';
   CREATE DATABASE authentik OWNER authentik;
   GRANT ALL PRIVILEGES ON DATABASE authentik TO authentik;
   ```
3. Deploy: `op run --env-file=.env -- docker compose up -d authentik-server authentik-worker`

**Configuration Required:**
- ❌ No applications configured yet (forward auth middleware exists in Traefik but SSO not working)
- Need to create apps in Authentik UI for: grafana, prometheus, loki, alloy, gitea, dokploy, media services

**Troubleshooting:**
```bash
# Test DB connection
psql -h 10.10.10.111 -U authentik -d authentik

# Test Redis
docker run --rm redis:alpine redis-cli -h 10.10.10.111 -a $(op read "op://Server/redis/password") ping
```

---

### Docker Networking

**Traefik Routing:**
- Same VM containers: Use container name (e.g., `http://authentik-server:9000`)
- Different VM: Use VM IP:port (e.g., `http://10.10.10.112:3000`)

**Flow:** User → DNS (*.onurx.com = 10.10.10.110) → Traefik → Backend (container name or VM IP)

---

### Observability Stack

**Status:** ✅ Deployed (10.10.10.112) | **Retention:** 90 days (Prometheus + Loki)

**Components:**
- Prometheus v3.1.0 - `https://prometheus.onurx.com` ⚠️ No auth
- Grafana 11.4.0 - `https://grafana.onurx.com` ✅ Own login
- Loki 3.3.2 - `https://loki.onurx.com` (API only, no UI) ⚠️ No auth
- Alloy v1.11.2 - `https://alloy.onurx.com` (observability VM only) ⚠️ No auth

**Alloy:**
- Each VM has independent Alloy instance (no unified UI)
- Collects: System metrics, Docker metrics, Docker logs
- Sends to: Prometheus (metrics) + Loki (logs)
- Other UIs: `http://10.10.10.110:12345` (edge), `http://10.10.10.113:12345` (media)

**Grafana Explore Queries:**
```promql
# Prometheus
up                                          # All targets
node_cpu_seconds_total                      # CPU metrics
container_memory_usage_bytes                # Docker memory

# Loki (access via Grafana Explore only)
{container="grafana"}                       # Grafana logs
{container="traefik"} |= "error"           # Traefik errors
{compose_project="observability"}           # All stack logs
```

**Deploy:** `op run --env-file=.env -- docker compose up -d prometheus grafana loki alloy`

---

### NetBird VPN (Remote Access)

**Status:** ✅ Deployed (NetBird Cloud) | **Location:** Edge VM (10.10.10.110) | **Dashboard:** https://app.netbird.io

**Config:**
- Setup key: `op://Server/netbird/token` | Network mode: host | Route: `10.10.10.0/24` → netbird-edge
- DNS: *.onurx.com resolved via AdGuard (10.10.10.110)

**Deploy:** `op run --env-file=.env -- docker compose up -d netbird`

**Troubleshooting:**
```bash
docker exec netbird netbird status        # Check status
docker exec netbird netbird routes list   # View routes
```

---

### Database Connections

All services connect to db host (10.10.10.111):

```yaml
# PostgreSQL
DATABASE_URL: postgresql://user:pass@10.10.10.111:5432/dbname

# MongoDB
MONGO_URL: mongodb://user:pass@10.10.10.111:27017/dbname

# Redis
REDIS_URL: redis://10.10.10.111:6379/0

# MinIO (S3)
S3_ENDPOINT: http://10.10.10.111:9000
```

---

### Git Workflow ✅ NEW (VirtioFS Removed)

**Migration Complete:** All VMs now use standard git workflow (VirtioFS removed on 2025-10-27)

**Architecture:**
- Each VM has full git repository at `/opt/homelab/`
- Central Gitea repository: `https://git.onurx.com/fx/homelab`
- Repository is **public** (read-only access, no authentication needed for git pull)
- DNS resolves `git.onurx.com` via AdGuard wildcard (`*.onurx.com` → `10.10.10.110`)

**To update configs from your Mac:**
1. Edit files locally: `cd ~/Repositories/infrastructure-1`
2. Commit and push: `git add . && git commit -m "message" && git push`
3. Pull changes on VMs: `ssh fx@10.10.10.xxx 'cd /opt/homelab && git pull'`
4. Restart affected services: `op run --env-file=.env -- docker compose up -d <service>`

**Git configuration on VMs:**
```bash
# Remote URL (all VMs)
origin: https://git.onurx.com/fx/homelab.git

# Branch tracking
main → origin/main

# No authentication needed (public repository)
git pull  # Just works
```

**Benefits of Git vs VirtioFS:**
- ✅ Proper file change notifications (file watching works)
- ✅ Standard git workflow (commit history, diffs, rollbacks)
- ✅ No permission issues between host/guest
- ✅ VMs are truly independent (can work offline)
- ✅ Better for Traefik config reloading

---

## Common Commands

### Deploy Service
```bash
# SSH to VM
ssh root@10.10.10.xxx

# Navigate to working dir
cd /opt/homelab

# Deploy single service
op run --env-file=.env -- docker compose up -d <service-name>

# Deploy all services
op run --env-file=.env -- docker compose up -d

# Check logs
docker compose logs -f <service-name>
```

### Check Status
```bash
# Container status
docker compose ps

# View logs
docker compose logs -f <service-name>

# Traefik dashboard
http://10.10.10.110:8080

# Portainer
https://10.10.10.112:9443
```

### Update Service
```bash
# Pull latest image
docker compose pull <service-name>

# Recreate container
op run --env-file=.env -- docker compose up -d <service-name>
```

### Remove and Reinstall Service
```bash
# Stop and remove
docker compose down <service-name> -v

# Remove bind mount data
rm -rf <service-name>/data/*

# Redeploy
docker compose pull <service-name>
op run --env-file=.env -- docker compose up -d <service-name>
```

### Test Database Connections
```bash
# MongoDB (from db host)
docker exec mongodb mongosh --eval "db.adminCommand('ping')"

# PostgreSQL (from db host)
docker exec postgres pg_isready -U postgres

# Test from another VM
mongosh --host 10.10.10.111:27017 -u <user> -p <pass>
psql -h 10.10.10.111 -U <user> -d <database>
```

### Create New VM
```bash
# On Proxmox host
qm clone <template-id> <new-id> --name <vm-name> --full
qm set <new-id> --memory 4096 --cores 2 --ipconfig0 ip=10.10.10.xxx/24,gw=10.10.10.1
qm start <new-id>

# Inside VM
sudo hostnamectl set-hostname <vm-name>
echo 'export OP_SERVICE_ACCOUNT_TOKEN="ops_xxx"' >> ~/.bashrc
source ~/.bashrc

# Clone repository
cd /opt
sudo git clone https://git.onurx.com/fx/homelab.git
sudo chown -R fx:fx homelab/
cd homelab
git branch --set-upstream-to=origin/main main
```

---

## VM Template Setup

### Create Template (One-Time)

**Install base packages:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y curl wget vim htop net-tools git ca-certificates gnupg

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker homelab
sudo systemctl enable docker

# Configure Git (this is saved in template)
git config --global user.name "XVll"
git config --global user.email "onur03@gmail.com"

# Install 1Password CLI
curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
  sudo gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | \
  sudo tee /etc/apt/sources.list.d/1password.list
sudo apt update && sudo apt install -y 1password-cli

# Install QEMU guest agent
sudo apt install -y qemu-guest-agent
sudo systemctl enable qemu-guest-agent
```

**Clean before templating:**
```bash
# Remove SSH keys (regenerated on boot)
sudo rm -f /etc/ssh/ssh_host_*

# Clear history and machine-id
cat /dev/null > ~/.bash_history
history -c
sudo truncate -s 0 /etc/machine-id

# Shutdown
sudo shutdown -h now
```

**Convert to template in Proxmox UI:** Right-click VM → Convert to Template

**Important:**
- Git is pre-configured in template (name/email)
- DO NOT set `OP_SERVICE_ACCOUNT_TOKEN` in template (set per VM)
- Use Full Clone when creating VMs (not Linked Clone)

---

## 1Password Setup

### Create Items in "Server" Vault

**Required items:**
- `mongodb` - fields: username, password
- `postgres` - fields: username, password
- `redis` - field: password
- `minio` - fields: username, password
- `grafana` - fields: username, password
- `cloudflare` - fields: email, api_token
- `authentik-db` - field: password (PostgreSQL user password)
- `authentik` - field: secret_key (generate with: `openssl rand -base64 50`)

**Verify setup:**
```bash
op read "op://Server/mongodb/username"
op read "op://Server/postgres/password"
```

**How it works:**
1. `.env` files contain: `MONGODB_ROOT_USER=op://Server/mongodb/username`
2. Run: `op run --env-file=.env -- docker compose up -d`
3. `op run` fetches actual values from 1Password and injects them

**Troubleshooting:**
- "item not found" → Check vault name is "Server", item/field names match exactly
- "not signed in" → Set `OP_SERVICE_ACCOUNT_TOKEN` in `~/.bashrc`

---

## Service-Specific Notes

### Gitea - Git Hosting & CI/CD

**VM:** dev (10.10.10.114) | **Status:** ✅ Deployed | **Access:** https://git.onurx.com (SSH: port 222)

**Components:**
- Gitea v1.24.7 - Git + Container Registry + Package Registry + Actions (admin: `fxx`)
- act_runner v0.2.13 - CI/CD executor (labels: ubuntu-latest, ubuntu-22.04)
- PostgreSQL on db host (10.10.10.111) - Database: `gitea`, User: `gitea`

**Features:** Git hosting, Gitea Actions (CI/CD), OCI container registry, Package registry (npm/PyPI), Repository mirroring, Git LFS

**1Password:** `gitea-db/password`, `gitea/secret_key`, `gitea/internal_token`, `gitea/runner_token`

**Usage:**
```bash
git clone https://git.onurx.com/fxx/repo.git                # HTTPS
git clone ssh://git@git.onurx.com:222/fxx/repo.git          # SSH
docker login git.onurx.com && docker push git.onurx.com/fxx/image:tag  # Container registry
```

**Note:** Infrastructure repo is PUBLIC (allows VMs to git pull without auth)

---

### Dokploy - Application Deployment Platform

**VM:** deploy (10.10.10.115) | **Status:** ✅ Deployed | **Access:** https://deploy.onurx.com

**Components:** Dokploy (latest), PostgreSQL 16 (bundled), Redis 7 (bundled), Traefik v3.5 (bundled, internal)

**Architecture:** Docker Swarm mode | Self-contained PaaS | Main Traefik on edge VM proxies to Dokploy

**Purpose:** Deploy personal apps and side projects via UI (Git → Docker → Deploy)

**1Password:** `dokploy` (admin credentials)

**Install:** `curl -sSL https://dokploy.com/install.sh | sudo sh`

---

### Home Assistant - Home Automation Platform

**VM:** ha (10.10.10.116) | **Status:** ✅ Deployed | **Access:** https://ha.onurx.com

**Deployment:** Home Assistant OS (Proxmox helper script) | Standalone VM with dedicated OS (not Docker)

**Database:** PostgreSQL recorder on db host (10.10.10.111) | Database: `homeassistant` | Retention: 30 days

**Config:**
```yaml
recorder:
  db_url: postgresql://homeassistant:PASSWORD@10.10.10.111:5432/homeassistant
  purge_keep_days: 30
```

**1Password:** `homeassistant-db/password`

**Backups:** Settings → System → Backups (download `.tar` files)

**Note:** Not managed via Docker Compose | Configuration via File Editor add-on | Use partial backups for migrations

---

## Network Layout

| VM | IP | Services |
|----|-----|----------|
| db | 10.10.10.111 | MongoDB, PostgreSQL, Redis, MinIO |
| observability | 10.10.10.112 | Portainer, Prometheus, Grafana, Loki, Alloy |
| edge | 10.10.10.110 | Traefik, AdGuard, Authentik, NetBird |
| media | 10.10.10.113 | Jellyfin, Arr Stack, n8n, Paperless, qBittorrent |
| dev | 10.10.10.114 | Gitea (Git + CI/CD) |
| deploy | 10.10.10.115 | Dokploy (Application Deployment Platform) |
| ha | 10.10.10.116 | Home Assistant (Home Automation) |

**Network:** VLAN 10 (10.10.10.0/24)
**Gateway:** 10.10.10.1
**DNS (after AdGuard):** 10.10.10.110

---

## Important Notes

### Secrets Management
- All passwords in 1Password (vault: "Server")
- `.env` files contain only `op://` references (safe to commit)
- Never commit actual passwords
- Use `op run --env-file=.env -- <command>` to inject secrets

### Service Dependencies
Deploy in order:
1. Databases (MongoDB, PostgreSQL, Redis, MinIO)
2. Portainer (for management)
3. Traefik → AdGuard → Authentik
4. Observability stack
5. Applications

### Traefik SSL
- Domain: `*.onurx.com`
- Provider: Cloudflare DNS-01 challenge
- Email: onur03@gmail.com
- Certs stored: `edge/traefik/data/acme.json`
- Auto-renewal via Let's Encrypt

### File Naming Convention
- `@file` - Defined in YAML files (what we use)
- `@docker` - Defined via Docker labels
- `@internal` - Traefik built-ins

---

## Next Steps

### Current Status
- ✅ **Phase 1 COMPLETE**: Databases (MongoDB, PostgreSQL, Redis, MinIO) + Portainer
- ✅ **Phase 2 COMPLETE**: Traefik + AdGuard + Authentik + NetBird
  - Traefik reverse proxy with SSL (Cloudflare DNS-01)
  - AdGuard Home DNS server deployed
  - Authentik SSO with embedded outpost configured
  - Forward auth middleware ready (uses `authentik` middleware in routers.yml)
  - Admin user: `akadmin` (login: http://10.10.10.110:9000)
  - NetBird VPN client deployed (remote access working, DNS resolving *.onurx.com)
- ✅ **Phase 3 COMPLETE**: Observability Stack (Prometheus, Grafana, Loki, Alloy)
  - Prometheus v3.1.0: Metrics storage with 90-day retention (https://prometheus.onurx.com)
  - Grafana 11.4.0: Dashboards and visualization (https://grafana.onurx.com)
  - Loki 3.3.2: Log aggregation with 90-day retention (API only, no web UI)
  - Alloy v1.11.2: Unified collector for system metrics, Docker metrics, and logs (https://alloy.onurx.com)
  - All datasources provisioned and working in Grafana Explore
  - All services accessible via Traefik with valid Let's Encrypt SSL certificates
  - Authentik SSO middleware temporarily removed (will be re-enabled after configuring applications)
- ⏳ **Phase 4 IN PROGRESS**: Applications (Jellyfin, Arr Stack, n8n, Paperless) + Development Stack (Gitea, Dokploy)

### Immediate Next Tasks

**1. Deploy Media Services** (media VM - 10.10.10.113)
   - Jellyfin (media server)
   - Prowlarr → Sonarr/Radarr (media management)
   - qBittorrent (download client)
   - n8n (workflow automation)
   - Paperless (document management)

**2. Deploy Development Stack** (dev VM - 10.10.10.114)
- Gitea (Git + Container Registry + CI/CD)
- Dokploy (Deployment platform)
   - Self-hosted PaaS platform

**3. Configure Authentik Applications**
   - Create applications in Authentik for: Grafana, Prometheus, Loki, Alloy
   - Create applications for media services: Jellyfin, Sonarr, Radarr, Prowlarr, qBittorrent, n8n, Paperless
   - Re-enable `authentik` middleware in `routers.yml` for protected services
   - Test forward authentication works correctly

**4. Cutover from Old Infrastructure**
   - Update DNS to point to new infrastructure
   - Test all services end-to-end
   - Verify Authentik forward auth works
   - Decommission old infrastructure

### Important Notes
- **Authentik Forward Auth**: Uses embedded outpost (no separate container needed)
- **Forward Auth Endpoint**: `http://authentik-server:9000/outpost.goauthentik.io/auth/traefik`
- **Protected Services**: Add `authentik` middleware to router in `routers.yml`
- **DNS rewrites**: Managed via AdGuard UI at http://10.10.10.110:8888
- **Testing**: Will test when switching from old to new infrastructure

---

**Last Updated:** 2025-10-28 - Infrastructure audit complete, documentation refined and compacted
