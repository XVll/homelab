# Adding System Monitoring to Home Assistant

To see CPU, RAM, and Disk metrics for your Home Assistant VM in Grafana, you need to add the **System Monitor integration** to Home Assistant.

## Step 1: Add System Monitor Integration

**Option A - Via UI (Recommended):**
1. Open Home Assistant: http://10.10.10.116:8123
2. Go to **Settings** → **Devices & Services** → **Integrations**
3. Click **+ ADD INTEGRATION** (bottom right)
4. Search for **"System Monitor"**
5. Click **System Monitor** and add it

**Option B - Via configuration.yaml:**

Add this to your `configuration.yaml`:

```yaml
# System monitoring sensors
sensor:
  - platform: systemmonitor
    resources:
      # CPU
      - type: processor_use
      - type: processor_temperature
      - type: load_1m
      - type: load_5m
      - type: load_15m

      # Memory
      - type: memory_use_percent
      - type: memory_use
      - type: memory_free

      # Swap
      - type: swap_use_percent
      - type: swap_use
      - type: swap_free

      # Disk (/ mount point)
      - type: disk_use_percent
        arg: /
      - type: disk_use
        arg: /
      - type: disk_free
        arg: /

      # Network (adjust interface name if needed)
      - type: network_in
        arg: eth0
      - type: network_out
        arg: eth0
      - type: throughput_network_in
        arg: eth0
      - type: throughput_network_out
        arg: eth0

      # System
      - type: last_boot
```

Then restart Home Assistant.

## Step 2: Enable the Sensors

If you used the UI method, the sensors are disabled by default:

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Find **System Monitor**
3. Click on it to see all sensors
4. **Enable** the sensors you want:
   - Processor use (%)
   - Memory use (%)
   - Disk use (%)
   - Load (1m, 5m, 15m)
   - Network throughput
   - Any others you want

## Step 3: Verify Sensors Are Working

1. Go to **Developer Tools** → **States**
2. Filter for `sensor.processor_use` or `sensor.memory_use_percent`
3. You should see values like `5.2` (meaning 5.2% CPU usage)

## Step 4: Check Prometheus is Exporting Them

Once the sensors are enabled, they'll automatically be exported via the Prometheus integration.

Wait 60 seconds for Prometheus to scrape, then check:

```bash
# Check if CPU sensor is available
curl -s 'http://10.10.10.112:9090/api/v1/query?query=homeassistant_sensor_state{entity="sensor.processor_use"}' | python3 -m json.tool

# Check if memory sensor is available
curl -s 'http://10.10.10.112:9090/api/v1/query?query=homeassistant_sensor_state{entity="sensor.memory_use_percent"}' | python3 -m json.tool
```

## Step 5: Dashboard Will Update Automatically

Once the sensors are available in Prometheus, the Home Assistant detail dashboard will show:
- CPU usage
- Memory usage
- Disk usage
- Network throughput
- System load

## Troubleshooting

### Sensors not appearing in Prometheus

**Check sensor state in HA:**
```
Developer Tools → States → search for "processor" or "memory"
```

**Check if sensors are enabled:**
- Settings → Devices & Services → System Monitor → click on it
- Make sure sensors aren't disabled

**Wait for scrape:**
- Prometheus scrapes every 60 seconds
- Wait 1-2 minutes after enabling sensors

### Which network interface to monitor?

Home Assistant OS typically uses `eth0` or `enp0s3`. To find yours:
- Settings → System → Network
- Or check: Developer Tools → States → filter for "network"

## Expected Metrics After Setup

You should see these metrics in Prometheus:

```
homeassistant_sensor_state{entity="sensor.processor_use"}           # CPU %
homeassistant_sensor_state{entity="sensor.memory_use_percent"}      # RAM %
homeassistant_sensor_state{entity="sensor.disk_use_percent_"}       # Disk %
homeassistant_sensor_state{entity="sensor.load_1m"}                 # Load average
homeassistant_sensor_state{entity="sensor.network_throughput_in_eth0"}   # Network RX
homeassistant_sensor_state{entity="sensor.network_throughput_out_eth0"}  # Network TX
```

## Alternative: Monitor HA VM with Alloy

If you want more detailed system metrics (like other VMs), you could also deploy Alloy on the HA VM. However, since HA OS is a specialized appliance OS, it's easier to just use the System Monitor integration.
