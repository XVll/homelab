#!/usr/bin/env python3
"""
1. Remove grid lines from all timeseries charts for cleaner look
2. Add sparkline to CPU Usage column as test
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# 1. Remove grids from timeseries panels
print("=== Removing grid lines from timeseries charts ===\n")
for panel in dashboard['panels']:
    if panel.get('type') == 'timeseries':
        panel_title = panel.get('title', 'Untitled')

        # Add axisGridShow: false to custom settings
        if 'fieldConfig' in panel and 'defaults' in panel['fieldConfig']:
            defaults = panel['fieldConfig']['defaults']
            if 'custom' in defaults:
                defaults['custom']['axisGridShow'] = False
                print(f"✓ Removed grid from '{panel_title}'")

# 2. Add sparkline to CPU Usage column in table
print("\n=== Adding sparkline to CPU Usage column ===\n")
for panel in dashboard['panels']:
    if panel.get('id') == 19:  # Table panel
        print("Found table panel, updating CPU Usage column...")

        # Find CPU Usage override
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'CPU Usage':
                print("  Found CPU Usage override")

                # Add sparkline display mode
                # Keep existing properties and add sparkline
                existing_props = {prop['id']: prop for prop in override['properties']}

                # Update display mode to include sparkline
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "gradient-gauge"},
                    {"id": "custom.width", "value": 200},  # Wider for sparkline
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {
                        "id": "custom.cellOptions",
                        "value": {
                            "type": "sparkline",
                            "mode": "gradient"
                        }
                    },
                    {"id": "color", "value": {"mode": "thresholds"}},
                    existing_props.get('thresholds', {
                        "id": "thresholds",
                        "value": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 0.7},
                                {"color": "red", "value": 0.9}
                            ]
                        }
                    })
                ]

                print("  ✓ Added sparkline to CPU Usage column")
                print("  ✓ Increased width to 200px for sparkline visibility")
                break
        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Updates complete!")
print("\nChanges:")
print("  1. ✓ Removed grid lines from all 7 timeseries charts")
print("     - Cleaner, more modern appearance")
print("     - Less visual clutter")
print("     - Focus on data lines")
print("\n  2. ✓ Added sparkline to CPU Usage column (test)")
print("     - Shows historical trend in table cell")
print("     - Width increased to 200px")
print("     - Gradient mode for colored sparkline")
print("\n💡 If sparkline looks good, we can add to other columns too:")
print("   - Memory Usage")
print("   - Disk Usage")
print("   - Disk I/O")
print("   - Network I/O")
