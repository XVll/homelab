# Synology NAS Monitoring via SNMP

**No Docker or agents needed on Synology!** Uses SNMP protocol for lightweight monitoring.

## Setup Steps

### 1. Enable SNMP on Synology

SSH to Synology and check current SNMP status:
```bash
sudo synoservicecfg --status snmpd
```

If not enabled, enable via DSM web interface:
1. DSM → Control Panel → Terminal & SNMP
2. Click **SNMP** tab
3. Enable **SNMPv1, SNMPv2c service**
4. Community: Change from `public` to `homelab` (for security)
5. Click **Apply**

**Or enable via SSH:**
```bash
# Enable SNMP service
sudo synoservicecfg --enable snmpd
sudo synoservice --restart snmpd

# Verify it's running
sudo synoservicecfg --status snmpd
ps aux | grep snmpd
```

### 2. Update SNMP Exporter Config (if you changed community name)

If you changed the SNMP community from `public` to something else (recommended):

Edit `observability/snmp-exporter/snmp.yml`:
```yaml
synology:
  version: 2
  auth:
    community: homelab  # Change this to match your SNMP community
```

### 3. Deploy SNMP Exporter

On **observability VM**:
```bash
cd /opt/homelab
op run --env-file=.env -- docker compose up -d snmp-exporter
```

Wait 10-20 seconds, then verify:
```bash
# Check SNMP exporter is running
docker compose ps snmp-exporter

# Check logs
docker compose logs -f snmp-exporter

# Test SNMP exporter can reach Synology
curl "http://localhost:9116/snmp?target=10.10.10.116&module=synology"
```

You should see lots of metrics output if working correctly.

### 4. Reload Prometheus Config

```bash
# Reload Prometheus to pick up new scrape target
docker compose exec prometheus wget --post-data='' http://localhost:9090/-/reload
# Or just restart
docker compose restart prometheus
```

### 5. Verify in Prometheus

1. Open Prometheus: https://prometheus.onurx.com
2. Go to **Status → Targets**
3. Look for `synology` job
4. Should show **State: UP** with green indicator

### 6. Query Synology Metrics

In Prometheus, try these queries:

**CPU Usage:**
```promql
hrProcessorLoad{instance="10.10.10.116"}
```

**Memory Usage:**
```promql
hrStorageUsed{instance="10.10.10.116",hrStorageDescr=~".*Memory.*"}
/ hrStorageSize{instance="10.10.10.116",hrStorageDescr=~".*Memory.*"} * 100
```

**Disk Usage:**
```promql
hrStorageUsed{instance="10.10.10.116",hrStorageDescr=~"^/volume.*"}
/ hrStorageSize{instance="10.10.10.116",hrStorageDescr=~"^/volume.*"} * 100
```

**Network Traffic:**
```promql
rate(ifInOctets{instance="10.10.10.116"}[5m]) * 8  # Bits per second in
rate(ifOutOctets{instance="10.10.10.116"}[5m]) * 8  # Bits per second out
```

**System Uptime:**
```promql
sysUpTime{instance="10.10.10.116"} / 100 / 86400  # Days
```

**Temperature (Synology-specific):**
```promql
{instance="10.10.10.116",__name__=~".*temp.*"}
```

## Metrics Available

The SNMP exporter will collect:

- **System Info**: Model, uptime, hostname
- **CPU**: Processor load
- **Memory**: Total, used, available
- **Disk**: Volume usage, RAID status
- **Network**: Interface stats, traffic, errors
- **Temperature**: System and disk temps
- **Services**: DSM service status
- **RAID**: Array health and status

## Troubleshooting

**Target shows DOWN in Prometheus:**
```bash
# Test SNMP manually from observability VM
docker run --rm --network=container:snmp-exporter alpine/snmpwalk -v2c -c homelab 10.10.10.116

# Check if Synology firewall is blocking
# Synology → Control Panel → Security → Firewall
# Add rule to allow 10.10.10.112 (observability VM) on UDP port 161
```

**No metrics or errors:**
```bash
# Check SNMP exporter logs
docker compose logs snmp-exporter

# Verify SNMP community matches
curl "http://localhost:9116/snmp?target=10.10.10.116&module=synology"
```

**Want more metrics:**
- Synology MIBs are at: `/usr/share/snmp/mibs/`
- Can extend `snmp.yml` with more OIDs
- Reference: https://global.download.synology.com/download/Document/Software/DeveloperGuide/Firmware/DSM/All/enu/Synology_MIB_File.zip

## Alternative: Synology API

If SNMP doesn't provide enough detail, you can also:
1. Use Synology's official API (requires auth token)
2. Deploy a custom exporter that calls DSM API
3. Use existing community exporters like `synology-prometheus-exporter`

But SNMP is the lightest and requires no agents on Synology.
