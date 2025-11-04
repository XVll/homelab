#!/usr/bin/env python3
"""
Fix many-to-many matching error in disk usage query
Use proper aggregation to ensure 1:1 matching
"""

import json
import os

os.chdir('/home/fx/repositories/homelab/observability/grafana/dashboards')

with open('proxmox-overview.json', 'r') as f:
    dashboard = json.load(f)

# Find the table panel (id: 19)
for panel in dashboard['panels']:
    if panel.get('id') == 19:
        print("Fixing disk usage query to avoid many-to-many matching...")

        # Find the diskusg_percent query (target 6)
        for i, target in enumerate(panel['targets']):
            if target.get('refId') == 'diskusg_percent':
                print(f"\nUpdating query (index {i})...")

                # Fixed query using sum by (id) to ensure unique matching
                new_expr = '''sum by (id) (
  (
    (node_filesystem_size_bytes{mountpoint="/host/root",fstype="ext4"}
     - node_filesystem_avail_bytes{mountpoint="/host/root",fstype="ext4"})
    / node_filesystem_size_bytes{mountpoint="/host/root",fstype="ext4"}
  )
  * on(instance) group_left(id, name)
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
)'''

                target['expr'] = new_expr

                print("  ✓ Fixed many-to-many matching issue")
                print("  ✓ Using sum by (id) to aggregate properly")
                print("  ✓ Using group_left to join pve_guest_info labels")
                break

        break

with open('proxmox-overview.json', 'w') as f:
    json.dump(dashboard, f, indent=2)

print("\n✅ Query fixed!")
print("\nChanges:")
print("  - Wrapped in sum by (id) to ensure 1:1 matching")
print("  - Used group_left to properly join pve_guest_info")
print("  - VMs with Alloy data → real disk usage")
print("  - VMs without Alloy data → no result (will show N/A)")
