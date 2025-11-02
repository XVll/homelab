# Netdata Setup - Hybrid Monitoring Approach

**Philosophy:** Test Netdata alongside existing Grafana stack to compare real-time monitoring capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Observability VM (10.10.10.112)                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Netdata Parent (Hub)                                 │   │
│  │ - Receives streams from agents                       │   │
│  │ - Stores all metrics (dbengine - 2GB)               │   │
│  │ - Unified dashboard for all VMs                     │   │
│  │ - Access: https://netdata.onurx.com                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ Stream metrics
                           │ (API key auth)
                           │
┌──────────────────────────┴──────────────────────────────────┐
│  Media VM (10.10.10.113)                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Netdata Agent                                        │   │
│  │ - Collects local metrics (CPU, RAM, disk, Docker)   │   │
│  │ - Streams to parent                                  │   │
│  │ - 1-hour local retention (RAM mode)                 │   │
│  │ - Access: http://10.10.10.113:19999 (optional)      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Steps

### 1. Deploy Netdata Parent (Observability VM)

SSH to observability VM and deploy:

```bash
cd /opt/homelab
git pull
op run --env-file=.env -- docker compose up -d netdata
```

Wait 30 seconds for Netdata to start, then check:

```bash
# Check status
docker compose ps netdata
docker compose logs -f netdata

# Verify web UI is accessible
curl -I http://localhost:19999
```

**Expected output:** HTTP 200 OK

### 2. Deploy Netdata Agent (Media VM)

SSH to media VM and deploy:

```bash
cd /opt/homelab
git pull
docker compose up -d netdata
```

Wait 30 seconds, then check:

```bash
# Check status
docker compose ps netdata
docker compose logs -f netdata

# Verify it's streaming to parent
docker compose logs netdata | grep -i stream
```

**Expected output:** You should see "STREAM [send to 10.10.10.112:19999]: connected"

### 3. Verify in Netdata Parent Dashboard

Open in browser: **https://netdata.onurx.com** (via Traefik)

Or direct: **http://10.10.10.112:19999**

**What to look for:**

1. **Top menu** - Should show 2 nodes:
   - observability-netdata (local)
   - media-netdata (streamed)

2. **Metrics visible:**
   - System CPU, RAM, Disk, Network
   - Docker containers (all running containers on both VMs)
   - Real-time graphs updating every second

3. **Media VM specific:**
   - Plex, Sonarr, Radarr, qBittorrent containers
   - NAS mount metrics (/host/media)

### 4. Compare with Grafana

Open side-by-side:
- **Netdata:** https://netdata.onurx.com
- **Grafana:** https://grafana.onurx.com

**Things to compare:**

| Feature | Netdata | Grafana + Prometheus |
|---------|---------|----------------------|
| **Update frequency** | 1 second | 15 seconds |
| **Docker containers** | Auto-detected | Alloy collects |
| **Dashboard setup** | Zero config | Manual/import |
| **Historical data** | 4 hours parent + 1 hour agent | 90 days |
| **Drill-down** | Built-in | Need to build |
| **Alerting** | Built-in | Need Prometheus rules |
| **Log viewing** | systemd-journal only | Loki (Docker logs) |

## Configuration Details

### API Key Authentication

Both parent and agent use the same API key for secure streaming:

```
API Key: 11111111-2222-3333-4444-555555555555
```

**Security note:** This is a placeholder. In production, generate a secure UUID:
```bash
uuidgen
```

Update in:
- `observability/netdata/config/stream.conf` (parent)
- `media/netdata/config/stream.conf` (agent)

### Storage & Retention

**Parent (observability VM):**
- Mode: `dbengine` (compressed, on-disk)
- Local retention: 4 hours
- Multi-host storage: 2GB max
- Location: `./netdata/data`

**Agent (media VM):**
- Mode: `ram` (in-memory, fast)
- Local retention: 1 hour
- Data sent to parent: indefinite (parent's retention)
- Location: `./netdata/data` (minimal usage)

### Resource Usage

**Expected resource consumption:**

**Observability VM (Parent):**
- CPU: 5-8% (parent + own monitoring)
- RAM: ~200-300MB
- Disk: Up to 2GB (dbengine storage)

**Media VM (Agent):**
- CPU: 3-5% (agent only)
- RAM: ~150-200MB
- Disk: ~50MB (config + cache)

## Troubleshooting

### Agent not connecting to parent

```bash
# On media VM, check logs
docker compose logs netdata | grep -i stream

# Common issues:
# 1. Firewall blocking port 19999
sudo ufw allow from 10.10.10.113 to any port 19999

# 2. API key mismatch
# Check: media/netdata/config/stream.conf matches observability/netdata/config/stream.conf

# 3. Parent not running
# On observability VM:
docker compose ps netdata
```

### Metrics not appearing

```bash
# Check Netdata is collecting data locally first
curl http://localhost:19999/api/v1/charts | jq

# Should return JSON with all available charts
```

### High CPU usage

Netdata is resource-intensive. If CPU usage is too high:

1. **Disable some collectors** (edit `netdata.conf`):
```ini
[plugins]
    tc = no              # Traffic control (rarely needed)
    idlejitter = no      # Idle jitter (rarely needed)
    apps = no            # Per-app tracking (heavy)
```

2. **Reduce update frequency** (edit `netdata.conf`):
```ini
[global]
    update every = 2     # Update every 2 seconds instead of 1
```

3. **Restart Netdata:**
```bash
docker compose restart netdata
```

## Adding More Agents

To add Netdata agents to other VMs (edge, db, etc.):

1. **Copy the media VM agent config:**
```bash
# On observability VM (git repo):
cp -r media/netdata edge/netdata
# OR
cp -r media/netdata db/netdata
```

2. **Update hostname** in `edge/netdata/config/netdata.conf`:
```ini
[global]
    hostname = edge-netdata  # Change this
```

3. **Add to docker-compose.yml** (same config as media VM, just change hostname)

4. **Deploy:**
```bash
# On edge VM:
cd /opt/homelab
git pull
docker compose up -d netdata
```

5. **Verify in parent dashboard** - new node should appear automatically

## Netdata Cloud (Optional)

Netdata Cloud provides:
- Remote access from anywhere
- Multi-infrastructure monitoring
- Team collaboration
- Alerts via email/Slack

**To enable:**

1. Sign up at https://app.netdata.cloud
2. Create a space
3. Get claim token
4. Add to `observability/.env`:
```bash
NETDATA_CLAIM_TOKEN=your-token-here
NETDATA_CLAIM_ROOMS=your-room-id
```

5. Restart Netdata:
```bash
docker compose restart netdata
```

**Note:** Netdata Cloud is free for unlimited nodes (community edition).

## Next Steps

After testing Netdata:

1. **Compare dashboards** - Netdata vs Grafana
2. **Check resource usage** - Is 5-8% CPU acceptable?
3. **Test Docker monitoring** - Does it show all containers?
4. **Try log explorer** - Does systemd-journal view work?
5. **Decide:**
   - Keep both (hybrid approach)
   - Use Netdata for some VMs, Grafana for others
   - Export Netdata metrics to Prometheus (best of both worlds)

## Exporting Netdata to Prometheus (Advanced)

You can have Netdata export metrics to your existing Prometheus:

Edit `observability/netdata/config/exporting.conf`:
```ini
[exporting:global]
    enabled = yes

[prometheus:local]
    enabled = yes
    destination = prometheus:9090
    data source = average
    prefix = netdata
    update every = 15
    send names instead of ids = yes
```

Restart Netdata - now Prometheus scrapes Netdata's metrics too!

Access: https://prometheus.onurx.com
Query: `netdata_system_cpu_percentage_average`
