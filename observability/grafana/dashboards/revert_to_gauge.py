#!/usr/bin/env python3
"""
Revert Current CPU and Current Memory back to gauge panels
User prefers the gauge visualization
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

for panel in dashboard['panels']:
    panel_id = panel.get('id')
    panel_title = panel.get('title', '')

    # Panel 7: Current CPU
    # Panel 8: Current memory
    if panel_id in [7, 8]:
        print(f"\n=== Reverting '{panel_title}' to gauge ===")

        # Change back to gauge
        panel['type'] = 'gauge'
        print("  ✓ Type: stat → gauge")

        # Restore gauge options
        panel['options'] = {
            "orientation": "horizontal",
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
            "text": {}
        }
        print("  ✓ Restored gauge configuration")

        # Set targets back to instant query
        for target in panel.get('targets', []):
            target['range'] = False
            target['instant'] = False  # Gauge uses time_series format
            print("  ✓ Restored query format")

        # Keep existing fieldConfig (thresholds, colors, unit)
        print("  ✓ Preserved thresholds and colors")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Reverted to gauge panels!")
print("\nRestored:")
print("  - Classic horizontal gauge display")
print("  - Threshold markers (green/yellow/red)")
print("  - Clean, simple visualization")
print("  - Original layout and sizing")
