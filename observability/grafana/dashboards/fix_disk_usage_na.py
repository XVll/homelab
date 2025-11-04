#!/usr/bin/env python3
"""
Fix Disk Usage to show "N/A" for QEMU VMs (which always report 0)
Since Proxmox doesn't provide disk usage for QEMU VMs without guest agent
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Configuring Disk Usage to show N/A for QEMU VMs...")

        # Find Disk Usage override
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'Disk Usage':
                print("\nFound Disk Usage override, updating...")

                # Add mapping for 0 values to show "N/A"
                # Keep existing properties and add special mapping
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "lcd-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {
                        "id": "mappings",
                        "value": [
                            {
                                "options": {
                                    "match": "null+zero",
                                    "result": {
                                        "text": "N/A",
                                        "color": "semi-dark-gray"
                                    }
                                },
                                "type": "special"
                            }
                        ]
                    },
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
                print("✓ Added 'N/A' mapping for null/zero values")
                print("✓ QEMU VMs will show 'N/A' (disk usage not available without guest agent)")
                print("✓ LXC containers will show actual usage % if any exist")
                break
        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Disk Usage column configured!")
print("\nNote: Proxmox cannot report disk usage for QEMU VMs without QEMU guest agent.")
print("QEMU VMs will show 'N/A' instead of misleading 0.0%")
