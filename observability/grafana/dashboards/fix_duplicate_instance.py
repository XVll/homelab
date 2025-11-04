#!/usr/bin/env python3
"""
Fix duplicate instance label issue in disk usage query
Problem: label_replace creates multiple series with same instance value
Solution: Match on VM name directly, create temp_instance label instead
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Fixing duplicate instance label in disk usage query...")

        # Find the diskusg_percent query (target 6)
        for i, target in enumerate(panel['targets']):
            if target.get('refId') == 'diskusg_percent':
                print(f"\nUpdating query (index {i})...")

                # New approach: Create temp_name label on filesystem metrics, join on name
                new_expr = '''sum by (id) (
  label_replace(
    label_replace(
      label_replace(
        label_replace(
          label_replace(
            label_replace(
              (
                (node_filesystem_size_bytes{mountpoint="/host/root",fstype="ext4"}
                 - node_filesystem_avail_bytes{mountpoint="/host/root",fstype="ext4"})
                / node_filesystem_size_bytes{mountpoint="/host/root",fstype="ext4"}
              ),
              "temp_name", "edge", "instance", "edge-vm"
            ),
            "temp_name", "db", "instance", "db-vm"
          ),
          "temp_name", "media", "instance", "media-vm"
        ),
        "temp_name", "dev", "instance", "dev-vm"
      ),
      "temp_name", "deploy", "instance", "deploy-vm"
    ),
    "temp_name", "observability", "instance", "observability-vm"
  )
  * on(temp_name) group_left(id)
    label_replace(pve_guest_info{template!="1"}, "temp_name", "$1", "name", "(.*)")
)'''

                target['expr'] = new_expr

                print("  ✓ Fixed duplicate instance issue")
                print("  ✓ Using temp_name label for matching instead of instance")
                print("  ✓ Joins on VM name (unique per VM)")
                print("  ✓ Aggregates by id to get single value per VM")
                break

        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Query fixed!")
print("\nHow it works:")
print("  1. Add temp_name label to filesystem metrics (edge-vm → edge)")
print("  2. Add temp_name label to pve_guest_info (copies name)")
print("  3. Join on temp_name (unique per VM)")
print("  4. Aggregate by id to get final result")
print("\nResult:")
print("  - Standard VMs with Alloy → real disk usage %")
print("  - Synology/HA without Alloy → no result → N/A")
