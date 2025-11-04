#!/usr/bin/env python3
"""
Revert sparkline from CPU Usage column
Sparklines don't work with instant queries in tables
Keep the gradient-gauge (lcd-gauge) which works better for this use case
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Remove sparkline from CPU Usage column
for panel in dashboard['panels']:
    if panel.get('id') == 19:  # Table panel
        print("Reverting CPU Usage column to gradient progress bar...")

        # Find CPU Usage override
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'CPU Usage':
                print("  Found CPU Usage override")

                # Revert to lcd-gauge (works with instant queries)
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "lcd-gauge"},
                    {"id": "custom.width", "value": 150},  # Back to 150px
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {
                        "id": "thresholds",
                        "value": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 0.7},
                                {"color": "red", "value": 0.9}
                            ]
                        }
                    }
                ]

                print("  ✓ Reverted to lcd-gauge (colored text + progress bar)")
                print("  ✓ Width back to 150px")
                break
        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Sparkline reverted!")
print("\nWhy sparklines don't work here:")
print("  - Table queries use instant=true (single point in time)")
print("  - Sparklines need range queries (time series data)")
print("  - Would need separate range queries for each VM")
print("  - Would complicate the dashboard significantly")
print("\nCurrent solution (better for tables):")
print("  - lcd-gauge shows current value + colored progress bar")
print("  - Color-coded (green/yellow/red) based on thresholds")
print("  - Clean, modern appearance")
print("  - Works perfectly with instant queries")
print("\n💡 Sparklines work better in:")
print("  - Stat panels (single metric)")
print("  - Separate visualization panels")
print("  - Not ideal for multi-row tables with instant queries")
