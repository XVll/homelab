#!/usr/bin/env python3
"""
Configure stat panels to show bar-style gauge + sparkline
"""
import json

# Read the dashboard
with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Update CPU panel (ID 110) - stat with bar-style + sparkline
for panel in dashboard['panels']:
    if panel['id'] == 110:  # CPU
        panel['type'] = 'stat'
        panel['fieldConfig']['defaults']['custom'] = {
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
        }
        panel['options'] = {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "orientation": "horizontal",
            "textMode": "value_and_name",
            "colorMode": "background",  # Color the background like a bar
            "graphMode": "area",  # Show sparkline
            "justifyMode": "center",
            "text": {
                "titleSize": 12,
                "valueSize": 28
            }
        }

    elif panel['id'] == 111:  # Memory
        panel['type'] = 'stat'
        panel['fieldConfig']['defaults']['custom'] = {
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
        }
        panel['options'] = {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "orientation": "horizontal",
            "textMode": "value_and_name",
            "colorMode": "background",  # Color the background like a bar
            "graphMode": "area",  # Show sparkline
            "justifyMode": "center",
            "text": {
                "titleSize": 12,
                "valueSize": 28
            }
        }

# Write back
with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("✓ Updated CPU panel: bar-style background + sparkline")
print("✓ Updated Memory panel: bar-style background + sparkline")
print("✓ colorMode: background makes it look like a colored bar")
print("✓ graphMode: area shows the sparkline history")
