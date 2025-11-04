#!/usr/bin/env python3
"""
Fix table layout issues:
1. Status column should show only colored circles (no text)
2. Hide ID and Type columns
3. Reorder columns properly
4. Fix column alignment
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Fixing table panel layout...")

        # Update transformation to properly order and hide columns
        org_transform = panel['transformations'][1]['options']

        # Hide ID and Type columns
        org_transform['excludeByName'] = {
            "Time 1": True,
            "Time 2": True,
            "Time 3": True,
            "Time 4": True,
            "Time 5": True,
            "Time 6": True,
            "Time 7": True,
            "Time 8": True,
            "Time 9": True,
            "Time 10": True,
            "Value #id, name and type": True,
            "id": True,
            "type": True
        }

        # Set column order: Status, Name, vCPUs, Memory, Disk, CPU Usage, Memory Usage, Disk Usage, Disk I/O, Network I/O
        org_transform['indexByName'] = {
            "Value #status": 0,
            "name": 1,
            "Value #vcpus": 2,
            "Value #memsize": 3,
            "Value #disksize": 4,
            "Value #cpu_usage": 5,
            "Value #memusg_percent": 6,
            "Value #diskusg_percent": 7,
            "Value #disk_io": 8,
            "Value #network_io": 9
        }

        # Rename columns properly
        org_transform['renameByName'] = {
            "Value #disksize": "Disk",
            "Value #diskusg_percent": "Disk Usage",
            "Value #memsize": "Memory",
            "Value #memusg_percent": "Memory Usage",
            "Value #status": "Status",
            "Value #vcpus": "vCPUs",
            "Value #cpu_usage": "CPU Usage",
            "Value #disk_io": "Disk I/O",
            "Value #network_io": "Network I/O",
            "name": "Name"
        }

        # Fix Status column override - use color-background-solid for circle effect
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'Status':
                print("  - Fixing Status column display mode...")
                for prop in override['properties']:
                    if prop['id'] == 'custom.displayMode':
                        prop['value'] = 'color-background-solid'
                    elif prop['id'] == 'custom.width':
                        prop['value'] = 50  # Even smaller for circle only
                    elif prop['id'] == 'mappings':
                        # Keep mappings but ensure no text is shown
                        for mapping in prop['value']:
                            if mapping['type'] == 'value':
                                for key in mapping['options']:
                                    mapping['options'][key]['text'] = ''  # Empty text

        # Update Name column width
        name_override_exists = False
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'Name':
                name_override_exists = True
                break

        if not name_override_exists:
            panel['fieldConfig']['overrides'].append({
                "matcher": {"id": "byName", "options": "Name"},
                "properties": [
                    {"id": "custom.width", "value": 150}
                ]
            })

        print("  ✓ Status column: color-background-solid with no text")
        print("  ✓ Hidden: ID, Type columns")
        print("  ✓ Column order: Status → Name → vCPUs → Memory → Disk → CPU Usage → Memory Usage → Disk Usage → Disk I/O → Network I/O")
        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Table layout fixes complete!")
