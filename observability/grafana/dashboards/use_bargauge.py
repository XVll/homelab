#!/usr/bin/env python3
"""
Replace stat panel with bar gauge + sparklines
"""
import json

# Read the dashboard
with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Remove the panel we just added
dashboard['panels'] = [p for p in dashboard['panels'] if p['id'] != 100]

# Create bar gauge panel for current values
bargauge_panel = {
    "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
    },
    "description": "Current resource usage",
    "fieldConfig": {
        "defaults": {
            "color": {
                "mode": "thresholds"
            },
            "mappings": [],
            "min": 0,
            "max": 1,
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {
                        "color": "green",
                        "value": None
                    },
                    {
                        "color": "yellow",
                        "value": 0.7
                    },
                    {
                        "color": "red",
                        "value": 0.9
                    }
                ]
            },
            "unit": "percentunit",
            "decimals": 1
        },
        "overrides": []
    },
    "gridPos": {
        "h": 15,
        "w": 6,
        "x": 18,
        "y": 6
    },
    "id": 101,
    "options": {
        "reduceOptions": {
            "values": False,
            "calcs": [
                "lastNotNull"
            ],
            "fields": ""
        },
        "orientation": "horizontal",
        "displayMode": "gradient",
        "minVizHeight": 10,
        "minVizWidth": 0,
        "showUnfilled": True,
        "text": {
            "titleSize": 14,
            "valueSize": 18
        }
    },
    "pluginVersion": "11.4.0",
    "targets": [
        {
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "expr": "pve_cpu_usage_ratio{instance=\"$instance\"} / pve_cpu_usage_limit and on(id) pve_node_info",
            "instant": True,
            "legendFormat": "CPU",
            "refId": "CPU"
        },
        {
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "expr": "pve_memory_usage_bytes{instance=\"$instance\"} / pve_memory_size_bytes and on(id) pve_node_info",
            "instant": True,
            "legendFormat": "Memory",
            "refId": "Memory"
        },
        {
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "expr": "pve_disk_usage_bytes{instance=\"$instance\", id=~\"storage/.+\"} / pve_disk_size_bytes * on (id, instance) group_left(storage) pve_storage_info",
            "instant": True,
            "legendFormat": "{{storage}}",
            "refId": "Storage"
        }
    ],
    "title": "Current Usage",
    "type": "bargauge"
}

# Create CPU sparkline panel
cpu_sparkline = {
    "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
    },
    "fieldConfig": {
        "defaults": {
            "color": {
                "mode": "thresholds"
            },
            "mappings": [],
            "min": 0,
            "max": 1,
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {
                        "color": "green",
                        "value": None
                    },
                    {
                        "color": "yellow",
                        "value": 0.7
                    },
                    {
                        "color": "red",
                        "value": 0.9
                    }
                ]
            },
            "unit": "percentunit",
            "decimals": 1
        },
        "overrides": []
    },
    "gridPos": {
        "h": 3,
        "w": 6,
        "x": 18,
        "y": 0
    },
    "id": 102,
    "options": {
        "reduceOptions": {
            "values": False,
            "calcs": [
                "lastNotNull"
            ],
            "fields": ""
        },
        "orientation": "horizontal",
        "textMode": "value",
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "center",
        "text": {
            "valueSize": 20
        }
    },
    "pluginVersion": "11.4.0",
    "targets": [
        {
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "expr": "pve_cpu_usage_ratio{instance=\"$instance\"} / pve_cpu_usage_limit and on(id) pve_node_info",
            "range": True,
            "legendFormat": "CPU",
            "refId": "A"
        }
    ],
    "title": "CPU",
    "type": "stat"
}

# Create Memory sparkline panel
memory_sparkline = {
    "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
    },
    "fieldConfig": {
        "defaults": {
            "color": {
                "mode": "thresholds"
            },
            "mappings": [],
            "min": 0,
            "max": 1,
            "thresholds": {
                "mode": "absolute",
                "steps": [
                    {
                        "color": "green",
                        "value": None
                    },
                    {
                        "color": "yellow",
                        "value": 0.75
                    },
                    {
                        "color": "red",
                        "value": 0.9
                    }
                ]
            },
            "unit": "percentunit",
            "decimals": 1
        },
        "overrides": []
    },
    "gridPos": {
        "h": 3,
        "w": 6,
        "x": 18,
        "y": 3
    },
    "id": 103,
    "options": {
        "reduceOptions": {
            "values": False,
            "calcs": [
                "lastNotNull"
            ],
            "fields": ""
        },
        "orientation": "horizontal",
        "textMode": "value",
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "center",
        "text": {
            "valueSize": 20
        }
    },
    "pluginVersion": "11.4.0",
    "targets": [
        {
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "expr": "pve_memory_usage_bytes{instance=\"$instance\"} / pve_memory_size_bytes and on(id) pve_node_info",
            "range": True,
            "legendFormat": "Memory",
            "refId": "A"
        }
    ],
    "title": "Memory",
    "type": "stat"
}

# Add all new panels
dashboard['panels'].extend([cpu_sparkline, memory_sparkline, bargauge_panel])

# Write back
with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("✓ Created bar gauge panel for current values (ID: 101)")
print("✓ Created CPU sparkline panel (ID: 102)")
print("✓ Created Memory sparkline panel (ID: 103)")
print("✓ Layout: sparklines on top, bar gauges below")
