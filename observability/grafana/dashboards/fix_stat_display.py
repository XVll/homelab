#!/usr/bin/env python3
"""
Fix stat panels to properly show lcd-gauge bars and correct values
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

print("=== Fixing stat panel displays ===\n")

for panel in dashboard['panels']:
    panel_id = panel.get('id')
    panel_title = panel.get('title', 'Untitled')

    # Panel 7 & 8: Current CPU and Memory - need lcd-gauge bars
    if panel_id in [7, 8]:
        print(f"Fixing {panel_title} to show lcd-gauge bar")

        # For stat panels, we need to use custom cell options
        panel['fieldConfig']['defaults']['custom'] = {
            "cellOptions": {
                "type": "color-text"
            }
        }

        # Actually, let's use the table column approach
        # Add overrides for proper display
        panel['fieldConfig']['overrides'] = [{
            "matcher": {"id": "byName", "options": "Value"},
            "properties": [
                {"id": "custom.displayMode", "value": "lcd-gauge"},
                {"id": "custom.cellOptions", "value": {"type": "gauge"}},
                {"id": "unit", "value": "percentunit"},
                {"id": "min", "value": 0},
                {"id": "max", "value": 1}
            ]
        }]

        # Keep stat options simple
        panel['options'] = {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "orientation": "horizontal",
            "textMode": "value",
            "colorMode": "value",
            "graphMode": "none",
            "justifyMode": "center"
        }

        print(f"  ✓ Added lcd-gauge display mode")

    # Panel 23 & 24: CPU and Memory sparklines - fix units
    elif panel_id in [23, 24]:
        print(f"Fixing {panel_title} sparkline values")

        # Ensure proper unit
        if 'fieldConfig' not in panel:
            panel['fieldConfig'] = {"defaults": {}, "overrides": []}

        panel['fieldConfig']['defaults']['unit'] = 'percentunit'
        panel['fieldConfig']['defaults']['decimals'] = 1

        # Keep sparkline options
        panel['options'] = {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "orientation": "horizontal",
            "textMode": "value",
            "colorMode": "value",
            "graphMode": "area",
            "justifyMode": "center",
            "text": {
                "valueSize": 24
            }
        }

        print(f"  ✓ Set percentunit and sparkline")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Fixed stat panel displays!")
print("\nChanges:")
print("  - Current CPU/Memory: lcd-gauge display mode")
print("  - CPU/Memory sparklines: percentunit format")
print("  - Proper gauge rendering with bars")
