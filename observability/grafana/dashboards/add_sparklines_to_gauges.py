#!/usr/bin/env python3
"""
Convert Current CPU and Current Memory gauge panels to stat panels with sparklines
Sparklines work here because these panels use range queries
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

updated_panels = []

for panel in dashboard['panels']:
    panel_id = panel.get('id')
    panel_title = panel.get('title', '')

    # Panel 7: Current CPU gauge
    # Panel 8: Current memory gauge
    if panel_id in [7, 8]:
        print(f"\n=== Converting '{panel_title}' (ID: {panel_id}) ===")

        # Change from gauge to stat panel
        old_type = panel.get('type')
        panel['type'] = 'stat'
        print(f"  Type: {old_type} → stat")

        # Update options for stat with sparkline
        panel['options'] = {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "orientation": "auto",
            "textMode": "value_and_name",
            "colorMode": "value",
            "graphMode": "area",  # This enables sparkline
            "justifyMode": "auto",
            "showPercentChange": False
        }
        print("  ✓ Added sparkline (graphMode: area)")

        # Ensure targets are range queries (they should be already)
        for target in panel.get('targets', []):
            if 'range' not in target or not target.get('range'):
                target['range'] = True
                target['instant'] = False
                print("  ✓ Enabled range query for sparkline data")

        # Keep existing fieldConfig (thresholds, colors, etc.)
        print("  ✓ Preserved thresholds and color settings")

        updated_panels.append(panel_title)

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print(f"\n✅ Converted {len(updated_panels)} gauge panels to stat with sparklines!")
print("\nUpdated panels:")
for title in updated_panels:
    print(f"  - {title}")

print("\n📊 Sparkline configuration:")
print("  - Type: stat panel")
print("  - Graph mode: area (sparkline)")
print("  - Shows: current value + historical trend")
print("  - Color-coded by thresholds")
print("  - Compact design fits in same space")

print("\n✨ Benefits:")
print("  - See CPU/Memory trends at a glance")
print("  - Identify spikes or patterns quickly")
print("  - More informative than gauge alone")
print("  - Clean, modern dashboard look")
