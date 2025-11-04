#!/usr/bin/env python3
"""
Consolidate right-side panels into single Host Information panel
"""
import json

# Read the dashboard
with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# IDs of panels to remove
panels_to_remove = [7, 8, 11, 23, 24]

# Remove the panels
dashboard['panels'] = [p for p in dashboard['panels'] if p['id'] not in panels_to_remove]

# Create new consolidated panel
host_info_panel = {
    "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
    },
    "description": "Proxmox host resource usage",
    "fieldConfig": {
        "defaults": {
            "color": {
                "mode": "thresholds"
            },
            "custom": {
                "axisCenteredZero": False,
                "axisColorMode": "text",
                "axisLabel": "",
                "axisPlacement": "auto",
                "barAlignment": 0,
                "drawStyle": "line",
                "fillOpacity": 30,
                "gradientMode": "hue",
                "hideFrom": {
                    "legend": False,
                    "tooltip": False,
                    "viz": False
                },
                "lineInterpolation": "linear",
                "lineWidth": 2,
                "pointSize": 5,
                "scaleDistribution": {
                    "type": "linear"
                },
                "showPoints": "auto",
                "spanNulls": False,
                "stacking": {
                    "group": "A",
                    "mode": "none"
                },
                "thresholdsStyle": {
                    "mode": "area"
                },
                "axisGridShow": False
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
        "h": 21,
        "w": 6,
        "x": 18,
        "y": 0
    },
    "id": 100,  # New unique ID
    "options": {
        "reduceOptions": {
            "values": False,
            "calcs": [
                "lastNotNull"
            ],
            "fields": ""
        },
        "orientation": "horizontal",
        "textMode": "value_and_name",
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "text": {
            "titleSize": 16,
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
            "instant": False,
            "legendFormat": "CPU",
            "refId": "CPU"
        },
        {
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "expr": "pve_memory_usage_bytes{instance=\"$instance\"} / pve_memory_size_bytes and on(id) pve_node_info",
            "range": True,
            "instant": False,
            "legendFormat": "Memory",
            "refId": "Memory"
        },
        {
            "datasource": {
                "type": "prometheus",
                "uid": "prometheus"
            },
            "expr": "pve_disk_usage_bytes{instance=\"$instance\", id=~\"storage/.+\"} / pve_disk_size_bytes * on (id, instance) group_left(storage) pve_storage_info",
            "range": True,
            "instant": False,
            "legendFormat": "{{storage}}",
            "refId": "Storage"
        }
    ],
    "title": "Host Resources",
    "type": "stat"
}

# Add the new panel
dashboard['panels'].append(host_info_panel)

# Write back
with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("✓ Consolidated panels into 'Host Resources' panel")
print("✓ Removed panels:", panels_to_remove)
print("✓ New panel ID:", 100)
