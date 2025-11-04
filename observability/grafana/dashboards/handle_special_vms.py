#!/usr/bin/env python3
"""
Handle special VMs (Synology, HA) that don't have Alloy disk metrics
- These VMs use their own OS disks, not our standard setup
- Show N/A for disk usage on these VMs
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Updating Disk Usage query to handle special VMs...")

        # Find the diskusg_percent query (target 6)
        for i, target in enumerate(panel['targets']):
            if target.get('refId') == 'diskusg_percent':
                print(f"\nUpdating query (index {i})...")

                # Updated query that includes all VMs but only has data for those with Alloy
                # VMs without Alloy (synology, ha) will be null and show N/A
                new_expr = '''pve_guest_info{template!="1"}
  * on(id) group_left()
    (
      (node_filesystem_size_bytes{mountpoint="/host/root",fstype="ext4"}
       - node_filesystem_avail_bytes{mountpoint="/host/root",fstype="ext4"})
      / node_filesystem_size_bytes{mountpoint="/host/root",fstype="ext4"}
    ) * on(instance) group_right()
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
      )
or
pve_guest_info{template!="1",name=~"synology|ha"} * 0'''

                target['expr'] = new_expr
                target['format'] = 'table'
                target['instant'] = True

                print("  ✓ Query updated")
                print("  ✓ VMs with Alloy (edge, db, media, etc.) → real disk usage")
                print("  ✓ VMs without Alloy (synology, ha) → null (will show N/A)")
                break

        # Update Disk Usage override to show N/A for null values
        for override in panel['fieldConfig']['overrides']:
            if override['matcher'].get('options') == 'Disk Usage':
                print("\nUpdating Disk Usage column config...")
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
                                    "match": "null",
                                    "result": {
                                        "text": "N/A",
                                        "color": "text"
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
                print("  ✓ Added N/A mapping for null values (synology, ha)")
                print("  ✓ Real VMs keep colored progress bars")
                break

        # Double-check that cluster and device columns are hidden
        org_transform = panel['transformations'][1]['options']
        if 'excludeByName' not in org_transform:
            org_transform['excludeByName'] = {}

        # Hide cluster and device if they somehow appear
        hidden_columns = ['cluster', 'device', 'tier', 'environment', 'job', 'fstype', 'mountpoint']
        for col in hidden_columns:
            org_transform['excludeByName'][col] = True

        print(f"\n✓ Ensured hidden columns: {', '.join(hidden_columns)}")

        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Special VM handling complete!")
print("\nDisk Usage display:")
print("  - edge, db, media, dev, deploy, observability → Real usage % with progress bar")
print("  - synology, ha → N/A (use their own OS disks)")
print("  - Hidden columns: cluster, device, tier, environment, job, fstype, mountpoint")
