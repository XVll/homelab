#!/usr/bin/env python3
"""
Create separate bar gauge panels for CPU, Memory, and Storage
"""
import json

# Read the dashboard
with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Remove the panels we just created
dashboard['panels'] = [p for p in dashboard['panels'] if p['id'] not in [101, 102, 103]]

# CPU Panel - bar gauge with sparkline
cpu_panel = {
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
        "h": 4,
        "w": 6,
        "x": 18,
        "y": 0
    },
    "id": 110,
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
            "instant": True,
            "legendFormat": "CPU",
            "refId": "A"
        }
    ],
    "title": "CPU",
    "type": "bargauge"
}

# Memory Panel - bar gauge with sparkline
memory_panel = {
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
        "h": 4,
        "w": 6,
        "x": 18,
        "y": 4
    },
    "id": 111,
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
            "instant": True,
            "legendFormat": "Memory",
            "refId": "A"
        }
    ],
    "title": "Memory",
    "type": "bargauge"
}

# Storage Panel - bar gauge
storage_panel = {
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
        "h": 8,
        "w": 6,
        "x": 18,
        "y": 8
    },
    "id": 112,
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
            "expr": "pve_disk_usage_bytes{instance=\"$instance\", id=~\"storage/.+\"} / pve_disk_size_bytes * on (id, instance) group_left(storage) pve_storage_info",
            "instant": True,
            "legendFormat": "{{storage}}",
            "refId": "A"
        }
    ],
    "title": "Storage",
    "type": "bargauge"
}

# Add all panels
dashboard['panels'].extend([cpu_panel, memory_panel, storage_panel])

# Write back
with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("✓ Created separate bar gauge panels:")
print("  - CPU (ID: 110, y=0, h=4)")
print("  - Memory (ID: 111, y=4, h=4)")
print("  - Storage (ID: 112, y=8, h=8)")
