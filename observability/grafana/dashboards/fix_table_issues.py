#!/usr/bin/env python3
"""
Fix table issues:
1. Add 🟢🔴 icons to status, use colored text, center, remove header
2. Show colored text values WITH progress bars for CPU/Memory/Disk usage
3. Fix missing Disk Usage column
4. Filter out template VMs (template=1)
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Fixing table issues...")

        # Issue 4: Filter out templates - add filter to all queries
        print("\n1. Filtering out template VMs...")
        for target in panel['targets']:
            if 'expr' in target:
                expr = target['expr']
                # Add template filter if not already present
                if 'template' not in expr:
                    # Add filter for non-templates at the end
                    if 'pve_guest_info' in expr:
                        # Replace pve_guest_info with pve_guest_info{template!="1"}
                        expr = expr.replace('pve_guest_info', 'pve_guest_info{template!="1"}')
                        target['expr'] = expr
                        print(f"   - Added template filter to query: {target['refId']}")

        # Issue 1: Status column with 🟢🔴 icons, colored text, centered
        print("\n2. Fixing Status column...")
        status_override = None
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'Status':
                status_override = override
                break

        if status_override:
            status_override['properties'] = [
                {
                    "id": "mappings",
                    "value": [
                        {
                            "options": {
                                "0": {
                                    "color": "red",
                                    "index": 1,
                                    "text": "🔴"
                                },
                                "1": {
                                    "color": "green",
                                    "index": 0,
                                    "text": "🟢"
                                }
                            },
                            "type": "value"
                        }
                    ]
                },
                {"id": "custom.displayMode", "value": "color-text"},
                {"id": "custom.width", "value": 50},
                {"id": "custom.align", "value": "center"}
            ]
            print("   ✓ Status: 🟢 green running, 🔴 red stopped, centered, colored text")

        # Issue 1b: Remove Status column header
        # Add this to the organize transformation
        org_transform = panel['transformations'][1]['options']
        if 'renameByName' not in org_transform:
            org_transform['renameByName'] = {}
        org_transform['renameByName']['Value #status'] = ''  # Empty string removes header
        print("   ✓ Status header removed")

        # Issue 2 & 3: Progress bars with colored text values
        print("\n3. Configuring progress bars with colored text...")

        # CPU Usage - lcd-gauge shows both bar and value
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'CPU Usage':
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "lcd-gauge"},  # Shows value + bar
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.7},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
                print("   ✓ CPU Usage: lcd-gauge with colored text + bar")
                break

        # Memory Usage - lcd-gauge
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'Memory Usage':
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "lcd-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.75},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
                print("   ✓ Memory Usage: lcd-gauge with colored text + bar")
                break

        # Disk Usage - lcd-gauge (Issue 3: Make sure it's visible)
        disk_usage_found = False
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'Disk Usage':
                disk_usage_found = True
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "lcd-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.7},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
                print("   ✓ Disk Usage: lcd-gauge with colored text + bar")
                break

        if not disk_usage_found:
            print("   ⚠ Disk Usage override not found, adding it...")
            panel['fieldConfig']['overrides'].append({
                "matcher": {"id": "byName", "options": "Disk Usage"},
                "properties": [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "lcd-gauge"},
                    {"id": "custom.width", "value": 150},
                    {"id": "decimals", "value": 1},
                    {"id": "min", "value": 0},
                    {"id": "max", "value": 1},
                    {"id": "color", "value": {"mode": "thresholds"}},
                    {"id": "thresholds", "value": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 0.7},
                            {"color": "red", "value": 0.9}
                        ]
                    }}
                ]
            })
            print("   ✓ Disk Usage: lcd-gauge added")

        # Make sure Disk Usage is not hidden
        if 'Disk Usage' not in org_transform.get('excludeByName', {}):
            print("   ✓ Disk Usage is visible in table")
        else:
            org_transform['excludeByName']['Disk Usage'] = False
            print("   ✓ Disk Usage unhidden")

        # Also ensure the rename is correct
        if 'Value #diskusg_percent' in org_transform['renameByName']:
            print("   ✓ Disk Usage column renamed correctly")

        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ All fixes applied!")
print("\nSummary:")
print("1. ✓ Status: 🟢/🔴 icons, colored text, centered, no header")
print("2. ✓ CPU/Memory/Disk: lcd-gauge with colored text + progress bar")
print("3. ✓ Disk Usage: visible and properly configured")
print("4. ✓ Template VMs: filtered out (template!='1')")
