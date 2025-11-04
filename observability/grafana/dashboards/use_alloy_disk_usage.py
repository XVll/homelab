#!/usr/bin/env python3
"""
Update Disk Usage query to use Alloy node_exporter metrics instead of Proxmox
- Alloy provides real disk usage from inside each VM
- Map instance names: edge-vm → edge, db-vm → db, etc.
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Replacing Disk Usage query with Alloy metrics...")

        # Find the diskusg_percent query (target 6)
        for i, target in enumerate(panel['targets']):
            if target.get('refId') == 'diskusg_percent':
                print(f"\nOld query (index {i}):")
                print(f"  {target['expr']}")

                # New query using Alloy node_exporter metrics
                # This calculates: (size - avail) / size = usage %
                # Then maps instance names to match Proxmox names
                new_expr = '''(
  (node_filesystem_size_bytes{mountpoint="/host/root",fstype="ext4"}
   - node_filesystem_avail_bytes{mountpoint="/host/root",fstype="ext4"})
  / node_filesystem_size_bytes{mountpoint="/host/root",fstype="ext4"}
) * on(instance) group_left(id)
  label_replace(
    label_replace(
      label_replace(
        label_replace(
          label_replace(
            label_replace(
              label_replace(
                pve_guest_info{template!="1"},
                "instance", "edge-vm", "name", "edge"
              ),
              "instance", "db-vm", "name", "db"
            ),
            "instance", "media-vm", "name", "media"
          ),
          "instance", "dev-vm", "name", "dev"
        ),
        "instance", "deploy-vm", "name", "deploy"
      ),
      "instance", "observability-vm", "name", "observability"
    ),
    "instance", "synology", "name", "synology"
  )'''

                target['expr'] = new_expr

                print(f"\nNew query:")
                print(f"  Using Alloy node_exporter filesystem metrics")
                print(f"  - Calculates: (size - avail) / size")
                print(f"  - Maps VM instance names to Proxmox names")
                print(f"  - Provides REAL disk usage from inside VMs!")
                break

        # Update Disk Usage override to remove N/A mapping
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'Disk Usage':
                print("\nUpdating Disk Usage column config...")
                # Remove N/A mapping, add normal thresholds
                override['properties'] = [
                    {"id": "unit", "value": "percentunit"},
                    {"id": "custom.displayMode", "value": "lcd-gauge"},
                    {"id": "custom.width", "value": 150},
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
                print("  ✓ Removed N/A mapping")
                print("  ✓ Thresholds: green <70%, yellow 70-90%, red >90%")
                break

        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Disk Usage now uses REAL data from Alloy!")
print("\nVM name mapping:")
print("  - edge-vm → edge")
print("  - db-vm → db")
print("  - media-vm → media")
print("  - dev-vm → dev")
print("  - deploy-vm → deploy")
print("  - observability-vm → observability")
print("\nDisk usage will show actual filesystem usage from inside each VM!")
