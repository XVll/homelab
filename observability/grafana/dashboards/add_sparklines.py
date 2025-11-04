#!/usr/bin/env python3
"""
Add sparklines to CPU and Memory panels
"""
import json

# Read the dashboard
with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find and update CPU panel (ID 110) - change to stat with sparkline
for panel in dashboard['panels']:
    if panel['id'] == 110:  # CPU
        panel['type'] = 'stat'
        panel['options'] = {
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
                "titleSize": 14,
                "valueSize": 24
            }
        }
        # Change to range query for sparkline
        panel['targets'][0]['range'] = True
        panel['targets'][0]['instant'] = False

    elif panel['id'] == 111:  # Memory
        panel['type'] = 'stat'
        panel['options'] = {
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
                "titleSize": 14,
                "valueSize": 24
            }
        }
        # Change to range query for sparkline
        panel['targets'][0]['range'] = True
        panel['targets'][0]['instant'] = False

# Write back
with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("✓ Updated CPU panel with sparkline (stat panel)")
print("✓ Updated Memory panel with sparkline (stat panel)")
print("✓ Storage panel remains as bar gauge")
