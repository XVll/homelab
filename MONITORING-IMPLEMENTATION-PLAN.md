# Homelab Monitoring Implementation Plan
## Pure Alloy Architecture - Centralized Telemetry Collection

**Created:** 2025-11-04
**Status:** Ready for Implementation
**Goal:** Centralize all metrics/logs collection through Grafana Alloy, making Prometheus a pure remote_write receiver

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Key Design Decisions](#key-design-decisions)
3. [Current State vs Target State](#current-state-vs-target-state)
4. [Implementation Phases](#implementation-phases)
5. [Phase Details](#phase-details)
6. [Verification Checklist](#verification-checklist)
7. [Rollback Strategy](#rollback-strategy)
8. [Reference Information](#reference-information)

---

## Architecture Overview

### The Problem We're Solving

1. **Metric Overlap:** Same VM monitored by multiple sources (Proxmox + Alloy)
2. **Inconsistent Collection:** Some VMs use Alloy, others use specialized exporters
3. **Configuration Sprawl:** Scrape configs in both Prometheus and separate exporter containers
4. **Dashboard Confusion:** Unclear which metric source to use for which dashboard

### The Solution: Pure Alloy Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    ALL METRICS FLOW THROUGH ALLOY                │
└─────────────────────────────────────────────────────────────────┘

Synology (SNMP) ──────┐
                      │
Proxmox (API) ────────┤
                      │
Home Assistant (API) ─┤──> Alloy (observability VM) ──┐
                      │                                 │
Apps (/metrics) ──────┤                                 │
                      │                                 │
VMs (host/container) ─┘                                 │
                                                        │
Edge VM ──> Alloy (edge) ──────────────────────────────┤
DB VM ──> Alloy (db) ───────────────────────────────────┤
Media VM ──> Alloy (media) ─────────────────────────────┤
                                                        │
                                                        ▼
                                                  Prometheus
                                              (pure remote_write)
                                                        │
                                                        ▼
                                                    Grafana
```

---

## Key Design Decisions

### ✅ Decision 1: Use Grafana Alloy as Universal Collector

**What Alloy Replaces:**
- ❌ Node Exporter → `prometheus.exporter.unix`
- ❌ cAdvisor → `prometheus.exporter.cadvisor`
- ❌ Promtail → `loki.source.docker`
- ❌ SNMP Exporter → `prometheus.exporter.snmp`
- ❌ Direct Prometheus scrapes → `prometheus.scrape` + `remote_write`

**What Alloy CANNOT Replace (but can scrape):**
- Proxmox Exporter (keep container, but Alloy scrapes it)
- Application-specific exporters (future: postgres_exporter, adguard_exporter)

### ✅ Decision 2: Distributed Alloy Deployment

**Alloy on observability VM (10.10.10.112):**
- Infrastructure-wide collection:
  - SNMP (Synology)
  - Proxmox exporter scrape
  - Home Assistant API scrape
  - App /metrics scrapes (Traefik, Grafana, etc.)
- Local collection:
  - observability VM host metrics
  - observability VM container metrics
  - observability VM logs

**Alloy on each Debian VM (edge, db, media, dev, deploy):**
- Local collection only:
  - VM host metrics
  - VM container metrics
  - VM logs
- Remote write to Prometheus (10.10.10.112:9090)

### ✅ Decision 3: Prometheus as Pure TSDB

**Prometheus will:**
- ✅ Accept remote_write from all Alloy instances
- ✅ Store metrics in TSDB
- ✅ Serve queries to Grafana
- ❌ NOT scrape any targets (except maybe localhost self-monitoring)

**Benefits:**
- Simplified prometheus.yml (no complex scrape_configs)
- All collection logic in Alloy (single source of truth)
- Consistent labeling via Alloy external_labels
- Easier debugging (check Alloy UI, not Prometheus targets)

### ✅ Decision 4: Dashboard Metric Source Strategy

| Dashboard Type | Primary Metric Source | Rationale |
|----------------|----------------------|-----------|
| **Systems Overview** | Proxmox (`pve_*`) | Unified view of ALL VMs from hypervisor |
| **VM Detail (Debian)** | Alloy (`node_*`, `container_*`) | Accurate internal metrics |
| **VM Detail (Synology)** | SNMP (`snmp_*`) via Alloy | Can't install agent |
| **VM Detail (Home Assistant)** | HA API (`homeassistant_*`) via Alloy | HA OS limitation |
| **Application Dashboards** | App-specific metrics via Alloy | Deep app insights |

**No metric overlap in dashboards** - each uses single authoritative source.

### ✅ Decision 5: Consistent Labeling Strategy

All metrics collected by Alloy get these external_labels:

```alloy
external_labels = {
  cluster = "homelab"
  host = "vm-name"           // e.g., "edge", "db"
  host_ip = "10.10.10.xxx"   // e.g., "10.10.10.110"
  collector = "alloy"
  source = "alloy"           // vs "proxmox" for pve_* metrics
}
```

This allows clear differentiation between:
- Proxmox metrics (hypervisor perspective) - `source="proxmox"`
- Alloy metrics (guest perspective) - `source="alloy"`

---

## Current State vs Target State

### Current State (Before Implementation)

**Observability VM:**
- ✅ Alloy collecting local host/container metrics
- ✅ SNMP Exporter (separate container) → Prometheus scrapes
- ✅ Proxmox Exporter (separate container) → Prometheus scrapes
- ✅ Prometheus scrapes HA directly with auth token
- ✅ Prometheus scrapes app /metrics directly

**Other VMs:**
- ❌ No Alloy deployed yet
- ❌ Only monitored via Proxmox exporter

**Prometheus:**
- Has many scrape_configs for different targets
- Accepts remote_write from observability Alloy only

### Target State (After Implementation)

**Observability VM:**
- ✅ Alloy collects everything:
  - Local host/container metrics
  - SNMP from Synology (native `prometheus.exporter.snmp`)
  - Proxmox metrics (scrapes proxmox-exporter container)
  - Home Assistant metrics (scrapes HA API with auth)
  - App metrics (scrapes Traefik, Grafana, Loki, etc.)
- ✅ All forwarded via remote_write to Prometheus
- ❌ SNMP Exporter container removed (redundant)
- ✅ Proxmox Exporter container kept (but Alloy scrapes it)

**Edge, DB, Media, Dev VMs:**
- ✅ Alloy deployed on each
- ✅ Collecting local host/container metrics
- ✅ Remote write to Prometheus

**Prometheus:**
- ✅ Accepts ONLY remote_write
- ✅ No scrape_configs (or just localhost)
- ✅ Pure TSDB role

**Grafana Dashboards:**
- ✅ Systems Overview uses Proxmox metrics only
- ✅ VM Detail dashboards use Alloy metrics (where available)
- ✅ Clear metric source hierarchy
- ✅ No overlapping/conflicting data

---

## Implementation Phases

| Phase | Description | Time Est. | Dependencies |
|-------|-------------|-----------|--------------|
| **1** | Add SNMP collection to observability Alloy | 30 min | None |
| **2** | Add Proxmox scrape to observability Alloy | 15 min | Phase 1 |
| **3** | Add Home Assistant scrape to observability Alloy | 15 min | Phase 1 |
| **4** | Add app metrics scraping to observability Alloy | 20 min | Phase 1 |
| **5** | Clean up Prometheus scrape_configs | 10 min | Phases 1-4 complete |
| **6** | Deploy Alloy to edge VM | 30 min | Phase 5 |
| **7** | Deploy Alloy to db VM | 30 min | Phase 5 (can parallel with 6) |
| **8** | Rebuild Grafana dashboards | 1-2 hrs | Phases 6-7 |
| **9** | Remove snmp-exporter container | 5 min | Phase 1 verified |
| **10** | Update documentation | 30 min | Anytime |

**Total Time:** 4-5 hours (can be spread across multiple sessions)

---

## Phase Details

### Phase 1: Add SNMP Collection to Observability Alloy

**Goal:** Replace separate snmp-exporter container with Alloy's native SNMP support

**Tasks:**

1. **Prepare SNMP configuration:**
   ```bash
   # Move SNMP config to Alloy directory
   mkdir -p observability/alloy/config/
   cp observability/snmp-exporter/snmp.yml observability/alloy/config/snmp.yml
   ```

2. **Update Alloy config** (`observability/alloy/config/config.alloy`):
   ```alloy
   // ============================================================================
   // SNMP: Synology NAS Monitoring
   // ============================================================================

   prometheus.exporter.snmp "synology" {
     config_file = "/etc/alloy/snmp.yml"

     target "synology" {
       address = "10.10.10.100"
       module  = "synology"       // or "if_mib" - check your snmp.yml
       auth    = "homelab_v2"     // SNMP community/auth name from snmp.yml
     }
   }

   prometheus.scrape "snmp_synology" {
     targets    = prometheus.exporter.snmp.synology.targets
     forward_to = [prometheus.remote_write.prometheus.receiver]
     scrape_interval = "60s"
   }
   ```

3. **Update docker-compose.yml** to mount snmp.yml:
   ```yaml
   alloy:
     volumes:
       - ./alloy/config/config.alloy:/etc/alloy/config.alloy:ro
       - ./alloy/config/snmp.yml:/etc/alloy/snmp.yml:ro  # ADD THIS
       # ... other volumes
   ```

4. **Deploy changes:**
   ```bash
   cd /opt/homelab/observability

   # Commit config changes locally first
   git pull  # Get latest
   # Edit files
   git add alloy/config/
   git commit -m "Add SNMP collection to Alloy"
   git push

   # Pull on observability VM
   ssh fx@10.10.10.112 'cd /opt/homelab && git pull'

   # Restart Alloy
   ssh fx@10.10.10.112 'cd /opt/homelab/observability && op run --env-file=.env -- docker compose restart alloy'
   ```

**Verification:**

1. Check Alloy UI: http://10.10.10.112:12345
   - Navigate to "Component detail" → find `prometheus.exporter.snmp.synology`
   - Should show target status UP
   - Click through to see metrics being collected

2. Check Alloy logs:
   ```bash
   ssh fx@10.10.10.112 'docker logs alloy --tail 100'
   # Look for SNMP-related logs, no errors
   ```

3. Check Prometheus:
   ```promql
   # Query SNMP metrics
   snmp_up{job="snmp_synology"}

   # Check for synology-specific metrics
   {job="snmp_synology"}

   # Compare with old snmp-exporter metrics
   {job="synology"}  # Old way (if still running)
   ```

4. Check Grafana Synology dashboard:
   - Verify data still displays
   - Metrics should have `source="alloy"` label

**Success Criteria:**
- ✅ Alloy shows SNMP target UP
- ✅ SNMP metrics appear in Prometheus
- ✅ Synology dashboard shows data
- ✅ No errors in Alloy logs

**If Failed:**
- Check SNMP config file path in Alloy
- Verify Synology SNMP is enabled (port 161 UDP)
- Check SNMP community string / auth matches
- Test SNMP manually: `snmpwalk -v2c -c public 10.10.10.100`

**DO NOT PROCEED TO PHASE 2 UNTIL PHASE 1 IS VERIFIED ✅**

---

### Phase 2: Add Proxmox Scrape to Observability Alloy

**Goal:** Route Proxmox metrics through Alloy instead of direct Prometheus scrape

**Tasks:**

1. **Update Alloy config** (`observability/alloy/config/config.alloy`):
   ```alloy
   // ============================================================================
   // PROXMOX: VM Metrics from Hypervisor
   // ============================================================================

   prometheus.scrape "proxmox" {
     targets = [{
       __address__ = "proxmox-exporter:9221",
       job         = "proxmox",
     }]

     metrics_path = "/pve"
     params = {
       module = ["default"],
     }

     scrape_interval = "60s"
     forward_to = [prometheus.remote_write.prometheus.receiver]

     // Add labels to differentiate from Alloy VM metrics
     relabel_configs {
       source_labels = ["__address__"]
       target_label  = "source"
       replacement   = "proxmox"
     }
   }
   ```

2. **Deploy changes:**
   ```bash
   cd /opt/homelab/observability
   git add alloy/config/config.alloy
   git commit -m "Add Proxmox scrape to Alloy"
   git push

   ssh fx@10.10.10.112 'cd /opt/homelab && git pull && cd observability && op run --env-file=.env -- docker compose restart alloy'
   ```

**Verification:**

1. Check Alloy UI: http://10.10.10.112:12345
   - Find `prometheus.scrape.proxmox` component
   - Should show target UP

2. Check Prometheus:
   ```promql
   # Query Proxmox metrics via Alloy
   pve_up{source="proxmox"}

   # Check all VMs visible
   pve_up

   # Compare with old direct scrape (if still active)
   pve_up{job="proxmox"}  # Old way
   ```

3. Check Grafana Systems Overview dashboard:
   - All VMs should be visible
   - Status indicators working

**Success Criteria:**
- ✅ Proxmox metrics flowing through Alloy
- ✅ All VMs visible in Prometheus
- ✅ Systems Overview dashboard works

---

### Phase 3: Add Home Assistant Scrape to Observability Alloy

**Goal:** Route Home Assistant metrics through Alloy for consistency

**Tasks:**

1. **Update Alloy config** (`observability/alloy/config/config.alloy`):
   ```alloy
   // ============================================================================
   // HOME ASSISTANT: Automation Platform Metrics
   // ============================================================================

   prometheus.scrape "homeassistant" {
     targets = [{
       __address__ = "10.10.10.116:8123",
       job         = "homeassistant",
       instance    = "homeassistant",
       vm          = "ha",
       service     = "automation",
     }]

     metrics_path    = "/api/prometheus"
     scheme          = "http"
     scrape_interval = "60s"

     authorization {
       credentials = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3Y2I1MjgyYWQzMGE0MGIyOTJiZDlmNzA5NTNkMWNiYyIsImlhdCI6MTc2MjEyNDc0MSwiZXhwIjoyMDc3NDg0NzQxfQ.iLKy3vV02-VNluyMMsBFY-jDRUJDIB8gFWIqvt-4bUw"
     }

     forward_to = [prometheus.remote_write.prometheus.receiver]
   }
   ```

2. **Deploy changes:**
   ```bash
   cd /opt/homelab/observability
   git add alloy/config/config.alloy
   git commit -m "Add Home Assistant scrape to Alloy"
   git push

   ssh fx@10.10.10.112 'cd /opt/homelab && git pull && cd observability && op run --env-file=.env -- docker compose restart alloy'
   ```

**Verification:**

1. Check Alloy UI:
   - Find `prometheus.scrape.homeassistant`
   - Should show target UP (not 401/403)

2. Check Alloy logs for auth errors:
   ```bash
   ssh fx@10.10.10.112 'docker logs alloy --tail 50 | grep -i "401\|403\|homeassistant"'
   ```

3. Check Prometheus:
   ```promql
   # Query HA metrics
   homeassistant_sensor_state
   up{job="homeassistant"}
   ```

4. Check Grafana HA dashboard:
   - Entity states visible
   - No gaps in data

**Success Criteria:**
- ✅ HA metrics flowing through Alloy
- ✅ No auth errors
- ✅ HA dashboard shows data

---

### Phase 4: Add Application Metrics Scraping to Observability Alloy

**Goal:** Centralize all app /metrics endpoints through Alloy

**Tasks:**

1. **Update Alloy config** (`observability/alloy/config/config.alloy`):
   ```alloy
   // ============================================================================
   // APPLICATIONS: Service /metrics Endpoints
   // ============================================================================

   prometheus.scrape "apps" {
     targets = [
       {
         __address__ = "10.10.10.110:8082",
         job         = "traefik",
         instance    = "traefik",
         vm          = "edge",
         service     = "proxy",
       },
       {
         __address__ = "grafana:3000",
         job         = "grafana",
         instance    = "grafana",
         vm          = "observability",
         service     = "observability",
       },
       {
         __address__ = "loki:3100",
         job         = "loki",
         instance    = "loki",
         vm          = "observability",
         service     = "observability",
       },
       {
         __address__ = "prometheus:9090",
         job         = "prometheus",
         instance    = "prometheus",
         vm          = "observability",
         service     = "observability",
       },
     ]

     scrape_interval = "15s"
     forward_to = [prometheus.remote_write.prometheus.receiver]
   }
   ```

2. **Deploy changes:**
   ```bash
   cd /opt/homelab/observability
   git add alloy/config/config.alloy
   git commit -m "Add app metrics scraping to Alloy"
   git push

   ssh fx@10.10.10.112 'cd /opt/homelab && git pull && cd observability && op run --env-file=.env -- docker compose restart alloy'
   ```

**Verification:**

1. Check Alloy UI:
   - Find `prometheus.scrape.apps`
   - All 4 targets should be UP

2. Check Prometheus:
   ```promql
   # Traefik metrics
   traefik_entrypoint_requests_total

   # Grafana metrics
   grafana_api_response_status_total

   # Loki metrics
   loki_ingester_streams

   # Prometheus metrics
   prometheus_tsdb_head_samples
   ```

3. Check for duplicate metrics:
   ```promql
   # Should only see one source now
   count by (job) (up{job="traefik"})  # Should be 1
   ```

**Success Criteria:**
- ✅ All app metrics flowing through Alloy
- ✅ No duplicate metrics
- ✅ App dashboards still work

---

### Phase 5: Clean Up Prometheus Configuration

**Goal:** Remove all scrape_configs, make Prometheus pure remote_write receiver

**Tasks:**

1. **Backup current config:**
   ```bash
   cp observability/prometheus/config/prometheus.yml observability/prometheus/config/prometheus.yml.backup
   ```

2. **Update prometheus.yml:**
   ```yaml
   # ============================================================================
   # PROMETHEUS CONFIGURATION - Pure Remote Write Receiver
   # ============================================================================
   # All metrics collected by Alloy and sent via remote_write
   # Prometheus scrapes NOTHING (except optionally itself)
   # ============================================================================

   global:
     scrape_interval: 15s
     evaluation_interval: 15s
     scrape_timeout: 10s
     external_labels:
       cluster: 'homelab'
       environment: 'production'

   # Load alerting rules
   rule_files:
     - '/etc/prometheus/rules/*.yml'

   # ============================================================================
   # SCRAPE CONFIGURATIONS (Minimal/None)
   # ============================================================================

   scrape_configs:
     # Optional: Prometheus self-monitoring
     - job_name: 'prometheus'
       static_configs:
         - targets: ['localhost:9090']
           labels:
             instance: 'prometheus'
             vm: 'observability'
             service: 'observability'

   # ============================================================================
   # NOTES
   # ============================================================================
   # All other metrics come via remote_write from Alloy instances:
   # - Alloy (observability VM): SNMP, Proxmox, HA, apps, local metrics
   # - Alloy (edge VM): edge host + container metrics
   # - Alloy (db VM): db host + container metrics
   # - Alloy (other VMs): host + container metrics
   # ============================================================================
   ```

3. **Deploy changes:**
   ```bash
   cd /opt/homelab/observability
   git add prometheus/config/prometheus.yml
   git commit -m "Simplify Prometheus config - pure remote_write receiver"
   git push

   # Pull and reload
   ssh fx@10.10.10.112 'cd /opt/homelab && git pull'

   # Reload Prometheus config (no restart needed)
   ssh fx@10.10.10.112 'docker exec prometheus kill -HUP 1'

   # OR restart if you prefer
   ssh fx@10.10.10.112 'cd /opt/homelab/observability && op run --env-file=.env -- docker compose restart prometheus'
   ```

**Verification:**

1. Check Prometheus UI: http://10.10.10.112:9090
   - Go to Status → Targets
   - Should only see `prometheus` job (if you kept self-monitoring)
   - All other metrics come via remote_write (not visible in Targets page)

2. Check Prometheus logs:
   ```bash
   ssh fx@10.10.10.112 'docker logs prometheus --tail 100'
   # Look for "Configuration reload successful" or similar
   # No scrape errors
   ```

3. Query all metric sources:
   ```promql
   # SNMP metrics (via Alloy)
   snmp_up

   # Proxmox metrics (via Alloy)
   pve_up

   # HA metrics (via Alloy)
   homeassistant_sensor_state

   # App metrics (via Alloy)
   traefik_entrypoint_requests_total

   # VM metrics (via Alloy on observability VM)
   node_cpu_seconds_total{host="observability"}
   ```

4. Check Grafana dashboards:
   - All existing dashboards should still work
   - No missing data

**Success Criteria:**
- ✅ Prometheus config simplified
- ✅ All metrics still queryable
- ✅ No data loss
- ✅ Grafana dashboards work

**Rollback if needed:**
```bash
cp observability/prometheus/config/prometheus.yml.backup observability/prometheus/config/prometheus.yml
ssh fx@10.10.10.112 'docker exec prometheus kill -HUP 1'
```

---

### Phase 6: Deploy Alloy to Edge VM

**Goal:** Add host + container metrics collection for edge VM

**Tasks:**

1. **Create Alloy config for edge VM:**
   ```bash
   mkdir -p edge/alloy/config
   mkdir -p edge/alloy/data
   ```

2. **Create config file** (`edge/alloy/config/config.alloy`):
   ```alloy
   // ============================================================================
   // GRAFANA ALLOY CONFIGURATION - Edge VM
   // ============================================================================

   // ============================================================================
   // METRICS: System Metrics
   // ============================================================================

   prometheus.exporter.unix "system" {
     enable_collectors = [
       "cpu",
       "cpufreq",
       "diskstats",
       "filesystem",
       "loadavg",
       "meminfo",
       "netdev",
       "netstat",
       "stat",
       "time",
       "uname",
       "vmstat",
     ]
   }

   prometheus.scrape "system_metrics" {
     targets    = prometheus.exporter.unix.system.targets
     forward_to = [prometheus.remote_write.prometheus.receiver]
     scrape_interval = "15s"
   }

   // ============================================================================
   // METRICS: Docker Container Metrics
   // ============================================================================

   prometheus.exporter.cadvisor "docker" {
     docker_host = "unix:///var/run/docker.sock"
     storage_duration = "5m"
     docker_only = false
     store_container_labels = true

     enabled_metrics = [
       "cpu",
       "memory",
       "network",
       "disk",
       "diskIO",
     ]
   }

   prometheus.scrape "docker_metrics" {
     targets    = prometheus.exporter.cadvisor.docker.targets
     forward_to = [prometheus.remote_write.prometheus.receiver]
     scrape_interval = "15s"
   }

   // ============================================================================
   // METRICS: Prometheus Remote Write
   // ============================================================================

   prometheus.remote_write "prometheus" {
     endpoint {
       url = "http://10.10.10.112:9090/api/v1/write"

       headers = {
         "X-Source" = "alloy",
       }
     }

     external_labels = {
       cluster = "homelab",
       host = "edge",
       host_ip = "10.10.10.110",
       collector = "alloy",
       source = "alloy",
     }
   }

   // ============================================================================
   // LOGS: Docker Container Discovery
   // ============================================================================

   discovery.docker "containers" {
     host = "unix:///var/run/docker.sock"
   }

   // ============================================================================
   // LOGS: Docker Container Logs Collection
   // ============================================================================

   loki.source.docker "containers" {
     host       = "unix:///var/run/docker.sock"
     targets    = discovery.docker.containers.targets
     forward_to = [loki.process.add_labels.receiver]

     relabel_rules = discovery.relabel.docker_labels.rules
   }

   discovery.relabel "docker_labels" {
     targets = discovery.docker.containers.targets

     rule {
       source_labels = ["__meta_docker_container_name"]
       regex         = "/(.*)"
       target_label  = "container"
     }

     rule {
       source_labels = ["__meta_docker_container_id"]
       regex         = "(.{12}).*"
       target_label  = "container_id"
     }

     rule {
       source_labels = ["__meta_docker_container_image"]
       target_label  = "image"
     }

     rule {
       source_labels = ["__meta_docker_container_label_com_docker_compose_project"]
       target_label  = "compose_project"
     }

     rule {
       source_labels = ["__meta_docker_container_label_com_docker_compose_service"]
       target_label  = "compose_service"
     }
   }

   // ============================================================================
   // LOGS: Processing and Labeling
   // ============================================================================

   loki.process "add_labels" {
     forward_to = [loki.write.loki.receiver]

     stage.docker {}

     stage.static_labels {
       values = {
         host = "edge",
         cluster = "homelab",
       }
     }

     stage.regex {
       expression = "(?i)level=(?P<level>\\w+)"
     }

     stage.labels {
       values = {
         level = "",
       }
     }
   }

   // ============================================================================
   // LOGS: Loki Write Endpoint
   // ============================================================================

   loki.write "loki" {
     endpoint {
       url = "http://10.10.10.112:3100/loki/api/v1/push"
     }

     external_labels = {
       cluster = "homelab",
     }
   }
   ```

3. **Add Alloy to edge docker-compose.yml:**
   ```yaml
   # Add to edge/docker-compose.yml

   alloy:
     image: grafana/alloy:v1.11.2
     container_name: alloy
     restart: unless-stopped
     privileged: true
     command:
       - run
       - /etc/alloy/config.alloy
       - --server.http.listen-addr=0.0.0.0:12345
       - --storage.path=/var/lib/alloy/data
     ports:
       - "10.10.10.110:12345:12345"  # Alloy web UI
     volumes:
       - ./alloy/config/config.alloy:/etc/alloy/config.alloy:ro
       - /var/run/docker.sock:/var/run/docker.sock:ro
       - /:/host/root:ro
       - /sys:/host/sys:ro
       - /proc:/host/proc:ro
       - /var/lib/docker:/var/lib/docker:ro
       - /dev/disk:/dev/disk:ro
       - /sys/fs/cgroup:/sys/fs/cgroup:ro
       - ./alloy/data:/var/lib/alloy/data
     networks:
       - edge_net  # Use existing network name from edge compose
     environment:
       - HOSTNAME=edge
     healthcheck:
       test: ["CMD-SHELL", "alloy tools pprof health http://localhost:12345 || exit 1"]
       interval: 30s
       timeout: 10s
       retries: 3
       start_period: 20s
     logging:
       driver: "json-file"
       options:
         max-size: "10m"
         max-file: "3"
   ```

4. **Deploy to edge VM:**
   ```bash
   cd /opt/homelab/edge

   # Commit locally
   git add alloy/
   git add docker-compose.yml
   git commit -m "Add Alloy to edge VM"
   git push

   # Pull and deploy on edge VM
   ssh fx@10.10.10.110 'cd /opt/homelab && git pull'
   ssh fx@10.10.10.110 'cd /opt/homelab/edge && op run --env-file=.env -- docker compose up -d alloy'
   ```

**Verification:**

1. Check Alloy running:
   ```bash
   ssh fx@10.10.10.110 'docker ps | grep alloy'
   ```

2. Check Alloy UI: http://10.10.10.110:12345
   - Should see components loaded
   - System and Docker exporters UP

3. Check Alloy logs:
   ```bash
   ssh fx@10.10.10.110 'docker logs alloy --tail 50'
   # Look for successful remote_write
   ```

4. Check Prometheus:
   ```promql
   # Edge VM host metrics
   node_cpu_seconds_total{host="edge"}
   node_memory_MemTotal_bytes{host="edge"}

   # Edge VM containers
   container_cpu_usage_seconds_total{host="edge"}

   # Check specific containers
   container_memory_usage_bytes{host="edge",name=~"traefik|adguard|authentik"}
   ```

5. Check Loki:
   - Grafana → Explore → Loki
   - Query: `{host="edge"}`
   - Should see container logs

**Success Criteria:**
- ✅ Alloy running on edge VM
- ✅ Host metrics in Prometheus
- ✅ Container metrics in Prometheus (traefik, adguard, authentik, etc.)
- ✅ Logs flowing to Loki

---

### Phase 7: Deploy Alloy to DB VM

**Goal:** Add host + container metrics collection for db VM

**Tasks:**

1. **Create Alloy config for db VM:**
   ```bash
   mkdir -p db/alloy/config
   mkdir -p db/alloy/data
   ```

2. **Copy config from edge VM, update labels:**
   ```bash
   cp edge/alloy/config/config.alloy db/alloy/config/config.alloy

   # Edit db/alloy/config/config.alloy
   # Change external_labels:
   #   host = "db"
   #   host_ip = "10.10.10.111"
   # Change loki.process static_labels:
   #   host = "db"
   ```

3. **Add Alloy to db docker-compose.yml:**
   ```yaml
   # Same as edge, but update port binding:
   ports:
     - "10.10.10.111:12345:12345"
   ```

4. **Deploy to db VM:**
   ```bash
   cd /opt/homelab/db

   git add alloy/
   git add docker-compose.yml
   git commit -m "Add Alloy to db VM"
   git push

   ssh fx@10.10.10.111 'cd /opt/homelab && git pull'
   ssh fx@10.10.10.111 'cd /opt/homelab/db && op run --env-file=.env -- docker compose up -d alloy'
   ```

**Verification:**

1. Check Alloy running:
   ```bash
   ssh fx@10.10.10.111 'docker ps | grep alloy'
   ```

2. Check Alloy UI: http://10.10.10.111:12345

3. Check Prometheus:
   ```promql
   # DB VM host metrics
   node_cpu_seconds_total{host="db"}

   # DB VM containers
   container_memory_usage_bytes{host="db",name=~"postgres|mongodb|redis|minio|mosquitto"}
   ```

4. Check Loki:
   ```
   {host="db"}
   ```

**Success Criteria:**
- ✅ Alloy running on db VM
- ✅ Host metrics in Prometheus
- ✅ Database container metrics visible
- ✅ Logs flowing to Loki

---

### Phase 8: Rebuild Grafana Dashboards

**Goal:** Update dashboards to use correct metric sources without overlap

**Tasks:**

1. **Systems Overview Dashboard:**
   - Use ONLY `pve_*` metrics (Proxmox source)
   - Show all VMs in unified table view
   - Stat panels for each VM (status, CPU, memory, disk, network)
   - Drill-down links: `/d/system-detail?var-host=${__value.text}`

2. **VM Detail Dashboard (Generic template for Debian VMs):**
   - Variable: `$host` (edge, db, observability, etc.)
   - Host metrics section:
     - CPU: `rate(node_cpu_seconds_total{host="$host",mode!="idle"}[5m])`
     - Memory: `node_memory_MemTotal_bytes{host="$host"} - node_memory_MemAvailable_bytes{host="$host"}`
     - Disk: `node_filesystem_avail_bytes{host="$host"}`
     - Network: `rate(node_network_transmit_bytes_total{host="$host"}[5m])`
   - Container metrics section:
     - Table: containers by CPU, memory, network
     - Per-container graphs
   - Logs section:
     - Loki panel: `{host="$host"}`

3. **Synology Detail Dashboard:**
   - Use `snmp_*` metrics only
   - Disk volumes, RAID status, temperatures
   - Network traffic

4. **Home Assistant Detail Dashboard:**
   - Use `homeassistant_*` metrics only
   - Entity states, sensor values
   - Automation runs

5. **Application Dashboards:**
   - Traefik: `traefik_*` metrics
   - Databases: Container metrics (until dedicated exporters added)

**Note:** This phase may require manual dashboard editing in Grafana UI. Changes should then be exported to JSON and committed to git.

**Verification:**
- Load each dashboard
- Verify data displays correctly
- Check for duplicate/missing metrics
- Test variable dropdowns
- Test drill-down links

---

### Phase 9: Remove SNMP Exporter Container

**Goal:** Clean up redundant snmp-exporter container

**Tasks:**

1. **Comment out in docker-compose.yml:**
   ```yaml
   # snmp-exporter:
   #   image: prom/snmp-exporter:latest
   #   ...
   ```

2. **Remove container:**
   ```bash
   ssh fx@10.10.10.112 'cd /opt/homelab/observability && docker compose rm -sf snmp-exporter'
   ```

3. **Keep config as backup:**
   ```bash
   # Keep observability/snmp-exporter/snmp.yml for reference
   ```

**Verification:**
- SNMP metrics still flowing (via Alloy)
- Synology dashboard works
- Container removed: `docker ps` doesn't show snmp-exporter

---

### Phase 10: Update Documentation

**Goal:** Document the new architecture in README.md

**Tasks:**

1. Update README.md sections:
   - Monitoring Architecture
   - Alloy deployment pattern
   - How to add new VMs
   - How to add new SNMP devices
   - Troubleshooting Alloy

2. Add architecture diagram (ASCII art)

3. Document metric collection strategy

4. Update "Service Deployment" section with Alloy

**Deliverables:**
- Clear documentation of pure Alloy architecture
- Instructions for extending monitoring
- Troubleshooting guide

---

## Verification Checklist

### After Phases 1-5 (Observability VM Complete)

- [ ] Alloy collecting SNMP from Synology
- [ ] Alloy scraping Proxmox exporter
- [ ] Alloy scraping Home Assistant
- [ ] Alloy scraping apps (Traefik, Grafana, Loki, Prometheus)
- [ ] Alloy collecting local observability VM metrics
- [ ] All metrics forwarding to Prometheus via remote_write
- [ ] Prometheus has simplified scrape_configs
- [ ] All existing Grafana dashboards still work
- [ ] No missing metrics
- [ ] Alloy UI shows all targets UP

### After Phases 6-7 (Edge + DB VMs)

- [ ] Alloy running on edge VM
- [ ] Alloy running on db VM
- [ ] Edge VM host metrics in Prometheus
- [ ] Edge VM container metrics in Prometheus
- [ ] DB VM host metrics in Prometheus
- [ ] DB VM container metrics in Prometheus
- [ ] Logs from both VMs flowing to Loki
- [ ] Metrics properly labeled with `host`, `source`, etc.

### After Phase 8 (Dashboards)

- [ ] Systems Overview uses Proxmox metrics only
- [ ] VM Detail dashboards use Alloy metrics
- [ ] Synology dashboard uses SNMP metrics
- [ ] HA dashboard uses HA API metrics
- [ ] No overlapping/duplicate metrics in dashboards
- [ ] Drill-down links work
- [ ] Variables work correctly

### Final Checklist

- [ ] All VMs monitored (edge, db, observability, synology, ha)
- [ ] All metrics flowing through Alloy
- [ ] Prometheus is pure remote_write receiver
- [ ] All Grafana dashboards functional
- [ ] snmp-exporter container removed
- [ ] Documentation updated
- [ ] No errors in logs (Alloy, Prometheus, Grafana, Loki)

---

## Rollback Strategy

### Phase-by-Phase Rollback

**If Phase 1 fails (SNMP):**
- Revert Alloy config changes
- Keep snmp-exporter container running
- Prometheus continues scraping snmp-exporter directly

**If Phase 2 fails (Proxmox):**
- Revert Alloy config changes
- Prometheus continues scraping proxmox-exporter directly

**If Phase 3 fails (Home Assistant):**
- Revert Alloy config changes
- Prometheus continues scraping HA directly

**If Phase 5 fails (Prometheus config):**
- Restore from backup: `prometheus.yml.backup`
- Reload Prometheus: `docker exec prometheus kill -HUP 1`

**If Phase 6/7 fails (VM Alloy deployment):**
- Remove Alloy from affected VM
- VM continues to be monitored via Proxmox exporter only

### Complete Rollback

If entire implementation needs to be rolled back:

1. Restore `prometheus.yml.backup`
2. Revert Alloy config on observability VM
3. Restart Prometheus
4. Keep snmp-exporter container
5. Remove Alloy from edge/db VMs
6. All monitoring falls back to original state

---

## Reference Information

### Current Infrastructure

**VMs:**
- edge: 10.10.10.110 (Traefik, AdGuard, Authentik, NetBird)
- db: 10.10.10.111 (PostgreSQL, MongoDB, Redis, MinIO, Mosquitto)
- observability: 10.10.10.112 (Prometheus, Grafana, Loki, Alloy, Portainer)
- media: 10.10.10.113 (Plex, Sonarr, Radarr, etc.)
- dev: 10.10.10.114 (Gitea, Docker Registry)
- deploy: 10.10.10.101 (Coolify)
- ha: 10.10.10.116 (Home Assistant OS)
- synology: 10.10.10.100 (Xpenology NAS)
- proxmox: 10.10.10.20 (Hypervisor)

**Ports:**
- Prometheus: 9090
- Grafana: 3000
- Loki: 3100
- Alloy: 12345
- SNMP Exporter: 9116
- Proxmox Exporter: 9221

### Alloy Component Reference

**prometheus.exporter.unix** - System metrics (CPU, memory, disk, network)
**prometheus.exporter.cadvisor** - Docker container metrics
**prometheus.exporter.snmp** - SNMP device monitoring
**prometheus.scrape** - Generic metrics scraping
**prometheus.remote_write** - Send metrics to Prometheus
**loki.source.docker** - Docker container logs
**loki.write** - Send logs to Loki
**discovery.docker** - Discover Docker containers
**discovery.relabel** - Relabel discovered targets

### Useful Commands

**Check Alloy status:**
```bash
docker ps | grep alloy
docker logs alloy --tail 50
curl http://10.10.10.112:12345/-/healthy
```

**Reload Alloy config (no restart):**
```bash
# Alloy auto-reloads config file changes
# Just update the file and it picks it up
```

**Reload Prometheus config:**
```bash
docker exec prometheus kill -HUP 1
# OR
curl -X POST http://10.10.10.112:9090/-/reload
```

**Test SNMP manually:**
```bash
snmpwalk -v2c -c public 10.10.10.100 1.3.6.1.2.1.1.5
```

**Query Prometheus metrics:**
```bash
curl 'http://10.10.10.112:9090/api/v1/query?query=up'
```

**Check Loki logs:**
```bash
curl 'http://10.10.10.112:3100/loki/api/v1/query?query={host="edge"}'
```

---

## Next Steps After Implementation

Once all phases are complete, consider:

1. **Add more VMs:** Deploy Alloy to media, dev, deploy VMs
2. **Add app-specific exporters:**
   - AdGuard exporter (edge VM)
   - PostgreSQL exporter (db VM)
   - MongoDB exporter (db VM)
   - Redis exporter (db VM)
3. **Enable OpenTelemetry receiver** in Alloy for custom app instrumentation
4. **Add alerting rules** in Prometheus
5. **Add Alertmanager** for notifications
6. **Add more SNMP devices** (network switches, UPS, etc.)

---

## Important Notes

- **DO NOT rush** - verify each phase before proceeding
- **Keep backups** - git commits at each step
- **Test in Grafana** - ensure dashboards work after each change
- **Monitor Alloy UI** - watch for target failures
- **Check logs frequently** - catch errors early
- **Document deviations** - update this plan if you change approach

---

**Created by:** Claude Code
**Date:** 2025-11-04
**Status:** Ready for Implementation ✅
