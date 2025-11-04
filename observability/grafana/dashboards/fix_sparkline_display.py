#!/usr/bin/env python3
"""
Fix sparkline display issues:
1. Hide metric labels (cluster, environment, etc.)
2. Make sparkline more prominent
3. Improve text sizing
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
        print(f"\n=== Fixing '{panel_title}' display ===")

        # Update options for better sparkline display
        panel['options'] = {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "orientation": "auto",
            "textMode": "value",  # Only show value, not name
            "colorMode": "background",  # Color the background
            "graphMode": "area",  # Sparkline
            "justifyMode": "center",
            "showPercentChange": False,
            "text": {
                "valueSize": 60  # Bigger value text
            }
        }
        print("  ✓ Set textMode to 'value' (hides labels)")
        print("  ✓ Set colorMode to 'background' (colored panel)")
        print("  ✓ Increased value size to 60")
        print("  ✓ Center justified")

        # Update field config to hide labels
        if 'fieldConfig' not in panel:
            panel['fieldConfig'] = {"defaults": {}, "overrides": []}

        defaults = panel['fieldConfig']['defaults']

        # Add display name override to hide it
        defaults['displayName'] = ''

        # Keep existing thresholds and unit
        if 'thresholds' not in defaults:
            defaults['thresholds'] = {
                "mode": "absolute",
                "steps": [
                    {"color": "#299c46", "value": None},
                    {"color": "rgba(237, 129, 40, 0.89)", "value": 0.6 if panel_id == 8 else 0.7},
                    {"color": "#d44a3a", "value": 0.8 if panel_id == 8 else 0.9}
                ]
            }

        if 'unit' not in defaults:
            defaults['unit'] = 'percentunit'

        if 'decimals' not in defaults:
            defaults['decimals'] = 0  # No decimals for cleaner look

        print("  ✓ Hidden metric labels")
        print("  ✓ Set to 0 decimals for cleaner look")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Sparkline display fixed!")
print("\nChanges:")
print("  - Removed metric label text (cluster, environment, etc.)")
print("  - Value-only display (no field names)")
print("  - Larger value size (60)")
print("  - Background color mode (whole panel colored)")
print("  - Centered layout")
print("  - 0 decimals (80% instead of 80.0%)")
print("\n📊 Result:")
print("  - Big colored percentage value")
print("  - Clean sparkline underneath")
print("  - No clutter from labels")
print("  - Professional appearance")
