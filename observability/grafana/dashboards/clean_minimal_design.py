#!/usr/bin/env python3
"""
Fix the dashboard for clean, minimal design:
1. Clean up guest chart legends (show only series names, compact)
2. Replace circular gauges with lcd-gauge style stat panels
3. Replace history charts with sparkline stat panels (compact)
4. Remove confusing Space allocation panel
5. Keep only Storage usage on right
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

print("=== Cleaning up dashboard design ===\n")

for panel in dashboard['panels']:
    panel_id = panel.get('id')
    panel_title = panel.get('title', 'Untitled')

    # === Fix guest charts - cleaner legends ===
    if panel_id in [2, 5, 12, 13]:  # Guest CPU, Memory, Disk I/O, Network I/O
        print(f"Cleaning up: {panel_title}")

        # Simplify legend
        panel['options']['legend'] = {
            "calcs": [],  # Remove calculations clutter
            "displayMode": "list",
            "placement": "bottom",
            "showLegend": True
        }

        # Hide legend if too many series
        if panel_id in [12, 13]:  # IO panels can be busy
            panel['options']['legend']['showLegend'] = False

        print(f"  ✓ Simplified legend (no calcs)")

    # === Panel 7 & 8: Replace circular gauges with stat panels (lcd-gauge style) ===
    elif panel_id in [7, 8]:
        print(f"\nConverting {panel_title} to stat panel with lcd-gauge style")

        panel['type'] = 'stat'
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
            "justifyMode": "center",
            "text": {
                "valueSize": 28
            }
        }

        # Add lcd-gauge style display in fieldConfig
        if 'fieldConfig' not in panel:
            panel['fieldConfig'] = {"defaults": {}, "overrides": []}

        panel['fieldConfig']['defaults']['custom'] = {
            "displayMode": "lcd-gauge"
        }

        # Compact size
        if panel_id == 7:
            panel['gridPos'] = {"h": 3, "w": 6, "x": 18, "y": 0}
        else:
            panel['gridPos'] = {"h": 3, "w": 6, "x": 18, "y": 3}

        print(f"  ✓ Converted to stat with lcd-gauge style (3h x 6w)")

    # === Panel 23 & 24: Replace history charts with sparkline stats ===
    elif panel_id in [23, 24]:
        print(f"\nConverting {panel_title} to sparkline stat")

        panel['type'] = 'stat'
        panel['options'] = {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "orientation": "horizontal",
            "textMode": "value",
            "colorMode": "value",
            "graphMode": "area",  # Sparkline
            "justifyMode": "center",
            "text": {
                "valueSize": 20
            }
        }

        # Ensure range query for sparkline
        for target in panel.get('targets', []):
            target['range'] = True
            target['instant'] = False

        # Very compact
        if panel_id == 23:
            panel['gridPos'] = {"h": 2, "w": 6, "x": 18, "y": 6}
            panel['title'] = "CPU"
        else:
            panel['gridPos'] = {"h": 2, "w": 6, "x": 18, "y": 8}
            panel['title'] = "Memory"

        print(f"  ✓ Converted to sparkline stat (2h x 6w)")

    # === Panel 15: Remove Space allocation (confusing) ===
    elif panel_id == 15:
        print(f"\nHiding {panel_title} (confusing/redundant)")
        panel['gridPos'] = {"h": 0, "w": 0, "x": 0, "y": 0}
        panel['title'] = "HIDDEN - " + panel_title

    # === Panel 11: Keep Storage usage, reposition ===
    elif panel_id == 11:
        print(f"\nRepositioning {panel_title}")
        panel['gridPos'] = {"h": 11, "w": 6, "x": 18, "y": 10}
        print(f"  ✓ Storage usage (11h x 6w)")

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Dashboard cleaned up!")
print("\n📊 RIGHT COLUMN (Clean & Minimal):")
print("  1. CPU (stat with lcd-gauge) - 3h")
print("  2. Memory (stat with lcd-gauge) - 3h")
print("  3. CPU sparkline - 2h")
print("  4. Memory sparkline - 2h")
print("  5. Storage usage - 11h")
print("  Total: 21h (much cleaner!)")
print("\n📊 LEFT COLUMN (Guest Charts):")
print("  - Simplified legends (no calculation clutter)")
print("  - IO panels have no legend (cleaner)")
print("\n✨ Result:")
print("  - More charts, less text")
print("  - Clean, minimal design")
print("  - lcd-gauge style like table")
print("  - Sparklines instead of full charts")
print("  - Removed confusing panels")
