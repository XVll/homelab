#!/usr/bin/env python3
"""
Change Current CPU and Memory gauges to circular style
Match the lcd-gauge appearance from table columns
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
        print(f"\n=== Converting '{panel_title}' to circular gauge ===")

        # Keep gauge type but change orientation
        panel['type'] = 'gauge'

        # Update options for circular/vertical orientation
        panel['options'] = {
            "orientation": "auto",  # Auto will make it circular in small panels
            "reduceOptions": {
                "calcs": ["lastNotNull"],
                "fields": "",
                "values": False
            },
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
            "text": {
                "valueSize": 32  # Larger text in center
            }
        }
        print("  ✓ Changed to circular/auto orientation")
        print("  ✓ Increased value size to 32")

        # Ensure fieldConfig has proper settings
        if 'fieldConfig' not in panel:
            panel['fieldConfig'] = {"defaults": {}, "overrides": []}

        defaults = panel['fieldConfig']['defaults']

        # Ensure proper display settings
        if 'decimals' not in defaults:
            defaults['decimals'] = 1  # One decimal place

        if 'unit' not in defaults:
            defaults['unit'] = 'percentunit'

        # Ensure min/max are set for proper gauge display
        defaults['min'] = 0
        defaults['max'] = 1

        print("  ✓ Set min/max for proper gauge range")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Converted to circular gauges!")
print("\nChanges:")
print("  - Orientation: horizontal → auto (circular/semi-circle)")
print("  - Larger value text in center")
print("  - Threshold colors remain (green/yellow/red)")
print("  - Min/max range: 0-100%")
print("\n📊 Result:")
print("  - Circular gauge showing percentage")
print("  - Color-coded by threshold")
print("  - Similar style to table progress bars")
print("  - More compact and modern appearance")
