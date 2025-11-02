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
curl "http://localhost:9116/snmp?target=10.10.10.100&module=synology&auth=homelab_v2"
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

**System Info:**
```promql
systemStatus{instance="10.10.10.100"}       # Overall system status (1=Normal)
systemFanStatus{instance="10.10.10.100"}    # System fan status (1=Normal)
cpuFanStatus{instance="10.10.10.100"}       # CPU fan status (1=Normal)
modelName{instance="10.10.10.100"}          # Model name
```

**Temperature:**
```promql
temperature{instance="10.10.10.100"}                      # System temperature (Celsius)
diskTemperature{instance="10.10.100"}                     # Disk temperature (Celsius)
```

**Disk Health:**
```promql
diskHealthStatus{instance="10.10.10.100"}   # Disk health (1=Normal, 2=Warning, 3=Critical)
diskStatus{instance="10.10.10.100"}         # Disk status (1=Normal, 2=Initialized, 3=NotInitialized, 4=SystemPartitionFailed, 5=Crashed)
diskBadSector{instance="10.10.10.100"}      # Bad sector count (0 is good)
diskRetry{instance="10.10.10.100"}          # Retry count (0 is good)
diskIdentifyFail{instance="10.10.10.100"}   # Identify fail count (0 is good)
```

**RAID Status:**
```promql
raidStatus{instance="10.10.10.100"}         # RAID array status (1=Normal, 2=Repairing, 3=Migrating, ...)
raidFreeSize{instance="10.10.10.100"}       # Free space in RAID (bytes)
raidTotalSize{instance="10.10.10.100"}      # Total RAID size (bytes)
```

**RAID Usage Percentage:**
```promql
(1 - (raidFreeSize{instance="10.10.10.100"} / raidTotalSize{instance="10.10.10.100"})) * 100
```

**SMART Metrics:**
```promql
diskSMARTAttrCurrent{instance="10.10.10.100"}    # Current SMART values
diskSMARTAttrStatus{instance="10.10.10.100"}     # SMART status (0=Failed, 1=OK)
```

**Services:**
```promql
serviceName{instance="10.10.10.100"}        # List of services
serviceUsers{instance="10.10.10.100"}       # Active users per service
```

**Network:**
```promql
laLoadInt1{instance="10.10.10.100"}         # Load average (1 min)
laLoadInt5{instance="10.10.10.100"}         # Load average (5 min)
laLoadInt15{instance="10.10.10.100"}        # Load average (15 min)
```

**iSCSI LUN:**
```promql
iSCSILUNInfoStatus{instance="10.10.10.100"}    # iSCSI LUN status
iSCSILUNName{instance="10.10.10.100"}          # iSCSI LUN names
```

## Metrics Available (71 Total)

The SNMP exporter collects comprehensive metrics from your Synology:

### System Health
- `systemStatus` - Overall system health (1=Normal, 2=Failed)
- `systemFanStatus` - System fan health (1=Normal, 2=Failed)
- `cpuFanStatus` - CPU fan health (1=Normal, 2=Failed)
- `temperature` - System temperature in Celsius
- `powerStatus` - Power supply status
- `upgradeAvailable` - Firmware upgrade available (1=Available, 2=Unavailable, 3=Connecting, 4=Disconnected, 5=Others)
- `modelName` - Synology model name
- `serialNumber` - Device serial number
- `version` - DSM version

### Disk Health (Per Disk)
- `diskStatus` - Disk status (1=Normal, 2=Initialized, 3=NotInitialized, 4=SystemPartitionFailed, 5=Crashed)
- `diskHealthStatus` - S.M.A.R.T health (1=Normal, 2=Warning, 3=Critical, 4=Failing)
- `diskTemperature` - Disk temperature in Celsius
- `diskBadSector` - Bad sector count
- `diskRetry` - Retry count
- `diskIdentifyFail` - Identify failure count
- `diskRemainLife` - Estimated remaining life percentage
- `diskModel` - Disk model name
- `diskRole` - Disk role in system

### SMART Data (Per Disk)
- `diskSMARTAttrCurrent` - Current SMART values
- `diskSMARTAttrWorst` - Worst recorded SMART values
- `diskSMARTAttrThreshold` - SMART thresholds
- `diskSMARTAttrRaw` - Raw SMART data
- `diskSMARTAttrStatus` - SMART test status (0=Failed, 1=OK)

### RAID Arrays
- `raidStatus` - RAID status (1=Normal, 2=Repairing, 3=Migrating, 4=Expanding, 5=Deleting, 6=Creating, 7=RaidSyncing, 8=RaidParityChecking, 9=RaidAssembling, 10=Canceling, 11=Degrade, 12=Crashed)
- `raidName` - RAID volume name
- `raidFreeSize` - Free space (bytes)
- `raidTotalSize` - Total size (bytes)

### Services
- `serviceName` - DSM service name
- `serviceUsers` - Active users per service

### Network & Performance
- `laLoadInt1` - 1-minute load average
- `laLoadInt5` - 5-minute load average
- `laLoadInt15` - 15-minute load average

### iSCSI (if enabled)
- `iSCSILUNInfoStatus` - LUN status
- `iSCSILUNName` - LUN name
- `iSCSILUNThinProvisioning` - Thin provisioning enabled
- `iSCSILUNUUID` - LUN UUID

### Flash Cache (if configured)
- `flashCacheSpaceName` - Cache space name
- `flashCacheSpaceStatus` - Cache space status

## Troubleshooting

**Target shows DOWN in Prometheus:**
```bash
# Test SNMP manually from observability VM
docker run --rm --network=container:snmp-exporter alpine/snmpwalk -v2c -c homelab 10.10.10.100

# Check if Synology firewall is blocking
# Synology → Control Panel → Security → Firewall
# Add rule to allow 10.10.10.112 (observability VM) on UDP port 161
```

**No metrics or errors:**
```bash
# Check SNMP exporter logs
docker compose logs snmp-exporter

# Verify SNMP community matches
curl "http://localhost:9116/snmp?target=10.10.10.100&module=synology&auth=homelab_v2"
```

**Verify SNMP is listening on Synology:**
```bash
# SSH to Synology and check
sudo netstat -ulnp | grep 161

# Should show:
# udp        0      0 0.0.0.0:161             0.0.0.0:*                           28866/snmpd
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
